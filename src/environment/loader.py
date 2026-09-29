import json
from pathlib import Path

from .airport import Airport
from .flight import Flight
from .graph import AirNetwork


def load_network(
    map_path: str | Path,
    airports_path: str | Path,
) -> AirNetwork:
    """
    Carrega uma malha aérea a partir de dois arquivos JSON:

    - airports_path: catálogo dos aeroportos;
    - map_path: definição do mapa e suas conexões.

    O mapa informa quais aeroportos fazem parte daquele cenário.
    """

    map_file = Path(map_path)
    airports_file = Path(airports_path)

    if not map_file.exists():
        raise FileNotFoundError(
            f"Arquivo do mapa não encontrado: {map_file}"
        )

    if not airports_file.exists():
        raise FileNotFoundError(
            f"Catálogo de aeroportos não encontrado: {airports_file}"
        )

    with airports_file.open("r", encoding="utf-8") as file:
        airports_data = json.load(file)

    with map_file.open("r", encoding="utf-8") as file:
        map_data = json.load(file)

    airport_catalog = {
        airport_data["code"]: airport_data
        for airport_data in airports_data["airports"]
    }

    network = AirNetwork()

    for airport_code in map_data["airports"]:
        if airport_code not in airport_catalog:
            raise ValueError(
                f"Aeroporto '{airport_code}' não existe no catálogo."
            )

        airport_data = airport_catalog[airport_code]

        airport = Airport(
            code=airport_data["code"],
            name=airport_data["name"],
            latitude=airport_data["latitude"],
            longitude=airport_data["longitude"],
        )

        network.add_airport(airport)

    for flight_data in map_data["flights"]:
        origin_code = flight_data["origin"]
        destination_code = flight_data["destination"]

        if origin_code not in airport_catalog:
            raise ValueError(
                f"Aeroporto de origem '{origin_code}' não existe no catálogo."
            )

        if destination_code not in airport_catalog:
            raise ValueError(
                f"Aeroporto de destino '{destination_code}' não existe no catálogo."
            )

        origin = network.get_airport(origin_code)
        destination = network.get_airport(destination_code)

        flight = Flight(
            origin=origin,
            destination=destination,
            distance=flight_data["distance"],
        )

        network.add_flight(flight)

    return network