"""Agente da Fase 3 com o modelo dos laboratórios do IESB (Labs 7, 8 e 9).

Modelo: Qwen/Qwen2.5-1.5B-Instruct, executado LOCALMENTE com a biblioteca
`transformers` (sem API, sem chave, sem limite de requisições).

O ciclo é o mesmo do Lab 9 (pensar -> agir -> observar):
  1. o modelo recebe o pedido e a lista de ferramentas (`tools=` no chat template);
  2. se quiser usar uma ferramenta, responde com  <tool_call>{"name": ..., "arguments": {...}}</tool_call>;
  3. o código executa a ferramenta e devolve o resultado com o papel "tool";
  4. o modelo escreve a resposta final em português.

`QwenAgent.run()` devolve o mesmo dicionário do `FlightAgent` (agent.py), então a
avaliação, o notebook e a interface gráfica funcionam com qualquer um dos dois.
"""
from __future__ import annotations

import json
import os
import re
import time

from .prompts import get_system_prompt, ACTIVE_VERSION
from .tools import FlightTools, TOOL_SPECS

MODELO_PADRAO = "Qwen/Qwen2.5-1.5B-Instruct"
MAX_TURNS = 4            # chamadas ao modelo por pedido (ferramenta -> resposta)
MAX_NEW_TOKENS = 400     # o Lab 9 usa 150; a resposta final com a rota precisa de mais

_CACHE: dict = {}        # o modelo (~3 GB) é carregado uma única vez por sessão
_RE_CHAMADA = re.compile(r"<tool_call>\s*(.*?)\s*(?:</tool_call>|$)", re.DOTALL)


def _config(nome: str) -> str | None:
    valor = os.environ.get(nome)
    if valor:
        return valor
    try:
        from google.colab import userdata
        return userdata.get(nome)
    except Exception:
        return None


def carregar_modelo(nome: str = MODELO_PADRAO):
    """Baixa (na primeira vez) e devolve (tokenizer, modelo, dispositivo)."""
    if nome in _CACHE:
        return _CACHE[nome]
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    token = os.environ.get("HF_TOKEN") or _config("HF_TOKEN")   # opcional
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if dispositivo == "cuda" else torch.float32
    tok = AutoTokenizer.from_pretrained(nome, token=token)
    try:
        modelo = AutoModelForCausalLM.from_pretrained(nome, dtype=dtype, token=token)
    except TypeError:        # versões antigas do transformers usam torch_dtype
        modelo = AutoModelForCausalLM.from_pretrained(nome, torch_dtype=dtype, token=token)
    modelo.to(dispositivo).eval()
    _CACHE[nome] = (tok, modelo, dispositivo)
    return _CACHE[nome]


def extrair_chamadas(texto: str):
    """Lê os blocos <tool_call> da saída do modelo.

    Devolve (texto_antes, chamadas); cada chamada é {"nome", "args"} ou
    {"invalida": trecho} quando o JSON do modelo está quebrado.
    """
    primeiro = texto.find("<tool_call>")
    antes = texto if primeiro < 0 else texto[:primeiro]
    chamadas = []
    for bloco in _RE_CHAMADA.findall(texto):
        obj = None
        try:
            obj = json.loads(bloco)
        except json.JSONDecodeError:
            ini, fim = bloco.find("{"), bloco.rfind("}")
            if 0 <= ini < fim:
                try:
                    obj = json.loads(bloco[ini:fim + 1])
                except json.JSONDecodeError:
                    obj = None
        if not isinstance(obj, dict) or not isinstance(obj.get("name"), str):
            chamadas.append({"invalida": bloco[:200]})
            continue
        args = obj.get("arguments", obj.get("parameters", {}))
        if isinstance(args, str):               # alguns modelos mandam o JSON como texto
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = None
        chamadas.append({"nome": obj["name"], "args": args if isinstance(args, dict) else {}})
    return antes.strip(), chamadas


def normalizar_args(args: dict) -> dict:
    """Corrige deslizes de tipo comuns em modelos pequenos, sem mudar o sentido.

    Ex.: evitar="ATL" -> ["ATL"]; vento="-10" -> -10; campos None são removidos.
    A ferramenta continua validando tudo (códigos, faixas e enums).
    """
    a = {k: v for k, v in args.items() if v is not None}
    if isinstance(a.get("evitar"), str):
        a["evitar"] = [p.strip() for p in re.split(r"[,\s]+", a["evitar"]) if p.strip()]
    if isinstance(a.get("eventos"), dict):
        a["eventos"] = [a["eventos"]]
    if isinstance(a.get("vento"), str):
        try:
            a["vento"] = float(a["vento"].replace(",", "."))
        except ValueError:
            pass
    if isinstance(a.get("congestionamento"), (str, float)):
        try:
            a["congestionamento"] = int(float(a["congestionamento"]))
        except (TypeError, ValueError):
            pass
    return a


class QwenAgent:
    """Qwen2.5-1.5B-Instruct local: interpreta o pedido, usa as ferramentas e explica."""

    def __init__(self, tools: FlightTools, model: str | None = None,
                 prompt_version: str = ACTIVE_VERSION):
        self.tools = tools
        self.model = model or MODELO_PADRAO
        self.system = get_system_prompt(prompt_version)
        self.tool_defs = [
            {"type": "function",
             "function": {"name": s["name"], "description": s["description"],
                          "parameters": s["parameters"]}}
            for s in TOOL_SPECS
        ]

    def _execute(self, name: str, args: dict) -> dict:
        fn = getattr(self.tools, name, None)
        if name not in {s["name"] for s in TOOL_SPECS} or fn is None:
            return {"ok": False, "erro": f"Ferramenta desconhecida: {name}"}
        try:
            return fn(**args)
        except TypeError as e:
            return {"ok": False, "erro": f"Argumentos inválidos: {e}"}
        except Exception as e:  # a ferramenta nunca derruba o agente
            return {"ok": False, "erro": f"Falha na ferramenta: {e}"}

    def _gerar(self, messages: list) -> tuple[str, int, int]:
        """Uma chamada ao modelo. Devolve (texto, tokens_de_entrada, tokens_gerados)."""
        import torch
        tok, modelo, dispositivo = carregar_modelo(self.model)
        entrada = tok.apply_chat_template(
            messages, tools=self.tool_defs, add_generation_prompt=True,
            return_tensors="pt", return_dict=True).to(dispositivo)
        n_in = entrada["input_ids"].shape[1]
        with torch.no_grad():
            saida = modelo.generate(**entrada, max_new_tokens=MAX_NEW_TOKENS,
                                    do_sample=False, pad_token_id=tok.eos_token_id)
        novos = saida[0][n_in:]
        return tok.decode(novos, skip_special_tokens=True), n_in, int(len(novos))

    def run(self, pedido: str) -> dict:
        messages = [{"role": "system", "content": self.system},
                    {"role": "user", "content": pedido}]
        chamadas, tokens_in, tokens_out = [], 0, 0
        resposta, erro = "", None
        inicio = time.time()

        try:
            for _ in range(MAX_TURNS):
                texto, n_in, n_out = self._gerar(messages)
                tokens_in += n_in
                tokens_out += n_out
                antes, pedidas = extrair_chamadas(texto)

                if not pedidas:
                    resposta = texto.strip()
                    break

                validas = [c for c in pedidas if "nome" in c]
                if not validas:      # JSON quebrado: uma chance de o modelo corrigir
                    chamadas.append({"nome": "(chamada inválida)", "entrada": {},
                                     "saida": {"ok": False, "erro": pedidas[0]["invalida"]}})
                    messages.append({"role": "assistant", "content": texto})
                    messages.append({"role": "user", "content":
                                     "Sua chamada de ferramenta não é um JSON válido. Envie de novo "
                                     'no formato <tool_call>{"name": ..., "arguments": {...}}</tool_call>.'})
                    continue

                preparadas = [(c["nome"], normalizar_args(c["args"])) for c in validas]
                messages.append({"role": "assistant", "content": antes,
                                 "tool_calls": [{"type": "function",
                                                 "function": {"name": n, "arguments": a}}
                                                for n, a in preparadas]})
                for nome, args in preparadas:
                    saida = self._execute(nome, args)
                    chamadas.append({"nome": nome, "entrada": args, "saida": saida})
                    messages.append({"role": "tool", "name": nome,
                                     "content": json.dumps(saida, ensure_ascii=False)})
            else:
                erro = f"Limite de {MAX_TURNS} turnos atingido sem resposta final."
        except Exception as e:   # falta de memória, download falhou etc.
            erro = f"Erro do modelo local: {type(e).__name__}: {e}"

        return {"pedido": pedido, "resposta": resposta, "chamadas": chamadas,
                "tokens_in": tokens_in, "tokens_out": tokens_out,
                "latencia_s": round(time.time() - inicio, 2), "erro": erro}
