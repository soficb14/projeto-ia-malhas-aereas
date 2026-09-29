from src.environment.loader import load_network

from src.search.astar import a_star_search
from src.search.bfs import breadth_first_search

MAP_PATH = "data/maps/mapa_pequeno.json"
AIRPORTS_PATH = "data/maps/airports.json"


def test_bfs_finds_route():
    network = load_network(
        MAP_PATH,
        AIRPORTS_PATH,
        )

    result = breadth_first_search(
        network,
        start="ATL",
        goal="LAX",
    )

    assert result is not None
    assert result.path[0].code == "ATL"
    assert result.path[-1].code == "LAX"


def test_bfs_calculates_path_cost():
    network = load_network(
        MAP_PATH,
        AIRPORTS_PATH,
        )

    result = breadth_first_search(
        network,
        start="ATL",
        goal="LAX",
    )

    assert result is not None
    assert result.cost > 0


def test_bfs_start_equals_goal():
    network = load_network(
        MAP_PATH,
        AIRPORTS_PATH,
        )

    result = breadth_first_search(
        network,
        start="ATL",
        goal="ATL",
    )

    assert result is not None
    assert [airport.code for airport in result.path] == ["ATL"]
    assert result.cost == 0.0
    assert result.expanded_nodes == 0


def test_bfs_and_astar_can_find_different_costs():
    network = load_network(
        MAP_PATH,
        AIRPORTS_PATH,
        )

    bfs_result = breadth_first_search(
        network,
        start="ATL",
        goal="LAX",
    )

    astar_result = a_star_search(
        network,
        start="ATL",
        goal="LAX",
    )

    assert bfs_result is not None
    assert astar_result is not None

    # A BFS encontra a rota com menos voos.
    assert len(bfs_result.path) < len(astar_result.path)

    # O A* encontra a rota de menor distância.
    assert bfs_result.cost > astar_result.cost

    assert bfs_result.cost == 4500
    assert astar_result.cost == 3602