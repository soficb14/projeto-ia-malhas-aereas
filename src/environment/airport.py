from dataclasses import dataclass


@dataclass(frozen=True)
class Airport:
    """
    Representa um aeroporto da malha aérea.

    Cada aeroporto corresponde a um nó do grafo direcionado.
    """

    code: str
    name: str
    latitude: float
    longitude: float

    def __str__(self) -> str:
        return self.code