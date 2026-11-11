"""Ferramentas expostas ao LLM (Fase 3).

O LLM nunca calcula rota: ele chama `buscar_rota`, que delega ao A* (Fase 1)
usando o custo previsto pelo modelo (Fase 2). Esta camada só valida os
argumentos, monta o contexto e formata a saída.

A ligação com o seu projeto fica em `Backend` (veja backend_projeto.py).
"""
from __future__ import annotations

from typing import Protocol

HORARIOS = ("Peak", "Off-peak")
CLIMAS = ("Clear", "Rain", "Snow", "Storm")
TIPOS_EVENTO = ("Storm", "Closure", "Delay")


class Backend(Protocol):
    """Contrato mínimo entre o agente e o seu código das Fases 1 e 2."""

    def aeroportos(self) -> dict[str, str]:
        """{codigo_iata: nome}"""

    def rota_mais_curta(self, origem: str, destino: str,
                        evitar: set[str], contexto: dict | None = None) -> dict | None:
        """A* com custo = distância. Retorna {"caminho": [...], "km": float}.
        O contexto é usado só para respeitar trechos fechados (Closure)."""

    def rota_mais_rapida(self, origem: str, destino: str, contexto: dict,
                        evitar: set[str]) -> dict | None:
        """A* com custo = tempo previsto pelo modelo.
        Retorna {"caminho": [...], "km": float, "min": float}."""

    def tempo_da_rota(self, caminho: list[str], contexto: dict) -> float:
        """Tempo previsto (min) de um caminho dado, sob o mesmo contexto."""


TOOL_SPECS = [
    {
        "name": "buscar_rota",
        "description": (
            "Calcula a rota aérea mais rápida (tempo previsto pelo modelo de custo) "
            "entre dois aeroportos e compara com a rota mais curta em km. "
            "Use sempre que o usuário pedir uma rota."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "origem": {"type": "string", "description": "Código IATA, ex.: CLT"},
                "destino": {"type": "string", "description": "Código IATA, ex.: LAX"},
                "evitar": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Códigos IATA de aeroportos a evitar.",
                },
                "eventos": {
                    "type": "array",
                    "description": "Problemas em um trecho específico.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "de": {"type": "string"},
                            "para": {"type": "string"},
                            "tipo": {"type": "string", "enum": list(TIPOS_EVENTO)},
                        },
                        "required": ["de", "para", "tipo"],
                    },
                },
                "horario": {"type": "string", "enum": list(HORARIOS)},
                "clima": {"type": "string", "enum": list(CLIMAS)},
                "vento": {"type": "number",
                          "description": "Nós, de -25 (proa) a 25 (cauda)."},
                "congestionamento": {"type": "integer", "minimum": 1, "maximum": 5},
            },
            "required": ["origem", "destino"],
        },
    },
    {
        "name": "listar_aeroportos",
        "description": "Lista os aeroportos da malha (código IATA e nome).",
        "parameters": {"type": "object", "properties": {}},
    },
]


def _erro(msg: str) -> dict:
    return {"ok": False, "erro": msg}


class FlightTools:
    def __init__(self, backend: Backend):
        self.backend = backend
        self._aeroportos = {k.upper(): v for k, v in backend.aeroportos().items()}

    # ---------- utilitários ----------
    def _codigo(self, valor, campo: str):
        if not isinstance(valor, str) or not valor.strip():
            return None, f"{campo} ausente."
        cod = valor.strip().upper()
        if cod not in self._aeroportos:
            return None, (f"Aeroporto '{valor}' não existe na malha "
                          f"(campo {campo}). Use listar_aeroportos.")
        return cod, None

    # ---------- ferramentas ----------
    def listar_aeroportos(self) -> dict:
        return {"ok": True, "aeroportos": self._aeroportos}

    def buscar_rota(self, origem: str, destino: str, evitar: list | None = None,
                    eventos: list | None = None, horario: str = "Off-peak",
                    clima: str = "Clear", vento: float = 0,
                    congestionamento: int = 1) -> dict:
        org, e = self._codigo(origem, "origem")
        if e:
            return _erro(e)
        dst, e = self._codigo(destino, "destino")
        if e:
            return _erro(e)
        if org == dst:
            return _erro("Origem e destino são o mesmo aeroporto.")

        bloqueados: set[str] = set()
        for item in evitar or []:
            cod, e = self._codigo(item, "evitar")
            if e:
                return _erro(e)
            bloqueados.add(cod)
        if org in bloqueados or dst in bloqueados:
            return _erro("Origem ou destino está na lista de aeroportos a evitar.")

        evs = []
        for ev in eventos or []:
            if not isinstance(ev, dict):
                return _erro("Evento inválido: esperado {de, para, tipo}.")
            a, e = self._codigo(ev.get("de"), "eventos.de")
            if e:
                return _erro(e)
            b, e = self._codigo(ev.get("para"), "eventos.para")
            if e:
                return _erro(e)
            if ev.get("tipo") not in TIPOS_EVENTO:
                return _erro(f"Tipo de evento inválido. Use um de {TIPOS_EVENTO}.")
            evs.append({"de": a, "para": b, "tipo": ev["tipo"]})

        if horario not in HORARIOS:
            return _erro(f"horario deve ser um de {HORARIOS}.")
        if clima not in CLIMAS:
            return _erro(f"clima deve ser um de {CLIMAS}.")
        if not isinstance(vento, (int, float)) or not -25 <= vento <= 25:
            return _erro("vento deve estar entre -25 e 25 nós.")
        if not isinstance(congestionamento, int) or not 1 <= congestionamento <= 5:
            return _erro("congestionamento deve ser inteiro de 1 a 5.")

        contexto = {"horario": horario, "clima": clima, "vento": vento,
                    "congestionamento": congestionamento, "eventos": evs}

        rapida = self.backend.rota_mais_rapida(org, dst, contexto, bloqueados)
        if rapida is None:
            return _erro("Não existe rota entre esses aeroportos com as restrições.")
        curta = self.backend.rota_mais_curta(org, dst, bloqueados, contexto)
        tempo_curta = (self.backend.tempo_da_rota(curta["caminho"], contexto)
                       if curta else None)

        return {
            "ok": True,
            "rota": rapida["caminho"],
            "tempo_previsto_min": round(rapida["min"], 1),
            "distancia_km": round(rapida["km"], 1),
            "rota_mais_curta": None if not curta else {
                "rota": curta["caminho"],
                "distancia_km": round(curta["km"], 1),
                "tempo_previsto_min": round(tempo_curta, 1),
            },
            "economia_min": (None if tempo_curta is None
                             else round(tempo_curta - rapida["min"], 1)),
            "contexto": contexto,
        }