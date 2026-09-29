import json
from pathlib import Path

from .airport import Airport
from .flight import Flight
from .graph import AirNetwork


def load_network(file_path: str | Path) -> AirNetwork:
    """
    Carrega uma malha aérea a partir de um arquivo JSON.

    O arquivo deve conter:
    - uma lista de aeroportos;
    - uma lista de voos direcionados.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo do mapa não encontrado: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    network = AirNetwork()

    airports: dict[str, Airport] = {}

    for airport_data in data["airports"]:
        airport = Airport(
            code=airport_data["code"],
            name=airport_data["name"],
            latitude=airport_data["latitude"],
            longitude=airport_data["longitude"],
        )

        network.add_airport(airport)
        airports[airport.code] = airport

    for flight_data in data["flights"]:
        origin = airports[flight_data["origin"]]
        destination = airports[flight_data["destination"]]

        flight = Flight(
            origin=origin,
            destination=destination,
            distance=flight_data["distance"],
        )

        network.add_flight(flight)

    return network