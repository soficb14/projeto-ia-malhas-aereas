from dataclasses import dataclass

from ..environment.airport import Airport


@dataclass
class SearchResult:
    """
    Resultado de uma busca no grafo.
    """

    path: list[Airport]
    cost: float
    expanded_nodes: int