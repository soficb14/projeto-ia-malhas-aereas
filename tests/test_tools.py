import heapq
import pytest
from src.agent.tools import FlightTools

KM = {("CLT", "ATL"): 400, ("ATL", "LAX"): 3100, ("CLT", "DFW"): 1700,
      ("DFW", "LAX"): 1900, ("CLT", "LAX"): 3400}
NOMES = {"CLT": "Charlotte", "ATL": "Atlanta", "DFW": "Dallas", "LAX": "Los Angeles"}


class FakeBackend:
    def __init__(self):
        self.adj = {}
        for (a, b), km in KM.items():
            self.adj.setdefault(a, {})[b] = km
            self.adj.setdefault(b, {})[a] = km

    def aeroportos(self):
        return NOMES

    def _dijkstra(self, o, d, custo, evitar):
        pq, vis = [(0, o, [o])], set()
        while pq:
            c, n, p = heapq.heappop(pq)
            if n == d:
                return c, p
            if n in vis:
                continue
            vis.add(n)
            for m in self.adj.get(n, {}):
                if m not in evitar and m not in vis:
                    heapq.heappush(pq, (c + custo(n, m), m, p + [m]))
        return None

    def _km(self, p):
        return sum(self.adj[a][b] for a, b in zip(p, p[1:]))

    def rota_mais_curta(self, o, d, evitar, contexto=None):
        r = self._dijkstra(o, d, lambda a, b: self.adj[a][b], evitar)
        return r and {"caminho": r[1], "km": r[0]}

    def _t(self, a, b, ctx):
        f = 1.5 if ctx["clima"] == "Storm" else 1.0
        return self.adj[a][b] / 10 * f

    def rota_mais_rapida(self, o, d, ctx, evitar):
        r = self._dijkstra(o, d, lambda a, b: self._t(a, b, ctx), evitar)
        return r and {"caminho": r[1], "km": self._km(r[1]), "min": r[0]}

    def tempo_da_rota(self, p, ctx):
        return sum(self._t(a, b, ctx) for a, b in zip(p, p[1:]))


@pytest.fixture
def tools():
    return FlightTools(FakeBackend())


def test_rota_ok(tools):
    r = tools.buscar_rota("clt", "lax")
    assert r["ok"] and r["rota"][0] == "CLT" and r["rota"][-1] == "LAX"
    assert r["economia_min"] >= 0


def test_evitar(tools):
    r = tools.buscar_rota("CLT", "LAX", evitar=["ATL", "DFW"])
    assert r["ok"] and r["rota"] == ["CLT", "LAX"]


@pytest.mark.parametrize("kw", [
    {"origem": "CLT", "destino": "XYZ"},
    {"origem": "CLT", "destino": "CLT"},
    {"origem": "CLT", "destino": "LAX", "evitar": ["LAX"]},
    {"origem": "CLT", "destino": "LAX", "clima": "Fog"},
    {"origem": "CLT", "destino": "LAX", "vento": 99},
    {"origem": "CLT", "destino": "LAX", "congestionamento": 9},
    {"origem": "CLT", "destino": "LAX",
     "eventos": [{"de": "CLT", "para": "ATL", "tipo": "X"}]},
])
def test_validacao(tools, kw):
    assert tools.buscar_rota(**kw)["ok"] is False