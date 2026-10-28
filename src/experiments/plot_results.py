import csv
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

CSV_PATH = RESULTS_DIR / "fase1_resultados.csv"

NODES_PLOT_PATH = RESULTS_DIR / "nos_expandidos.png"
TIME_PLOT_PATH = RESULTS_DIR / "tempo_execucao.png"


def load_results() -> list[dict]:
    """Carrega os resultados experimentais do CSV."""

    with CSV_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def create_nodes_plot(results: list[dict]) -> None:
    """Gera o gráfico de nós expandidos."""

    maps = ["pequeno", "medio", "grande"]

    bfs_values = []
    astar_values = []

    for map_name in maps:
        for result in results:
            if (
                result["mapa"] == map_name
                and result["algoritmo"] == "BFS"
            ):
                bfs_values.append(
                    int(result["nos_expandidos"])
                )

            if (
                result["mapa"] == map_name
                and result["algoritmo"] == "A*"
            ):
                astar_values.append(
                    int(result["nos_expandidos"])
                )

    positions = range(len(maps))
    width = 0.35

    plt.figure(figsize=(8, 5))

    plt.bar(
        [position - width / 2 for position in positions],
        bfs_values,
        width,
        label="BFS",
    )

    plt.bar(
        [position + width / 2 for position in positions],
        astar_values,
        width,
        label="A*",
    )

    plt.xticks(
        list(positions),
        ["Pequeno", "Médio", "Grande"],
    )

    plt.xlabel("Tamanho do mapa")
    plt.ylabel("Nós expandidos")
    plt.title("Comparação de nós expandidos — BFS × A*")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        NODES_PLOT_PATH,
        dpi=150,
    )

    plt.close()


def create_time_plot(results: list[dict]) -> None:
    """Gera o gráfico de tempo de execução."""

    maps = ["pequeno", "medio", "grande"]

    bfs_values = []
    astar_values = []

    for map_name in maps:
        for result in results:
            if (
                result["mapa"] == map_name
                and result["algoritmo"] == "BFS"
            ):
                bfs_values.append(
                    float(result["tempo_ms"])
                )

            if (
                result["mapa"] == map_name
                and result["algoritmo"] == "A*"
            ):
                astar_values.append(
                    float(result["tempo_ms"])
                )

    positions = range(len(maps))
    width = 0.35

    plt.figure(figsize=(8, 5))

    plt.bar(
        [position - width / 2 for position in positions],
        bfs_values,
        width,
        label="BFS",
    )

    plt.bar(
        [position + width / 2 for position in positions],
        astar_values,
        width,
        label="A*",
    )

    plt.xticks(
        list(positions),
        ["Pequeno", "Médio", "Grande"],
    )

    plt.xlabel("Tamanho do mapa")
    plt.ylabel("Tempo de execução (ms)")
    plt.title("Comparação de tempo de execução — BFS × A*")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        TIME_PLOT_PATH,
        dpi=150,
    )

    plt.close()


def main() -> None:
    """Gera os gráficos a partir dos resultados experimentais."""

    results = load_results()

    create_nodes_plot(results)
    create_time_plot(results)

    print(f"Gráfico de nós: {NODES_PLOT_PATH}")
    print(f"Gráfico de tempo: {TIME_PLOT_PATH}")


if __name__ == "__main__":
    main()