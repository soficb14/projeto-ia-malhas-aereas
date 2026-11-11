import random
from dataclasses import dataclass, asdict

import pandas as pd

from .graph import AirNetwork


@dataclass
class FlightDatasetRow:
    """
    Uma observação de voo (Fase 2). weather_condition e wind_component
    podem ser NaN, simulando falhas de coleta.
    """
    origin: str
    destination: str
    distance: float
    aircraft_type: str           # "Turboprop", "Narrow-body", "Wide-body"
    route_congestion_index: int  # 1 a 5
    weather_condition: str | float   # "Clear", "Rain", "Snow", "Storm" (ou NaN)
    wind_component: float            # nós; + cauda, - proa (ou NaN)
    time_of_day: str                 # "Peak" ou "Off-peak"
    real_elapsed_time: float         # alvo (Y), em minutos


# Perfil de cada aeronave: multiplicadores sobre clima, vento e tempo base
AIRCRAFT_PROFILE = {
    "Turboprop":   {"weather": 1.5, "wind": 1.6, "speed": 1.15},
    "Narrow-body": {"weather": 1.0, "wind": 1.0, "speed": 1.00},
    "Wide-body":   {"weather": 0.7, "wind": 0.6, "speed": 0.95},
}
WEATHER_PENALTIES = {"Clear": 0.0, "Rain": 15.0, "Snow": 35.0, "Storm": 60.0}
TIME_PERIODS = ["Peak", "Off-peak"]


def generate_synthetic_flight_dataset(
    network: AirNetwork,
    samples_per_flight: int = 20,
    seed: int = 42,
    missing_rate: float = 0.03,
) -> pd.DataFrame:
    """
    Gera o dataset sintético de observações para todos os voos da malha.

    :param missing_rate: fração de valores apagados em weather_condition e
                         wind_component (0 desliga os faltantes).
    """
    rng = random.Random(seed)
    nan = float("nan")
    aircraft_types = list(AIRCRAFT_PROFILE)
    weathers = list(WEATHER_PENALTIES)
    rows = []

    for flight_list in network.flights.values():
        for flight in flight_list:
            base_time = flight.estimated_time

            for _ in range(samples_per_flight):
                aircraft = rng.choice(aircraft_types)
                profile = AIRCRAFT_PROFILE[aircraft]
                congestion = rng.randint(1, 5)
                weather = rng.choice(weathers)
                wind = round(rng.uniform(-25.0, 25.0), 1)
                time_day = rng.choice(TIME_PERIODS)
                peak = time_day == "Peak"

                # --- tempo real (alvo), calculado com os valores VERDADEIROS ---
                weather_delay = WEATHER_PENALTIES[weather] * profile["weather"]
                congestion_delay = congestion * 4.0 * (1.5 if peak else 1.0)
                peak_delay = 20.0 if peak else 0.0
                storm_peak_delay = 15.0 if (weather == "Storm" and peak) else 0.0
                wind_impact = -0.4 * wind * profile["wind"] * (base_time / 120.0)
                noise_sd = 3.0 + (6.0 if weather in ("Storm", "Snow") else 0.0)
                noise = rng.gauss(0, noise_sd)

                real_time = (
                    base_time * profile["speed"]
                    + weather_delay + congestion_delay + peak_delay
                    + storm_peak_delay + wind_impact + noise
                )
                real_time = max(real_time, base_time * 0.75)  # limite físico

                # --- falhas de coleta: apaga DEPOIS de calcular o alvo ---
                observed_weather = nan if rng.random() < missing_rate else weather
                observed_wind = nan if rng.random() < missing_rate else wind

                row = FlightDatasetRow(
                    origin=flight.origin.code,
                    destination=flight.destination.code,
                    distance=flight.distance,
                    aircraft_type=aircraft,
                    route_congestion_index=congestion,
                    weather_condition=observed_weather,
                    wind_component=observed_wind,
                    time_of_day=time_day,
                    real_elapsed_time=round(real_time, 2),
                )
                rows.append(asdict(row))

    return pd.DataFrame(rows)