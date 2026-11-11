import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold, KFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERICAL = ["distance", "route_congestion_index", "wind_component"]
CATEGORICAL = ["aircraft_type", "weather_condition", "time_of_day"]
FEATURES = NUMERICAL + CATEGORICAL
TARGET = "real_elapsed_time"


def build_preprocessor() -> ColumnTransformer:
    num = Pipeline([("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler())])
    cat = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    return ColumnTransformer([("num", num, NUMERICAL), ("cat", cat, CATEGORICAL)])


def train_and_evaluate(df: pd.DataFrame, seed: int = 42, n_splits: int = 5,
                       group_by_route: bool = False):
    X, y = df[FEATURES], df[TARGET]
    groups = df["origin"] + "-" + df["destination"]

    X_tr, X_te, y_tr, y_te, g_tr, _ = train_test_split(
        X, y, groups, test_size=0.2, random_state=seed)

    cv = GroupKFold(n_splits=n_splits) if group_by_route \
        else KFold(n_splits=n_splits, shuffle=True, random_state=seed)

    models = {
        "Baseline (média)": DummyRegressor(strategy="mean"),
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=seed),
    }

    rows, pipelines = [], {}
    for name, model in models.items():
        pipe = Pipeline([("prep", build_preprocessor()), ("model", model)])
        cv_res = cross_validate(
            pipe, X_tr, y_tr, cv=cv, groups=g_tr if group_by_route else None,
            scoring={"mae": "neg_mean_absolute_error",
                     "rmse": "neg_root_mean_squared_error"})
        pipe.fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        rows.append({
            "modelo": name,
            "cv_mae": -cv_res["test_mae"].mean(),
            "cv_mae_std": cv_res["test_mae"].std(),
            "cv_rmse": -cv_res["test_rmse"].mean(),
            "teste_mae": mean_absolute_error(y_te, pred),
            "teste_rmse": np.sqrt(mean_squared_error(y_te, pred)),
        })
        pipelines[name] = pipe

    results = pd.DataFrame(rows).set_index("modelo")
    best = results.drop(index="Baseline (média)")["cv_mae"].idxmin()
    return pipelines[best], results, (X_te, y_te, pipelines[best].predict(X_te))


def error_analysis(X_te, y_te, y_pred) -> dict:
    d = X_te.copy()
    d["erro_abs"] = (y_te - y_pred).abs()
    cols = ["weather_condition", "time_of_day", "aircraft_type", "route_congestion_index"]
    return {c: d.groupby(c)["erro_abs"].mean().round(2) for c in cols}


def predict_time(pipeline, distance, aircraft_type, congestion,
                 weather, wind, time_of_day) -> float:
    row = pd.DataFrame([{
        "distance": distance, "aircraft_type": aircraft_type,
        "route_congestion_index": congestion, "weather_condition": weather,
        "wind_component": wind, "time_of_day": time_of_day}])
    return max(float(pipeline.predict(row)[0]), 1.0)

def build_cost_map(network, pipeline, context: dict,
                   overrides: dict | None = None,
                   max_speed_km_h: float = 900.0) -> dict:
    """
    context: {"aircraft_type", "route_congestion_index", "weather_condition",
              "wind_component", "time_of_day"}
    overrides: {(origem, destino): {campo: valor}}, para eventos pontuais
               (tempestade num trecho, congestionamento extremo etc.)
    """
    rows, keys, floors = [], [], []

    for flights in network.flights.values():
        for f in flights:
            key = (f.origin.code, f.destination.code)
            ctx = {**context, **(overrides or {}).get(key, {})}
            rows.append({"distance": f.distance, **ctx})
            keys.append(key)
            floors.append(f.distance / max_speed_km_h * 60)  # minutos

    
        preds = pipeline.predict(pd.DataFrame(rows)[FEATURES])
    return {k: max(float(p), fl) for k, p, fl in zip(keys, preds, floors)}