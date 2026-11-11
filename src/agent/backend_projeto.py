"""Adaptador entre o agente (Fase 3) e as Fases 1 e 2."""
from __future__ import annotations

import json

from ..environment.graph import AirNetwork
from ..search.astar import a_star_search
from ..environment.model import build_cost_map
from ..search.heuristics import MAX_SPEED_KMH

CONTEXTO_VAZIO = {"horario": "Off-peak", "clima": "Clear", "vento": 0,
                  "congestionamento": 1, "eventos": []}


class ProjetoBackend:
    def __init__(self, rede: AirNetwork, pipeline, aircraft_type: str,
             max_speed_km_h: float = MAX_SPEED_KMH):
        """aircraft_type: o modelo exige essa feature, mas o usuário não a informa.
        Use o tipo mais comum do dataset e documente a premissa no relatório."""
        self.rede = rede
        self.pipeline = pipeline
        self.aircraft_type = aircraft_type
        self.max_speed = max_speed_km_h
        self._cache: dict[str, tuple[dict, set]] = {}

    # ---------- contrato usado por FlightTools ----------
    def aeroportos(self) -> dict[str, str]:
        return {code: getattr(a, "name", None) or getattr(a, "city", None) or code
                for code, a in self.rede.airports.items()}

    def rota_mais_curta(self, origem, destino, evitar, contexto=None):
        # Respeita trechos fechados do contexto: é uma rota que dá para voar.
        _, fechados = self._custos(contexto or CONTEXTO_VAZIO)
        net = self._subrede(evitar, fechados)
        res = a_star_search(net, origem, destino, "distance")
        if res is None:
            return None
        return {"caminho": [a.code for a in res.path], "km": res.cost,
                "nos_expandidos": res.expanded_nodes}

    def rota_mais_rapida(self, origem, destino, contexto, evitar):
        custos, fechados = self._custos(contexto)
        net = self._subrede(evitar, fechados)
        net.set_learned_costs(custos)
        res = a_star_search(net, origem, destino, "predicted_time")
        if res is None:
            return None
        caminho = [a.code for a in res.path]
        return {"caminho": caminho, "km": self._km(net, caminho), "min": res.cost,
                "nos_expandidos": res.expanded_nodes}

    def tempo_da_rota(self, caminho, contexto):
        custos, _ = self._custos(contexto)
        return sum(custos[(u, v)] for u, v in zip(caminho, caminho[1:]))

    # ---------- internos ----------
    def _custos(self, contexto: dict):
        chave = json.dumps(contexto, sort_keys=True)
        if chave in self._cache:
            return self._cache[chave]

        modelo_ctx = {
            "aircraft_type": self.aircraft_type,
            "route_congestion_index": contexto["congestionamento"],
            "weather_condition": contexto["clima"],
            "wind_component": contexto["vento"],
            "time_of_day": contexto["horario"],
        }

        overrides: dict[tuple[str, str], dict] = {}
        fechados: set[tuple[str, str]] = set()
        for ev in contexto.get("eventos", []):
            for par in ((ev["de"], ev["para"]), (ev["para"], ev["de"])):  # nos dois sentidos
                if ev["tipo"] == "Closure":
                    fechados.add(par)
                elif ev["tipo"] == "Storm":
                    overrides.setdefault(par, {})["weather_condition"] = "Storm"
                elif ev["tipo"] == "Delay":
                    overrides.setdefault(par, {})["route_congestion_index"] = 5

        custos = build_cost_map(self.rede, self.pipeline, modelo_ctx,
                                overrides=overrides, max_speed_km_h=self.max_speed)
        self._cache[chave] = (custos, fechados)
        return self._cache[chave]

    def _subrede(self, evitar: set[str], fechados: set[tuple[str, str]]) -> AirNetwork:
        net = AirNetwork()
        for a in self.rede.airports.values():
            if a.code not in evitar:
                net.add_airport(a)
        for origem, voos in self.rede.flights.items():
            if origem in evitar:
                continue
            for v in voos:
                destino = v.destination.code
                if destino in evitar or (origem, destino) in fechados:
                    continue
                net.add_flight(v)
        return net

    @staticmethod
    def _km(net: AirNetwork, caminho: list[str]) -> float:
        return sum(min(f.distance for f in net.get_outgoing_flights(u)
                       if f.destination.code == v)
                   for u, v in zip(caminho, caminho[1:]))