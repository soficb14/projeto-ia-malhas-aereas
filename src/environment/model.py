import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error


def preprocess_and_train(df: pd.DataFrame):
    """
    Realiza o pré-processamento dos dados, faz a divisão de treino/teste,
    treina dois modelos de Machine Learning e avalia a performance de ambos.
    """
    # 1. Separar features (X) e variável alvo (y)
    X = df.drop(columns=["origin", "destination", "real_elapsed_time"])
    y = df["real_elapsed_time"]

    # Identificar colunas categóricas e numéricas
    categorical_features = ["aircraft_type", "weather_condition", "time_of_day"]
    numerical_features = [col for col in X.columns if col not in categorical_features]

    # 2. Configurar o pré-processamento (Pipeline de transformação)
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), categorical_features)
        ]
    )

    # 3. Divisão em dados de treino (80%) e teste (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Definir os modelos a comparar (exigência da Fase 2: pelo menos dois modelos)
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=50, random_state=42)
    }

    trained_pipelines = {}
    evaluation_results = {}

    print("--- Resultados da Avaliação dos Modelos (Fase 2) ---")
    
    for name, model in models.items():
        # Criar pipeline unindo o pré-processamento e o estimador de ML
        pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("model", model)
        ])

        # Treinar o modelo
        pipeline.fit(X_train, y_train)
        
        # Fazer previsões no conjunto de teste
        y_pred = pipeline.predict(X_test)

        # Avaliar métricas (MAE e RMSE)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        evaluation_results[name] = {"MAE": mae, "RMSE": rmse}
        trained_pipelines[name] = pipeline

        print(f"\nModelo: {name}")
        print(f"  - Erro Médio Absoluto (MAE): {mae:.2f} minutos")
        print(f"  - Raiz do Erro Quadrático Médio (RMSE): {rmse:.2f} minutos")

    print("-" * 50)
    
    # Retorna o melhor modelo treinado (por exemplo, com menor MAE) para futuras predições na busca A*
    best_model_name = min(evaluation_results, key=lambda k: evaluation_results[k]["MAE"])
    print(f"Melhor modelo selecionado para integração no A*: {best_model_name}")

    return trained_pipelines[best_model_name]