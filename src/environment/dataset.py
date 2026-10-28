import random
from dataclasses import dataclass, asdict
import pandas as pd

from .graph import AirNetwork
from .flight import Flight


@dataclass
class FlightDatasetRow:
    """
    Representa uma amostra/observação de um voo no mundo real com variáveis
    ambientais e operacionais para a Fase 2.
    """
    origin: str
    destination: str
    distance: float
    aircraft_type: str           # Ex: "Turboprop", "Narrow-body", "Wide-body"
    route_congestion_index: int  # Congestionamento do corredor aéreo (1 a 5)
    weather_condition: str       # Ex: "Clear", "Rain", "Snow", "Storm"
    wind_component: float        # Vento em nós (-25 a +25)
    time_of_day: str             # Ex: "Peak" (pico) ou "Off-peak" (fora de pico)
    real_elapsed_time: float     # Variável Alvo (Y) - Tempo real observado em minutos


def generate_synthetic_flight_dataset(
    network: AirNetwork, 
    samples_per_flight: int = 20, 
    seed: int = 42
) -> pd.DataFrame:
    """
    Gera um DataFrame sintético do Pandas contendo dados de observação
    para todos os voos cadastrados na malha aérea (AirNetwork).
    
    :param network: Instância da malha aérea (AirNetwork).
    :param samples_per_flight: Quantidade de observações/amostras por trecho de voo.
    :param seed: Semente aleatória para reprodutibilidade dos experimentos.
    :return: pandas.DataFrame com as colunas de características e a variável alvo real_elapsed_time.
    """
    random.seed(seed)
    
    aircraft_types = ["Turboprop", "Narrow-body", "Wide-body"]
    weather_conditions = ["Clear", "Rain", "Snow", "Storm"]
    time_periods = ["Peak", "Off-peak"]

    weather_penalties = {
        "Clear": 0.0,
        "Rain": 15.0,
        "Snow": 35.0,
        "Storm": 60.0
    }

    dataset_rows = []

    # Iterar por todos os voos existentes na malha
    for origin_code, flight_list in network.flights.items():
        for flight in flight_list:
            distance = flight.distance
            
            # Aproveita o cálculo base de tempo teórico que já tinhas no projeto
            base_time = flight.estimated_time

            for _ in range(samples_per_flight):
                aircraft = random.choice(aircraft_types)
                congestion = random.randint(1, 5)
                weather = random.choice(weather_conditions)
                wind = random.uniform(-25.0, 25.0)  # Vento positivo = cauda, negativo = proa
                time_day = random.choice(time_periods)

                # Cálculo sintético do tempo real (variável alvo Y) com base nos obstáculos
                weather_delay = weather_penalties[weather]
                congestion_delay = congestion * 4.0
                peak_delay = 20.0 if time_day == "Peak" else 0.0
                wind_impact = -0.4 * wind  
                random_noise = random.gauss(0, 5.0)

                real_time = base_time + weather_delay + congestion_delay + peak_delay + wind_impact + random_noise
                real_time = max(real_time, base_time * 0.75)  # Limite físico mínimo

                row = FlightDatasetRow(
                    origin=flight.origin.code,
                    destination=flight.destination.code,
                    distance=distance,
                    aircraft_type=aircraft,
                    route_congestion_index=congestion,
                    weather_condition=weather,
                    wind_component=round(wind, 1),
                    time_of_day=time_day,
                    real_elapsed_time=round(real_time, 2)
                )
                dataset_rows.append(asdict(row))

    return pd.DataFrame(dataset_rows)