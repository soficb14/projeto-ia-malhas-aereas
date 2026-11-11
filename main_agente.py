from src.environment.loader import load_network
from src.environment.dataset import generate_synthetic_flight_dataset
from src.environment.model import train_and_evaluate
from src.search.heuristics import check_heuristic
from src.agent.agent import FlightAgent
from src.agent.tools import FlightTools
from src.agent.backend_projeto import ProjetoBackend

# Premissa documentada: o usuário não informa a aeronave. Narrow-body é o perfil
# neutro do dataset (multiplicadores 1.0 em clima, vento e velocidade).
AIRCRAFT_PADRAO = "Narrow-body"


def main():
    # Fase 1: a malha
    network = load_network("data/maps/mapa_medio.json", "data/maps/airports.json")
    print("Aeroportos:", sorted(network.airports))

    # Fase 2: dataset + treino
    df = generate_synthetic_flight_dataset(network, samples_per_flight=20)
    pipeline, results, _ = train_and_evaluate(df)
    print(results.round(2))

    # Confere a admissibilidade com os custos do modelo (contexto neutro)
    backend = ProjetoBackend(network, pipeline, aircraft_type=AIRCRAFT_PADRAO)
    custos, _ = backend._custos({"horario": "Off-peak", "clima": "Clear", "vento": 0,
                                 "congestionamento": 1, "eventos": []})
    network.set_learned_costs(custos)
    print("Violações da heurística em predicted_time:",
          len(check_heuristic(network, "predicted_time")))

    # Fase 3: o LLM usa o backend como ferramenta
    agente = FlightAgent(FlightTools(backend))

    print("\nAgente de rotas. Digite 'sair' para encerrar.")
    while True:
        pedido = input("\nVocê: ").strip()
        if pedido.lower() in {"sair", "exit", "q"}:
            break
        r = agente.run(pedido)
        print("\nAgente:", r["resposta"] or r["erro"])
        print(f"[{r['latencia_s']}s | {r['tokens_in']}+{r['tokens_out']} tokens | "
              f"ferramentas: {[c['nome'] for c in r['chamadas']]}]")


if __name__ == "__main__":
    main()