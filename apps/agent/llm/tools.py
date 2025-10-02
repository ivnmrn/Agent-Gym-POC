import os

import pandas as pd
import requests
from langchain.tools import tool

API_BASE = os.getenv("STATS_API_BASE_URL", "http://api:8000")


class Tools:
    """Collection of tools for the agent."""

    @staticmethod
    def list_tools():
        return [fetch_stats, compute_kpis, compute_conclusions]


@tool("fetch_stats")
def fetch_stats(user_id: str, start: str, end: str) -> list:
    """
    NAME: fetch_stats
    PURPOSE: Get raw training rows from the Statistics API for the given user and date range.

    WHEN TO USE:
      - First step when you need data. Call this BEFORE computing KPIs.
      - If you don't have `rows` yet or you suspect they are outdated.

    INPUTS:
      - user_id (str): user identifier.
      - start (str): inclusive ISO date 'YYYY-MM-DD'.
      - end   (str): inclusive ISO date 'YYYY-MM-DD'.

    RETURNS:
      - List[Row]: each row has {date, exercise, muscle_group, weight, reps, set, rpe, rir, ...}

    EXAMPLE CALL:
      fetch_stats({"user_id":"123","start":"2025-09-01","end":"2025-09-25"})
    """

    url = f"{API_BASE}/api/v1/statistics/{user_id}/stats"
    headers = {
        "accept": "application/json",
        "X-User": user_id,
    }

    params = {
        "start": start,
        "end": end,
    }

    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()


@tool("compute_kpis")
def compute_kpis(rows: list) -> dict:
    """
    NAME: compute_conclusions
    PURPOSE: Turn KPIs into actionable advice given the user's goal.

    PRECONDITION:
      - Must be called ONLY IF `kpis` is already available (output of compute_kpis).

    INPUTS:
      - kpis (dict): result from compute_kpis
      - goal (str): e.g., "fuerza", "hipertrofia", etc.

    RETURNS:
      - { advice: str }

    EXAMPLE CALL:
      compute_conclusions({"kpis":{...}, "goal":"fuerza"})
    """
    df = pd.DataFrame(rows)
    if df.empty:
        return {"summary": "sin datos", "by_muscle": [], "alerts": []}

    for col in ("weight", "reps", "set", "rpe", "rir"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["volume"] = df.get("weight", 0) * df.get("reps", 0)

    by_muscle = (
        df.groupby("muscle_group")
        .agg(
            kg=("volume", "sum"),
            series=("set", "sum"),
            reps=("reps", "sum"),
            rpe_mean=("rpe", "mean"),
            rir_mean=("rir", "mean"),
        )
        .reset_index()
        .sort_values("kg", ascending=False)
    )

    # Compute ACWR (Acute:Chronic Workload Ratio)
    df["date"] = pd.to_datetime(df["date"])
    daily = df.groupby(["date", "muscle_group"])["volume"].sum().reset_index()
    w7 = (
        daily.set_index("date")
        .groupby("muscle_group")["volume"]
        .rolling("7D")
        .sum()
        .reset_index()
        .rename(columns={"volume": "v7"})
    )
    w28 = (
        daily.set_index("date")
        .groupby("muscle_group")["volume"]
        .rolling("28D")
        .sum()
        .reset_index()
        .rename(columns={"volume": "v28"})
    )
    trend = w7.merge(w28, on=["date", "muscle_group"], how="left")
    trend["acwr"] = (trend["v7"] / trend["v28"]).fillna(0.0)

    alerts = []
    for _, row in trend.dropna().iterrows():
        if row["acwr"] > 1.5:
            alerts.append(
                {
                    "date": str(row["date"].date()),
                    "muscle_group": row["muscle_group"],
                    "acwr": round(float(row["acwr"]), 2),
                    "msg": "ACWR>1.5 (salto de volumen)",
                }
            )

    return {
        "summary": "ok",
        "by_muscle": by_muscle.to_dict(orient="records"),
        "alerts": alerts[-10:],
    }


@tool("compute_conclusions")
def compute_conclusions(kpis: dict, goal: str) -> dict:
    """
    NAME: compute_conclusions
    PURPOSE: Turn KPIs into actionable advice given the user's goal.

    PRECONDITION:
      - Must be called ONLY IF `kpis` is already available (output of compute_kpis).

    INPUTS:
      - kpis (dict): result from compute_kpis
      - goal (str): e.g., "fuerza", "hipertrofia", etc.

    RETURNS:
      - { advice: str }

    EXAMPLE CALL:
      compute_conclusions({"kpis":{...}, "goal":"fuerza"})
    """
    advice = []
    if not kpis or kpis.get("summary") == "sin datos":
        return {"advice": "No hay datos disponibles para el periodo."}

    if goal and "fuerza" in goal.lower():
        top_muscles = sorted(kpis["by_muscle"], key=lambda x: x["kg"], reverse=True)[:3]
        advice.append("Para fuerza, enfócate en los músculos con mayor volumen:")
        for m in top_muscles:
            advice.append(f"- {m['muscle_group']}: {m['kg']} kg en {m['series']} series.")

    for alert in kpis.get("alerts", []):
        advice.append(
            f"Alerta el {alert['date']} en {alert['muscle_group']}: {alert['msg']} (ACWR={alert['acwr']})"
        )

    if not advice:
        advice.append("Todo parece normal. Mantén tu rutina actual.")

    return {"advice": "\n".join(advice)}
