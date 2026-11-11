"""Escolhe o modelo de linguagem do agente.

  "qwen"        Qwen2.5-1.5B-Instruct local (modelo dos laboratórios; sem chave)
  "openrouter"  modelo remoto por API compatível com OpenAI (precisa dos Secrets
                LLM_API_KEY, LLM_BASE_URL e LLM_MODEL)

Os dois devolvem o mesmo resultado em `run()`, então podem ser comparados nos
mesmos pedidos de teste.
"""
from __future__ import annotations

from .prompts import ACTIVE_VERSION

BACKENDS = ("qwen", "openrouter")


def criar_agente(tools, backend: str = "qwen", prompt_version: str = ACTIVE_VERSION,
                 model: str | None = None):
    if backend == "qwen":
        from .agent_qwen import QwenAgent
        return QwenAgent(tools, model=model, prompt_version=prompt_version)
    if backend == "openrouter":
        from .agent import FlightAgent
        return FlightAgent(tools, model=model, prompt_version=prompt_version)
    raise ValueError(f"backend deve ser um de {BACKENDS}, recebi {backend!r}")
