from src.environment.loader import load_network
from src.search.bfs import breadth_first_search


AIRPORTS_PATH = "data/maps/airports.json"

MAPS = [
    ("mapa_pequeno", "data/maps/mapa_pequeno.json"),
    ("mapa_medio", "data/maps/mapa_medio.json"),
    ("mapa_grande", "data/maps/mapa_grande.json"),
]


def test_all_maps_have_expected_sizes():
    expected_sizes = {
        "mapa_pequeno": 10,
        "mapa_medio": 25,
        "mapa_grande": 40,
    }

    for map_name, map_path in MAPS:
        network = load_network(
            map_path,
            AIRPORTS_PATH,
        )

        assert network.number_of_airports() == expected_sizes[map_name]


def test_all_maps_have_route_between_extremes():
    routes = {
        "mapa_pequeno": ("ATL", "LAX"),
        "mapa_medio": ("SEA", "MEM"),
        "mapa_grande": ("SEA", "BOS"),
    }

    for map_name, map_path in MAPS:
        network = load_network(
            map_path,
            AIRPORTS_PATH,
        )

        start, goal = routes[map_name]

        result = breadth_first_search(
            network,
            start=start,
            goal=goal,
        )

        assert result is not None
        assert result.path[0].code == start
        assert result.path[-1].code == goal


def test_map_airports_belong_to_catalog():
    import json

    with open(AIRPORTS_PATH, "r", encoding="utf-8") as file:
        catalog = json.load(file)

    catalog_codes = {
        airport["code"]
        for airport in catalog["airports"]
    }

    for _, map_path in MAPS:
        with open(map_path, "r", encoding="utf-8") as file:
            map_data = json.load(file)

        assert set(map_data["airports"]).issubset(catalog_codes)