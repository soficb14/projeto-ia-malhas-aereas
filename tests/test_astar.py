from src.environment.loader import load_network
from src.search.astar import a_star_search


MAP_PATH = "data/maps/mapa_pequeno.json"


def test_astar_finds_route():
    network = load_network(MAP_PATH)

    result = a_star_search(
        network,
        start="ATL",
        goal="LAX",
    )

    assert result is not None
    assert result.path[0].code == "ATL"
    assert result.path[-1].code == "LAX"


def test_astar_calculates_path_cost():
    network = load_network(MAP_PATH)

    result = a_star_search(
        network,
        start="ATL",
        goal="LAX",
    )

    assert result is not None
    assert result.cost > 0


def test_astar_start_equals_goal():
    network = load_network(MAP_PATH)

    result = a_star_search(
        network,
        start="ATL",
        goal="ATL",
    )

    assert result is not None
    assert [airport.code for airport in result.path] == ["ATL"]
    assert result.cost == 0.0
    assert result.expanded_nodes == 0