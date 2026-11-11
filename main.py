from src.environment.loader import load_network
from src.environment.dataset import generate_synthetic_flight_dataset
from src.environment.model import train_and_evaluate, build_cost_map, error_analysis
from src.search.astar import a_star_search
from src.search.heuristics import MAX_SPEED_KMH, check_heuristic


def route_str(result) -> str:
    if result is None:
        return "sem rota"
    return " -> ".join(a.code for a in result.path)


def main():
    print("=== FASE 2: CUSTO APRENDIDO + BUSCA ===")

    # 1. Malha aérea (Fase 1)
    print("\n[1/5] Carregando a malha aérea...")
    network = load_network("data/maps/mapa_medio.json", "data/maps/airports.json")
    print(f"-> {network.number_of_airports()} aeroportos, {network.number_of_flights()} voos")

    codes = sorted(network.airports)
    origin, destination = codes[0], codes[-1]
    print(f"-> Origem: {origin} | Destino: {destination}")

    # 2. Verificação da heurística (admissibilidade)
    print("\n[2/5] Verificando a heurística nos dados...")
    for metric in ("distance", "estimated_time"):
        bad = check_heuristic(network, metric)
        print(f"-> {metric}: {len(bad)} voos violam o limite inferior")

    # 3. Dataset sintético
    print("\n[3/5] Gerando o dataset sintético...")
    df = generate_synthetic_flight_dataset(network, samples_per_flight=20)
    print(f"-> {len(df)} linhas")

    # 4. Treino e comparação dos modelos
    print("\n[4/5] Treinando e comparando os modelos...")
    best_pipeline, results, holdout = train_and_evaluate(df)
    print(results.round(2))
    print("\nErro absoluto médio por condição:")
    for col, tabela in error_analysis(*holdout).items():
        print(f"\n{col}:\n{tabela}")

    # 5. Busca: o modelo muda a decisão?
    print("\n[5/5] Comparando rotas por distância e por tempo previsto...")
    bom = {"aircraft_type": "Narrow-body", "route_congestion_index": 1,
           "weather_condition": "Clear", "wind_component": 0.0,
           "time_of_day": "Off-peak"}
    ruim = {"aircraft_type": "Narrow-body", "route_congestion_index": 5,
            "weather_condition": "Storm", "wind_component": -20.0,
            "time_of_day": "Peak"}

    # 5a. Rota por distância
    base = a_star_search(network, origin, destination, metric="distance")
    print(f"\nPor distância: {route_str(base)}")
    if base:
        print(f"  custo {base.cost:.0f} km | nós expandidos: {base.expanded_nodes}")

    # 5b. Rota por tempo previsto em dois contextos globais
    for nome, ctx in (("Contexto bom (Clear/Off-peak)", bom),
                      ("Contexto ruim (Storm/Peak)", ruim)):
        network.set_learned_costs(
            build_cost_map(network, best_pipeline, ctx, max_speed_km_h=MAX_SPEED_KMH)
        )
        if nome.startswith("Contexto bom"):
            bad = check_heuristic(network, "predicted_time")
            print(f"\nHeurística em predicted_time: {len(bad)} violações")
        r = a_star_search(network, origin, destination, metric="predicted_time")
        print(f"\n{nome}: {route_str(r)}")
        if r:
            print(f"  custo {r.cost:.0f} min | nós expandidos: {r.expanded_nodes}")

    # 5c. Evento pontual: tempestade num único trecho da rota por distância
    if base and len(base.path) >= 3:
        trecho = (base.path[1].code, base.path[2].code)
        evento = {trecho: {"weather_condition": "Storm", "route_congestion_index": 5,
                           "time_of_day": "Peak", "wind_component": -25.0}}
        network.set_learned_costs(
            build_cost_map(network, best_pipeline, bom, overrides=evento,
                           max_speed_km_h=MAX_SPEED_KMH)
        )
        r = a_star_search(network, origin, destination, metric="predicted_time")
        print(f"\nTempestade só em {trecho[0]}->{trecho[1]}: {route_str(r)}")
        if r:
            print(f"  custo {r.cost:.0f} min")

    # 5d. Pares em que a rota por tempo difere da rota por distância (contexto bom)
    network.set_learned_costs(
        build_cost_map(network, best_pipeline, bom, max_speed_km_h=MAX_SPEED_KMH)
    )
    diferentes = []
    for o in codes:
        for d in codes:
            if o == d:
                continue
            a = a_star_search(network, o, d, metric="distance")
            b = a_star_search(network, o, d, metric="predicted_time")
            if a and b and route_str(a) != route_str(b):
                diferentes.append((o, d, route_str(a), route_str(b)))
    print(f"\nPares em que a rota muda: {len(diferentes)}")
    for item in diferentes[:5]:
        print(item)

    print("\n=== CONCLUÍDO ===")


if __name__ == "__main__":
    main()