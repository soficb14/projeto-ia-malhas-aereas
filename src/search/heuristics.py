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