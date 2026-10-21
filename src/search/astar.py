import heapq
from itertools import count

from ..environment.airport import Airport
from ..environment.graph import AirNetwork
from .heuristics import straight_line_distance
from .result import SearchResult


def a_star_search(
    network: AirNetwork,
    start: str,
    goal: str,
    metric: str = "distance",  # <- Parâmetro novo para escolher a métrica
) -> SearchResult | None:
    """
    Executa o algoritmo A* entre dois aeroportos.

    O custo da busca pode ser configurado por distância, tempo ou preço.
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

    # Heurística inicial (em linha reta - km)
    initial_heuristic = straight_line_distance(
        start_airport,
        goal_airport,
    )

    # Se a métrica for tempo ou preço, podemos ajustar a escala da heurística se necessário,
    # mas mantemos a base por enquanto.
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

            # Seleciona dinamicamente o custo do voo com base na métrica
            if metric == "distance":
                flight_cost = flight.distance
            elif metric == "estimated_time":
                flight_cost = flight.estimated_time
            elif metric == "price":
                flight_cost = flight.price
            else:
                raise ValueError(f"Métrica desconhecida: {metric}")

            new_cost = current_cost + flight_cost

            previous_cost = cost_so_far.get(neighbor)

            if previous_cost is not None and new_cost >= previous_cost:
                continue

            cost_so_far[neighbor] = new_cost
            parent[neighbor] = current

            # Heurística: se a métrica for diferente de distância pura, 
            # podes calibrar/converter a heurística proporcionalmente se desejar.
            heuristic = straight_line_distance(
                flight.destination,
                goal_airport,
            )
            
            # Ajuste proporcional simples de exemplo para tempo/preço se quiseres manter a admissibilidade:
            if metric == "estimated_time":
                heuristic = heuristic / 800.0 * 60.0  # Exemplo: conversão baseada em velocidade Média
            elif metric == "price":
                heuristic = heuristic * 0.15          # Exemplo: custo médio por km em dólar

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