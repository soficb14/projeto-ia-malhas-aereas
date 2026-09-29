import json
import math
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

AIRPORTS_PATH = BASE_DIR / "data" / "maps" / "airports.json"

MAPS = [
    BASE_DIR / "data" / "maps" / "mapa_pequeno.json",
    BASE_DIR / "data" / "maps" / "mapa_medio.json",
    BASE_DIR / "data" / "maps" / "mapa_grande.json",
]

EARTH_RADIUS_KM = 6371.0


def straight_line_distance(origin, destination):
    latitude_1 = math.radians(origin["latitude"])
    longitude_1 = math.radians(origin["longitude"])

    latitude_2 = math.radians(destination["latitude"])
    longitude_2 = math.radians(destination["longitude"])

    delta_latitude = latitude_2 - latitude_1
    delta_longitude = longitude_2 - longitude_1

    haversine = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(delta_longitude / 2) ** 2
    )

    angular_distance = 2 * math.asin(math.sqrt(haversine))

    return EARTH_RADIUS_KM * angular_distance


with AIRPORTS_PATH.open("r", encoding="utf-8") as file:
    airports_data = json.load(file)


airports = {
    airport["code"]: airport
    for airport in airports_data["airports"]
}


for map_path in MAPS:
    with map_path.open("r", encoding="utf-8") as file:
        map_data = json.load(file)

    corrections = 0

    for flight in map_data["flights"]:
        origin = airports[flight["origin"]]
        destination = airports[flight["destination"]]

        minimum_distance = straight_line_distance(
            origin,
            destination,
        )

        current_distance = flight["distance"]

        if current_distance < minimum_distance:
            new_distance = math.ceil(minimum_distance)

            print(
                f"{map_path.name}: "
                f"{flight['origin']} -> {flight['destination']} "
                f"{current_distance} km -> {new_distance} km"
            )

            flight["distance"] = new_distance
            corrections += 1

    with map_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            map_data,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    print(
        f"{map_path.name}: "
        f"{corrections} distância(s) corrigida(s).\n"
    )
