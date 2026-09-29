from dataclasses import dataclass

from .airport import Airport


@dataclass(frozen=True)
class Flight:
    """
    Representa um voo direto entre dois aeroportos.

    Cada voo corresponde a uma aresta direcionada do grafo.
    """

    origin: Airport
    destination: Airport
    distance: float

    def __post_init__(self) -> None:
        if self.distance <= 0:
            raise ValueError("A distância do voo deve ser maior que zero.")

    def __str__(self) -> str:
        return f"{self.origin.code} -> {self.destination.code} ({self.distance:.1f} km)"