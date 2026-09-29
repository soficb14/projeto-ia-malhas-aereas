import heapq
from dataclasses import dataclass
from itertools import count

from ..environment.airport import Airport
from ..environment.graph import AirNetwork
from .heuristics import straight_line_distance


@dataclass
class SearchResult:
    """
    Resultado de uma busca no grafo.
    """

    path: list[Airport]
    cost: float
    expanded_nodes: int


def a_star_search(
    network: AirNetwork,
    start: str,
    goal: str,
) -> SearchResult | None:
    """
    Executa o algoritmo A* entre dois aeroportos.

    O custo da busca é a distância total percorrida.
    A heurística utilizada é a distância em linha reta
    entre o aeroporto atual e o destino.
    """

    start_airport = network.get_airport(start)
    goal_airport = network.get_airport(goal)

    if start == goal:
        return SearchResult(
            path=[start_airport],
            cost=0.0,
            expanded_nodes=0,
        )

    counter = count()

    frontier: list[tuple[float, int, str]] = []

    initial_heuristic = straight_line_distance(
        start_airport,
        goal_airport,
    )

    heapq.heappush(
        frontier,
        (initial_heuristic, next(counter), start),
    )

    cost_so_far: dict[str, float] = {
        start: 0.0
    }

    parent: dict[str, str | None] = {
        start: None
    }

    expanded_nodes = 0

    while frontier:
        _, _, current = heapq.heappop(frontier)

        current_cost = cost_so_far[current]

        expanded_nodes += 1

        if current == goal:
            path = _reconstruct_path(
                network=network,
                parent=parent,
                goal=goal,
            )

            return SearchResult(
                path=path,
                cost=current_cost,
                expanded_nodes=expanded_nodes,
            )

        for flight in network.get_outgoing_flights(current):
            neighbor = flight.destination.code

            new_cost = current_cost + flight.distance

            previous_cost = cost_so_far.get(neighbor)

            if previous_cost is not None and new_cost >= previous_cost:
                continue

            cost_so_far[neighbor] = new_cost
            parent[neighbor] = current

            heuristic = straight_line_distance(
                flight.destination,
                goal_airport,
            )

            priority = new_cost + heuristic

            heapq.heappush(
                frontier,
                (
                    priority,
                    next(counter),
                    neighbor,
                ),
            )

    return None


def _reconstruct_path(
    network: AirNetwork,
    parent: dict[str, str | None],
    goal: str,
) -> list[Airport]:
    """
    Reconstrói o caminho encontrado pelo A*.
    """

    path_codes = []
    current: str | None = goal

    while current is not None:
        path_codes.append(current)
        current = parent[current]

    path_codes.reverse()

    return [
        network.get_airport(code)
        for code in path_codes
    ]