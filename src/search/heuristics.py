from math import asin, cos, radians, sin, sqrt

from ..environment.airport import Airport


EARTH_RADIUS_KM = 6371.0


def straight_line_distance(
    origin: Airport,
    destination: Airport,
) -> float:
    """
    Calcula a distância em linha reta aproximada entre dois aeroportos.

    A distância é calculada usando a fórmula de Haversine,
    considerando as coordenadas geográficas dos aeroportos.
    """

    latitude_1 = radians(origin.latitude)
    longitude_1 = radians(origin.longitude)

    latitude_2 = radians(destination.latitude)
    longitude_2 = radians(destination.longitude)

    delta_latitude = latitude_2 - latitude_1
    delta_longitude = longitude_2 - longitude_1

    haversine = (
        sin(delta_latitude / 2) ** 2
        + cos(latitude_1)
        * cos(latitude_2)
        * sin(delta_longitude / 2) ** 2
    )

    angular_distance = 2 * asin(sqrt(haversine))

    return EARTH_RADIUS_KM * angular_distance

MAX_SPEED_KMH = 900.0   # constante ÚNICA: usada na heurística e no piso do build_cost_map


def time_lower_bound(origin: Airport, destination: Airport) -> float:
    """Tempo mínimo (min) entre dois aeroportos: linha reta à velocidade máxima."""
    return straight_line_distance(origin, destination) / MAX_SPEED_KMH * 60.0


def heuristic_for_metric(metric: str, origin: Airport, destination: Airport) -> float:
    if metric == "distance":
        return straight_line_distance(origin, destination)
    if metric in ("estimated_time", "predicted_time"):
        return time_lower_bound(origin, destination)
    if metric == "price":
        return 0.0   # sem garantia de preço mínimo por km: h = 0 é admissível
    raise ValueError(f"Métrica desconhecida: {metric}")


def check_heuristic(network, metric: str, tol: float = 1e-9) -> list:
    """
    Verifica se o custo de cada aresta é >= ao limite inferior entre seus extremos.
    Como a distância haversine respeita a desigualdade triangular, isso garante
    que a heurística é admissível e consistente. Retorna os voos que violam.
    """
    violations = []
    for flights in network.flights.values():
        for f in flights:
            cost = network.get_flight_cost(f, metric)
            if cost < heuristic_for_metric(metric, f.origin, f.destination) - tol:
                violations.append(f)
    return violations