import json

import pytest

from src.environment.loader import load_network
from src.search.heuristics import straight_line_distance


MAPS = [
    "data/maps/mapa_pequeno.json",
    "data/maps/mapa_medio.json",
    "data/maps/mapa_grande.json",
]

AIRPORTS_PATH = "data/maps/airports.json"


@pytest.mark.parametrize("map_path", MAPS)
def test_flight_distance_is_not_smaller_than_straight_line_distance(
    map_path,
):
    """
    Verifica a condição necessária para a admissibilidade da heurística.

    Para cada voo:

        distância do voo >= distância em linha reta

    Dessa forma, a heurística baseada na distância geodésica
    não superestima o custo de atravessar um trecho da malha.
    """

    network = load_network(
        map_path,
        AIRPORTS_PATH,
    )

    with open(
        map_path,
        "r",
        encoding="utf-8",
    ) as file:
        map_data = json.load(file)

    for flight in map_data["flights"]:
        origin = network.get_airport(
            flight["origin"]
        )

        destination = network.get_airport(
            flight["destination"]
        )

        straight_line = straight_line_distance(
            origin,
            destination,
        )

        flight_distance = flight["distance"]

        assert flight_distance >= straight_line, (
            f"Voo {origin.code} -> {destination.code}: "
            f"distância do voo ({flight_distance:.2f} km) "
            f"é menor que a distância em linha reta "
            f"({straight_line:.2f} km)."
        )