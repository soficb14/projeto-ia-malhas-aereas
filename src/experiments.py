from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from .environment.graph import AirNetwork
from .search.result import SearchResult


@dataclass
class ExperimentResult:
    """
    Resultado da execução de uma estratégia de busca.
    """

    algorithm: str
    start: str
    goal: str
    cost: float | None
    expanded_nodes: int
    execution_time_ms: float
    path: list[str]


def run_experiment(
    algorithm: str,
    search_function: Callable[
        [AirNetwork, str, str],
        SearchResult | None,
    ],
    network: AirNetwork,
    start: str,
    goal: str,
) -> ExperimentResult:
    """
    Executa uma busca e registra suas métricas experimentais.

    Mede:
    - custo da rota;
    - nós expandidos;
    - tempo de execução.
    """

    start_time = perf_counter()

    result = search_function(
        network,
        start,
        goal,
    )

    end_time = perf_counter()

    execution_time_ms = (end_time - start_time) * 1000

    if result is None:
        return ExperimentResult(
            algorithm=algorithm,
            start=start,
            goal=goal,
            cost=None,
            expanded_nodes=result.expanded_nodes if result else 0,
            execution_time_ms=execution_time_ms,
            path=[],
        )

    return ExperimentResult(
        algorithm=algorithm,
        start=start,
        goal=goal,
        cost=result.cost,
        expanded_nodes=result.expanded_nodes,
        execution_time_ms=execution_time_ms,
        path=[airport.code for airport in result.path],
    )