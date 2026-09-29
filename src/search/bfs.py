from collections import deque

from ..environment.airport import Airport
from ..environment.graph import AirNetwork
from .result import SearchResult


def breadth_first_search(
    network: AirNetwork,
    start: str,
    goal: str,
) -> SearchResult | None:
    """
    Executa uma busca em largura (BFS) entre dois aeroportos.

    A BFS considera o número de voos realizados como critério
    para definir a ordem de exploração.

    Retorna None caso não exista caminho entre origem e destino.
    """

    network.get_airport(start)
    network.get_airport(goal)

    if start == goal:
        airport = network.get_airport(start)

        return SearchResult(
            path=[airport],
            cost=0.0,
            expanded_nodes=0,
        )

    frontier = deque([start])
    visited = {start}

    parent: dict[str, str | None] = {
        start: None
    }

    expanded_nodes = 0

    while frontier:
        current = frontier.popleft()
        expanded_nodes += 1

        for flight in network.get_outgoing_flights(current):
            neighbor = flight.destination.code

            if neighbor in visited:
                continue

            visited.add(neighbor)
            parent[neighbor] = current

            if neighbor == goal:
                path = _reconstruct_path(
                    network=network,
                    parent=parent,
                    goal=goal,
                )

                cost = _calculate_path_cost(
                    network=network,
                    path=path,
                )

                return SearchResult(
                    path=path,
                    cost=cost,
                    expanded_nodes=expanded_nodes,
                )

            frontier.append(neighbor)

    return None


def _reconstruct_path(
    network: AirNetwork,
    parent: dict[str, str | None],
    goal: str,
) -> list[Airport]:
    """
    Reconstrói o caminho encontrado usando o mapa de predecessores.
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


def _calculate_path_cost(
    network: AirNetwork,
    path: list[Airport],
) -> float:
    """
    Calcula a distância total do caminho encontrado.
    """

    total_distance = 0.0

    for origin, destination in zip(path, path[1:]):
        flights = network.get_outgoing_flights(origin.code)

        for flight in flights:
            if flight.destination.code == destination.code:
                total_distance += flight.distance
                break
        else:
            raise ValueError(
                f"Não existe voo entre {origin.code} e {destination.code}."
            )

    return total_distance