from src.environment.loader import load_network
from src.environment.dataset import generate_synthetic_flight_dataset
from src.environment.model import train_and_evaluate
from src.agent.backend_projeto import ProjetoBackend
from src.agent.tools import FlightTools
from src.agent.pedidos_teste import PEDIDOS

network = load_network("data/maps/mapa_medio.json", "data/maps/airports.json")
df = generate_synthetic_flight_dataset(network, samples_per_flight=20)
pipeline, _, _ = train_and_evaluate(df)
tools = FlightTools(ProjetoBackend(network, pipeline, aircraft_type="Narrow-body"))

for p in PEDIDOS:
    if p["ferramenta"] != "buscar_rota":
        continue
    r = tools.buscar_rota(**p["args"])
    print(f"#{p['id']:>2} {p['cat']:<12}", "OK " if r["ok"] else "SEM ROTA",
          r.get("rota") or r.get("erro"))