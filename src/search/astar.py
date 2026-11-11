import heapq
from itertools import count

from ..environment.airport import Airport
from ..environment.graph import AirNetwork
from .heuristics import heuristic_for_metric
from .result import SearchResult


def a_star_search(
    network: AirNetwork,
    start: str,
    goal: str,
    metric: str = "distance",
) -> SearchResult | None:
    """
    A* entre dois aeroportos. A métrica de custo pode ser:
    'distance', 'estimated_time', 'price' ou 'predicted_time' (Fase 2).
    """
    start_airport = network.get_airport(start)
    goal_airport = network.get_airport(goal)

    if start == goal:
        return SearchResult(path=[start_airport], cost=0.0, expanded_nodes=0)

    counter = count()
    frontier: list[tuple[float, int, str]] = [
        (heuristic_for_metric(metric, start_airport, goal_airport), next(counter), start)
    ]
    cost_so_far: dict[str, float] = {start: 0.0}
    parent: dict[str, str | None] = {start: None}
    closed: set[str] = set()
    expanded_nodes = 0

    while frontier:
        _, _, current = heapq.heappop(frontier)

        if current in closed:        # entrada velha do heap: ignora
            continue
        closed.add(current)

        current_cost = cost_so_far[current]
        expanded_nodes += 1

        if current == goal:
            path = _reconstruct_path(network=network, parent=parent, goal=goal)
            return SearchResult(path=path, cost=current_cost, expanded_nodes=expanded_nodes)

        for flight in network.get_outgoing_flights(current):
            neighbor = flight.destination.code
            new_cost = current_cost + network.get_flight_cost(flight, metric)

            previous_cost = cost_so_far.get(neighbor)
            if previous_cost is not None and new_cost >= previous_cost:
                continue

            cost_so_far[neighbor] = new_cost
            parent[neighbor] = current

            h = heuristic_for_metric(metric, flight.destination, goal_airport)
            heapq.heappush(frontier, (new_cost + h, next(counter), neighbor))

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