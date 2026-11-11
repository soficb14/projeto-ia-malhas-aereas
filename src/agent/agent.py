import json
import os
import time
import sys

import openai

from .prompts import get_system_prompt, ACTIVE_VERSION
from .tools import FlightTools, TOOL_SPECS

# Configuração por variáveis de ambiente (nada de chave no código):
#   LLM_API_KEY   chave do provedor
#   LLM_BASE_URL  ex.: https://openrouter.ai/api/v1
#   LLM_MODEL     ex.: o ID do modelo Qwen escolhido no provedor
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "")
MAX_TURNS = 5
MAX_RETRIES = 3


def _config(nome: str) -> str | None:
    valor = os.environ.get(nome)
    if valor:
        return valor
    try:
        from google.colab import userdata
        return userdata.get(nome)
    except Exception:
        return None


class FlightAgent:
    """LLM que interpreta o pedido, aciona as ferramentas e explica o resultado."""

    def __init__(self, tools: FlightTools, model: str | None = None,
                 prompt_version: str = ACTIVE_VERSION, client=None):
        self.tools = tools
        self.model = model or DEFAULT_MODEL or _config("LLM_MODEL")
        if not self.model:
            raise RuntimeError("Defina LLM_MODEL (ID do modelo no provedor).")
        self.system = get_system_prompt(prompt_version)
        if client is None:
            chave = _config("LLM_API_KEY")
            base = _config("LLM_BASE_URL")
            if not chave or not base:
                raise RuntimeError("Defina LLM_API_KEY e LLM_BASE_URL "
                                   "(variável de ambiente ou segredo do Colab).")
            client = openai.OpenAI(api_key=chave, base_url=base)
        self.client = client
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

    def _chamar(self, messages):
        for tentativa in range(MAX_RETRIES):
            try:
                return self.client.chat.completions.create(
                    model=self.model, max_tokens=2048,
                    messages=messages, tools=self.tool_defs)
            except openai.RateLimitError:
                if tentativa == MAX_RETRIES - 1:
                    raise
                time.sleep(2 ** (tentativa + 1))

    def run(self, pedido: str) -> dict:
        messages = [{"role": "system", "content": self.system},
                    {"role": "user", "content": pedido}]
        chamadas, tokens_in, tokens_out = [], 0, 0
        resposta, erro = "", None
        inicio = time.time()

        try:
            for _ in range(MAX_TURNS):
                resp = self._chamar(messages)
                if resp.usage:
                    tokens_in += resp.usage.prompt_tokens or 0
                    tokens_out += resp.usage.completion_tokens or 0

                msg = resp.choices[0].message
                if not msg.tool_calls:
                    resposta = msg.content or ""
                    break

                messages.append({
                    "role": "assistant", "content": msg.content or "",
                    "tool_calls": [
                        {"id": c.id, "type": "function",
                         "function": {"name": c.function.name,
                                      "arguments": c.function.arguments}}
                        for c in msg.tool_calls]})

                for c in msg.tool_calls:
                    try:
                        args = json.loads(c.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args, saida = {}, {"ok": False,
                                           "erro": "Argumentos não são JSON válido."}
                    else:
                        saida = self._execute(c.function.name, args)
                    chamadas.append({"nome": c.function.name, "entrada": args,
                                     "saida": saida})
                    messages.append({"role": "tool", "tool_call_id": c.id,
                                     "content": json.dumps(saida, ensure_ascii=False)})
            else:
                erro = f"Limite de {MAX_TURNS} turnos atingido sem resposta final."
        except openai.APIError as e:
            erro = f"Erro da API: {e}"

        return {"pedido": pedido, "resposta": resposta, "chamadas": chamadas,
                "tokens_in": tokens_in, "tokens_out": tokens_out,
                "latencia_s": round(time.time() - inicio, 2), "erro": erro}