import math

import pytest

from src.environment.dataset import generate_synthetic_flight_dataset
from src.environment.loader import load_network
from src.environment.model import build_cost_map, train_and_evaluate
from src.search.astar import a_star_search
from src.search.heuristics import MAX_SPEED_KMH, check_heuristic, time_lower_bound

MAPA = "data/maps/mapa_medio.json"
AEROPORTOS = "data/maps/airports.json"


@pytest.fixture(scope="module")
def network():
    return load_network(MAPA, AEROPORTOS)


@pytest.fixture(scope="module")
def treinado(network):
    df = generate_synthetic_flight_dataset(network, samples_per_flight=20)
    pipeline, results, _ = train_and_evaluate(df)
    return pipeline, results


def test_heuristica_admissivel_nos_dados(network):
    assert check_heuristic(network, "distance") == []
    assert check_heuristic(network, "estimated_time") == []


def test_dataset_tem_faltantes_e_alvo_completo(network):
    df = generate_synthetic_flight_dataset(network, samples_per_flight=20)
    assert df["wind_component"].isna().any()
    assert df["weather_condition"].isna().any()
    assert not df["real_elapsed_time"].isna().any()


def test_dataset_reprodutivel(network):
    a = generate_synthetic_flight_dataset(network, seed=7)
    b = generate_synthetic_flight_dataset(network, seed=7)
    assert a.equals(b)


def test_predicted_time_sem_custo_aprendido_levanta_erro(network):
    network.clear_learned_costs()
    flight = next(iter(network.flights.values()))[0]
    with pytest.raises(ValueError):
        network.get_flight_cost(flight, "predicted_time")


def test_modelos_batem_o_baseline(treinado):
    _, results = treinado
    baseline = results.loc["Baseline (média)", "cv_mae"]
    assert results.loc["Linear Regression", "cv_mae"] < baseline
    assert results.loc["Random Forest", "cv_mae"] < baseline


def test_astar_com_custo_aprendido_devolve_rota_valida(network, treinado):
    pipeline, _ = treinado
    ctx = {"aircraft_type": "Narrow-body", "route_congestion_index": 3,
           "weather_condition": "Clear", "wind_component": 0.0,
           "time_of_day": "Peak"}
    costs = build_cost_map(network, pipeline, ctx, max_speed_km_h=MAX_SPEED_KMH)
    network.set_learned_costs(costs)

    # nenhum custo previsto pode ficar abaixo do limite inferior da heurística
    for flights in network.flights.values():
        for f in flights:
            assert costs[(f.origin.code, f.destination.code)] >= \
                time_lower_bound(f.origin, f.destination) - 1e-6

    codes = sorted(network.airports)
    result = a_star_search(network, codes[0], codes[-1], metric="predicted_time")
    assert result is not None
    assert result.path[0].code == codes[0]
    assert result.path[-1].code == codes[-1]
    assert result.cost > 0 and not math.isnan(result.cost)
    for a, b in zip(result.path, result.path[1:]):   # cada passo é um voo real
        assert any(f.destination.code == b.code
                   for f in network.get_outgoing_flights(a.code))
    network.clear_learned_costs()