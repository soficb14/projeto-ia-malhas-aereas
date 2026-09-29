import csv
from pathlib import Path

from .experiments import ExperimentResult


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

CSV_PATH = RESULTS_DIR / "fase1_resultados.csv"


def export_results_to_csv(
    results: list[ExperimentResult],
    output_path: Path = CSV_PATH,
) -> None:
    """
    Salva os resultados dos experimentos em formato CSV.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "mapa",
                "algoritmo",
                "origem",
                "destino",
                "custo_km",
                "nos_expandidos",
                "tempo_ms",
                "rota",
            ]
        )

        for result in results:
            writer.writerow(
                [
                    result.map_name,
                    result.algorithm,
                    result.start,
                    result.goal,
                    result.cost,
                    result.expanded_nodes,
                    f"{result.execution_time_ms:.6f}",
                    " -> ".join(result.path),
                ]
            )


if __name__ == "__main__":
    from .run_experiments import run_all_experiments

    experiment_results = run_all_experiments()

    export_results_to_csv(experiment_results)

    print(f"Resultados salvos em: {CSV_PATH}")