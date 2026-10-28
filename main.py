from src.environment.loader import load_network
from src.environment.dataset import generate_synthetic_flight_dataset
from src.environment.model import preprocess_and_train

def main():
    print("=== A INICIAR TESTE DA FASE 2 ===")
    
    # 1. Carregar a malha aérea (Fase 1)
    print("\n[1/3] A carregar os dados geográficos e aeroportos...")
    try:
        network = load_network("data/maps/mapa_medio.json", "data/maps/airports.json")
        print("-> Malha aérea carregada com sucesso!")
    except Exception as e:
        print(f"-> Erro ao carregar a malha: {e}")
        return

    # 2. Gerar o dataset sintético (Fase 2 - Parte 1)
    print("\n[2/3] A gerar o dataset sintético de voos...")
    df_dataset = generate_synthetic_flight_dataset(network, samples_per_flight=5)
    print(f"-> Dataset gerado com sucesso! Total de linhas de treino: {len(df_dataset)}")
    print("Amostra dos dados criados:")
    print(df_dataset.head(3))

    # 3. Treinar e comparar os modelos (Fase 2 - Parte 2)
    print("\n[3/3] A treinar e a comparar os modelos (Regressão Linear vs Random Forest)...")
    best_model = preprocess_and_train(df_dataset)
    
    print("\n=== TESTE CONCLUÍDO COM SUCESSO! TUDO A FUNCIONAR PERFEITAMENTE ===")

if __name__ == "__main__":
    main()