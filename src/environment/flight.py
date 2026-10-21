from dataclasses import dataclass
from .airport import Airport


@dataclass(frozen=True)
class Flight:
    """
    Representa um voo direto entre dois aeroportos.

    Cada voo corresponde a uma aresta direcionada do grafo,
    suportando múltiplos critérios de custo (distância, tempo e preço).
    """

    origin: Airport
    destination: Airport
    distance: float
    estimated_time: float = 0.0
    price: float = 0.0

    def __post_init__(self) -> None:
        if self.distance <= 0:
            raise ValueError("A distância do voo deve ser maior que zero.")
        if self.estimated_time < 0:
            raise ValueError("O tempo estimado do voo não pode ser negativo.")
        if self.price < 0:
            raise ValueError("O preço do voo não pode ser negativo.")

    def __str__(self) -> str:
        return (
            f"{self.origin.code} -> {self.destination.code} "
            f"({self.distance:.1f} km, {self.estimated_time:.0f} min, R${self.price:.2f})"
        )