import json
import os
import sys
import time

import pandas as pd

from src.agent.backend_projeto import ProjetoBackend
from src.agent.fabrica import BACKENDS, criar_agente
from src.agent.tools import FlightTools
from src.environment.dataset import generate_synthetic_flight_dataset
from src.environment.loader import load_network
from src.environment.model import train_and_evaluate

PAUSA_S = {"qwen": 0, "openrouter": 6}   # OpenRouter: pausa para não estourar o plano gratuito
FALHAS_SEGUIDAS_MAX = 3                   # para tudo se a API falhar este tanto de vezes seguidas


def caminho_resultado(prompt_version: str, backend: str) -> str:
    """Os resultados do OpenRouter mantêm o nome antigo (fase3_avaliacao_v1.csv)."""
    if backend == "openrouter":
        return f"results/fase3_avaliacao_{prompt_version}.csv"
    return f"results/fase3_avaliacao_{backend}_{prompt_version}.csv"


def rota_valida(network, rota, origem, destino) -> bool:
    if not rota or rota[0] != origem or rota[-1] != destino:
        return False
    return all(
        any(f.destination.code == b for f in network.get_outgoing_flights(a))
        for a, b in zip(rota, rota[1:])
    )


def args_ok(esperado: dict, real: dict) -> bool:
    for k, v in esperado.items():
        if k == "vento_negativo":
            if not (real.get("vento", 0) < 0):
                return False
        elif k == "evitar":
            if not set(v) <= {str(c).upper() for c in real.get("evitar", [])}:
                return False
        elif k == "eventos":
            pares = {(str(e.get("de", "")).upper(), str(e.get("para", "")).upper())
                     for e in real.get("eventos", [])}
            if not {(e["de"], e["para"]) for e in v} <= pares:
                return False
        elif str(real.get(k, "")).upper() != str(v).upper():
            return False
    return True


def avaliar(caminho="data/pedidos_teste.json", model=None, prompt_version="v1",
            backend="qwen"):
    network = load_network("data/maps/mapa_medio.json", "data/maps/airports.json")
    pipeline, _, _ = train_and_evaluate(generate_synthetic_flight_dataset(network))
    projeto = ProjetoBackend(network, pipeline, aircraft_type="Narrow-body")
    tools = FlightTools(projeto)
    agent = criar_agente(tools, backend=backend, prompt_version=prompt_version, model=model)

    with open(caminho, encoding="utf-8") as f:
        pedidos = json.load(f)

    linhas = []
    seguidas = 0
    for p in pedidos:
        r = agent.run(p["pedido"])
        time.sleep(PAUSA_S.get(backend, 0))
        esp = p["espera"]
        buscas = [c for c in r["chamadas"] if c["nome"] == "buscar_rota"]
        usou = bool(buscas)

        ferramenta_ok = usou == esp["usa_ferramenta"]
        argumentos_ok = True
        valida = None
        fiel = None
        ok_esperado = True
        if usou:
            ultima = buscas[-1]
            argumentos_ok = args_ok(esp.get("entrada", {}), ultima["entrada"])
            saida = ultima["saida"]
            if "ok" in esp:
                ok_esperado = saida.get("ok") == esp["ok"]
            if saida.get("ok"):
                valida = rota_valida(network, saida["rota"],
                                     str(ultima["entrada"].get("origem", "")).upper(),
                                     str(ultima["entrada"].get("destino", "")).upper())
                fiel = all(c in r["resposta"] for c in saida["rota"])  # texto cita a rota real

        acerto = (ferramenta_ok and argumentos_ok and ok_esperado
                  and valida in (True, None) and fiel in (True, None)
                  and r["erro"] is None)
        linhas.append({"id": p["id"], "acerto": acerto, "ferramenta_ok": ferramenta_ok,
                       "argumentos_ok": argumentos_ok, "rota_valida": valida,
                       "resposta_fiel": fiel, "tokens_in": r["tokens_in"],
                       "tokens_out": r["tokens_out"], "latencia_s": r["latencia_s"],
                       "erro": r["erro"], "pedido": p["pedido"], "resposta": r["resposta"]})
        print(f"[{p['id']:>2}] {'OK ' if acerto else 'FALHA'} | {p['pedido'][:60]}")

        seguidas = seguidas + 1 if (r["erro"] or "").startswith("Erro da API") else 0
        if seguidas >= FALHAS_SEGUIDAS_MAX:
            print(f"\nA API falhou {seguidas} vezes seguidas (provável limite de cota). "
                  "Avaliação interrompida e NADA foi salvo.")
            return None

    df = pd.DataFrame(linhas)
    os.makedirs("results", exist_ok=True)
    destino = caminho_resultado(prompt_version, backend)
    df.to_csv(destino, index=False)
    print(f"\nModelo: {backend} | Prompt: {prompt_version} | salvo em {destino}")
    print(f"Acertos: {int(df['acerto'].sum())}/{len(df)}")
    print(f"Tokens: {df['tokens_in'].sum()} entrada / {df['tokens_out'].sum()} saída")
    print(f"Latência média: {df['latencia_s'].mean():.1f}s")
    return df


if __name__ == "__main__":
    # uso: python -m src.agent.avaliar [v1|v2|v3|v4] [qwen|openrouter]
    versao = sys.argv[1] if len(sys.argv) > 1 else "v1"
    modelo_llm = sys.argv[2] if len(sys.argv) > 2 else "qwen"
    if modelo_llm not in BACKENDS:
        sys.exit(f"Segundo argumento deve ser um de {BACKENDS}.")
    avaliar(prompt_version=versao, backend=modelo_llm)