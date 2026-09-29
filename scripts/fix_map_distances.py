import json
import math
import sys
from pathlib import Path


# Permite importar o código do projeto quando o script é executado
# diretamente com: python3 scripts/fix_map_distances.py
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.environment.loader import load_network
from src.search.heuristics import straight_line_distance


MAPS_DIR = BASE_DIR / "data" / "maps"

MAP_FILES = [
    MAPS_DIR / "mapa_pequeno.json",
    MAPS_DIR / "mapa_medio.json",
    MAPS_DIR / "mapa_grande.json",
]

SAFETY_MARGIN_KM = 5.0


def find_airports_path():
    """
    Descobre automaticamente o arquivo de aeroportos utilizado
    pelo projeto, sem assumir um nome específico.
    """

    candidates = []

    for path in BASE_DIR.rglob("*.json"):
        if path in MAP_FILES:
            continue

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            continue

        airports = data.get("airports")

        if not isinstance(airports, list):
            continue

        if not airports:
            continue

        # O arquivo de aeroportos do projeto contém objetos
        # com código e coordenadas.
        first = airports[0]

        if (
            isinstance(first, dict)
            and "code" in first
            and "latitude" in first
            and "longitude" in first
        ):
            candidates.append(path)

    if len(candidates) == 1:
        return candidates[0]

    if not candidates:
        raise FileNotFoundError(
            "Não foi possível localizar automaticamente "
            "o arquivo de aeroportos."
        )

    raise RuntimeError(
        "Foram encontrados vários arquivos possíveis de aeroportos:\n"
        + "\n".join(str(path) for path in candidates)
    )


def fix_map(map_path, airports_path):
    """
    Corrige apenas voos cuja distância cadastrada seja menor
    que a distância em linha reta calculada pela heurística.
    """

    network = load_network(
        str(map_path),
        str(airports_path),
    )

    with map_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    corrections = []

    for flight in data["flights"]:
        origin = network.get_airport(flight["origin"])
        destination = network.get_airport(flight["destination"])

        straight_line = straight_line_distance(
            origin,
            destination,
        )

        current_distance = float(flight["distance"])

        if current_distance < straight_line:
            new_distance = math.ceil(
                straight_line + SAFETY_MARGIN_KM
            )

            corrections.append(
                {
                    "origin": origin.code,
                    "destination": destination.code,
                    "old": current_distance,
                    "straight_line": straight_line,
                    "new": new_distance,
                }
            )

            flight["distance"] = new_distance

    with map_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    return corrections


def main():
    airports_path = find_airports_path()

    print("=" * 80)
    print("CORREÇÃO DAS DISTÂNCIAS DOS MAPAS")
    print("=" * 80)
    print(f"\nArquivo de aeroportos encontrado:")
    print(f"  {airports_path}")

    total_corrections = 0

    for map_path in MAP_FILES:
        print(f"\n{'-' * 80}")
        print(f"Mapa: {map_path.name}")

        corrections = fix_map(
            map_path,
            airports_path,
        )

        if not corrections:
            print("Nenhuma correção necessária.")
            continue

        for correction in corrections:
            print(
                f"{correction['origin']} -> "
                f"{correction['destination']}: "
                f"{correction['old']:.2f} km -> "
                f"{correction['new']} km "
                f"(linha reta: "
                f"{correction['straight_line']:.2f} km)"
            )

        print(
            f"Correções realizadas: {len(corrections)}"
        )

        total_corrections += len(corrections)

    print(f"\n{'=' * 80}")
    print(
        f"TOTAL DE CORREÇÕES: {total_corrections}"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()