import pandas as pd
import os

def get_garch_regime(symbol: str, date: str, forecast_file="C:/Users/ricke/Projects/garch-volatility-lab/logs/garch_forecast_log.csv") -> dict | None:
    """
    Return GARCH regime classification and forecast value for a symbol on a given date.

    Args:
        symbol (str): Symbol name (e.g. MES, MGC1)
        date (str): Date in YYYY-MM-DD format
        forecast_file (str): Path to garch_forecast_log.csv

    Returns:
        dict with forecast_vol, regime, and regime_score
        or None if no matching record is found
    """
    if not os.path.exists(forecast_file):
        print(f" Forecast file not found at: {forecast_file}")
        return None

    df = pd.read_csv(forecast_file)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    match = df[(df["symbol"] == symbol) & (df["date"] == date)]

    if match.empty:
        print(f" No GARCH forecast found for {symbol} on {date}")
        return None

    row = match.iloc[0]
    regime = row["regime"]
    score = {"LOW": +5, "NORMAL": 0, "HIGH": -10}.get(regime.upper(), 0)

    return {
        "forecast_vol": row["forecast_vol"],
        "regime": regime,
        "regime_score": score
    }
