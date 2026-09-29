from pathlib import Path

from .environment.loader import load_network
from .experiments import ExperimentResult, run_experiment
from .search.astar import a_star_search
from .search.bfs import breadth_first_search


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "data" / "maps"

AIRPORTS_PATH = MAPS_DIR / "airports.json"

MAPS = {
    "pequeno": MAPS_DIR / "mapa_pequeno.json",
    "medio": MAPS_DIR / "mapa_medio.json",
    "grande": MAPS_DIR / "mapa_grande.json",
}

ROUTES = {
    "pequeno": ("ATL", "LAX"),
    "medio": ("SEA", "MEM"),
    "grande": ("SEA", "BOS"),
}


def run_all_experiments() -> list[ExperimentResult]:
    """
    Executa BFS e A* nos três mapas da Fase I.
    """

    results = []

    algorithms = [
        ("BFS", breadth_first_search),
        ("A*", a_star_search),
    ]

    for map_name, map_path in MAPS.items():
        network = load_network(
            map_path,
            AIRPORTS_PATH,
        )

        start, goal = ROUTES[map_name]

        for algorithm_name, search_function in algorithms:
            result = run_experiment(
                map_name=map_name,
                algorithm=algorithm_name,
                search_function=search_function,
                network=network,
                start=start,
                goal=goal,
            )

            results.append(result)

    return results


def print_results(results: list[ExperimentResult]) -> None:
    """
    Exibe os resultados dos experimentos no terminal.
    """

    print("\nRESULTADOS DOS EXPERIMENTOS — FASE I")
    print("=" * 90)

    header = (
        f"{'Mapa':<10}"
        f"{'Algoritmo':<12}"
        f"{'Custo (km)':>14}"
        f"{'Nós expandidos':>18}"
        f"{'Tempo (ms)':>14}"
    )

    print(header)
    print("-" * 90)

    for result in results:
        cost = (
            f"{result.cost:.2f}"
            if result.cost is not None
            else "N/A"
        )

        print(
            f"{result.map_name:<10}"
            f"{result.algorithm:<12}"
            f"{cost:>14}"
            f"{result.expanded_nodes:>18}"
            f"{result.execution_time_ms:>14.4f}"
        )

    print("=" * 90)


if __name__ == "__main__":
    experiment_results = run_all_experiments()
    print_results(experiment_results)