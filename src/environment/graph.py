from collections import defaultdict

from .airport import Airport
from .flight import Flight


class AirNetwork:
    """
    Representa a malha aérea como um grafo direcionado.

    Os aeroportos são os nós e os voos diretos são as arestas.
    """

    def __init__(self) -> None:
        self.airports: dict[str, Airport] = {}
        self.flights: dict[str, list[Flight]] = defaultdict(list)

    def add_airport(self, airport: Airport) -> None:
        """
        Adiciona um aeroporto à malha.
        """
        if airport.code in self.airports:
            raise ValueError(
                f"O aeroporto {airport.code} já existe na malha."
            )

        self.airports[airport.code] = airport

    def add_flight(self, flight: Flight) -> None:
        """
        Adiciona um voo direcionado à malha.

        Os aeroportos de origem e destino precisam existir
        previamente no grafo.
        """
        origin_code = flight.origin.code
        destination_code = flight.destination.code

        if origin_code not in self.airports:
            raise ValueError(
                f"O aeroporto de origem {origin_code} não existe na malha."
            )

        if destination_code not in self.airports:
            raise ValueError(
                f"O aeroporto de destino {destination_code} não existe na malha."
            )

        self.flights[origin_code].append(flight)

    def get_airport(self, code: str) -> Airport:
        """
        Retorna um aeroporto pelo código IATA.
        """
        try:
            return self.airports[code]
        except KeyError:
            raise ValueError(
                f"O aeroporto {code} não existe na malha."
            ) from None

    def get_outgoing_flights(self, airport_code: str) -> list[Flight]:
        """
        Retorna todos os voos que partem de determinado aeroporto.
        """
        if airport_code not in self.airports:
            raise ValueError(
                f"O aeroporto {airport_code} não existe na malha."
            )

        return self.flights[airport_code]

    def get_neighbors(self, airport_code: str) -> list[Airport]:
        """
        Retorna os aeroportos diretamente alcançáveis a partir
        de determinado aeroporto.
        """
        return [
            flight.destination
            for flight in self.get_outgoing_flights(airport_code)
        ]

    def number_of_airports(self) -> int:
        """
        Retorna a quantidade de aeroportos da malha.
        """
        return len(self.airports)

    def number_of_flights(self) -> int:
        """
        Retorna a quantidade de voos direcionados da malha.
        """
        return sum(len(flights) for flights in self.flights.values())