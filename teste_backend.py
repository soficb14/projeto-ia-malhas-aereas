from src.environment.loader import load_network
from src.environment.dataset import generate_synthetic_flight_dataset
from src.environment.model import train_and_evaluate
from src.agent.backend_projeto import ProjetoBackend
from src.agent.tools import FlightTools

network = load_network("data/maps/mapa_medio.json", "data/maps/airports.json")
df = generate_synthetic_flight_dataset(network, samples_per_flight=20)
pipeline, _, _ = train_and_evaluate(df)

tools = FlightTools(ProjetoBackend(network, pipeline, aircraft_type="Narrow-body"))

codes = sorted(network.airports)
o, d = codes[0], codes[-1]
print("Aeroportos:", codes)

print("\n1) Rota normal:")
print(tools.buscar_rota(o, d))

print("\n2) Com tempestade, pico e vento de proa:")
print(tools.buscar_rota(o, d, clima="Storm", horario="Peak", vento=-20, congestionamento=5))

print("\n3) Aeroporto inexistente (deve dar ok=False):")
print(tools.buscar_rota(o, "XYZ"))

print("\n4) Tempestade só no trecho DEN-ORD (a rota deve mudar):")
r4 = tools.buscar_rota("ABQ", "STL", eventos=[{"de": "DEN", "para": "ORD", "tipo": "Storm"}])
print(r4["rota"], r4["tempo_previsto_min"], "| economia:", r4["economia_min"])

print("\n5) Trecho DEN-ORD fechado:")
r5 = tools.buscar_rota("ABQ", "STL", eventos=[{"de": "DEN", "para": "ORD", "tipo": "Closure"}])
print(r5.get("rota") or r5)

print("\n6) Evitando ORD:")
r6 = tools.buscar_rota("ABQ", "STL", evitar=["ORD"])
print(r6.get("rota") or r6)

print("\n7) Sentido inverso (LAX -> CLT) e vizinhos de LAX:")
print(tools.buscar_rota("LAX", "CLT").get("rota"))
print([a.code for a in network.get_neighbors("LAX")])