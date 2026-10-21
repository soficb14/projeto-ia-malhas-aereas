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

# Definimos as métricas que queremos testar para o A*
METRICS = ["distance", "estimated_time", "price"]


def run_all_experiments() -> list[ExperimentResult]:
    """
    Executa BFS e A* (para múltiplas métricas) nos três mapas da Fase I.
    """

    results = []

    for map_name, map_path in MAPS.items():
        network = load_network(
            map_path,
            AIRPORTS_PATH,
        )

        start, goal = ROUTES[map_name]

        # 1. Executa o BFS tradicional (otimiza por saltos/distância padrão)
        bfs_result = run_experiment(
            map_name=map_name,
            algorithm="BFS",
            search_function=breadth_first_search,
            network=network,
            start=start,
            goal=goal,
        )
        results.append(bfs_result)

        # 2. Executa o A* para cada uma das métricas multiobjetivo
        for metric in METRICS:
            alg_name = f"A* ({metric})"
            
            # Criamos uma função lambda para prender o parâmetro 'metric' na chamada do A*
            def a_star_wrapped(net, s, g):
                return a_star_search(net, s, g, metric=metric)

            result = run_experiment(
                map_name=map_name,
                algorithm=alg_name,
                search_function=a_star_wrapped,
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

    print("\nRESULTADOS DOS EXPERIMENTOS — MÚLTIPLAS MÉTRICAS")
    print("=" * 95)

    header = (
        f"{'Mapa':<10}"
        f"{'Algoritmo / Métrica':<20}"
        f"{'Custo':>14}"
        f"{'Nós expandidos':>18}"
        f"{'Tempo (ms)':>14}"
    )

    print(header)
    print("-" * 95)

    for result in results:
        cost = (
            f"{result.cost:.2f}"
            if result.cost is not None
            else "N/A"
        )

        print(
            f"{result.map_name:<10}"
            f"{result.algorithm:<20}"
            f"{cost:>14}"
            f"{result.expanded_nodes:>18}"
            f"{result.execution_time_ms:>14.4f}"
        )

    print("=" * 95)


if __name__ == "__main__":
    experiment_results = run_all_experiments()
    print_results(experiment_results)