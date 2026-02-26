"""
scoring_engine.py
-----------------
Core scoring logic for the Employee of the Month system.
Handles weighted scoring, eligibility checks, tie-breaking,
and winner history tracking.
"""

import pandas as pd
import json
import os
from datetime import datetime

# ------------------------------------------------------------
# DEFAULT WEIGHTS (must sum to 1.0)
# HR rationale:
#   - Performance score: primary KPI attainment metric
#   - Peer nominations: reflects collaboration & culture fit
#   - Attendance: reliability & commitment indicator
#   - Manager rating: direct supervisor assessment
# ------------------------------------------------------------
DEFAULT_WEIGHTS = {
    "performance_score": 0.40,
    "peer_nominations":  0.30,
    "attendance_pct":    0.20,
    "manager_rating":    0.10,
}

# Columns required in uploaded data
REQUIRED_COLUMNS = [
    "employee_id", "name", "department",
    "performance_score", "peer_nominations",
    "attendance_pct", "manager_rating",
    "months_employed", "email"
]

# Minimum months employed to be eligible
MIN_MONTHS_EMPLOYED = 6

# Path to persist winner history
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "data", "winner_history.json")


# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

def validate_dataframe(df: pd.DataFrame) -> tuple[bool, str]:
    """Check uploaded data has required columns and valid ranges."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return False, f"Missing columns: {', '.join(missing)}"

    # Range checks
    checks = {
        "performance_score": (0, 100),
        "attendance_pct":    (0, 100),
        "manager_rating":    (0, 10),
        "peer_nominations":  (0, 999),
        "months_employed":   (0, 999),
    }
    for col, (lo, hi) in checks.items():
        if not df[col].between(lo, hi).all():
            return False, f"'{col}' contains values outside expected range ({lo}–{hi})."

    return True, "OK"


# ------------------------------------------------------------
# NORMALISATION
# Converts each raw metric to a 0–100 scale before weighting
# so that metrics with different units are fairly compared.
# ------------------------------------------------------------

def normalise(series: pd.Series) -> pd.Series:
    """Min-max normalise a series to 0–100."""
    min_val, max_val = series.min(), series.max()
    if max_val == min_val:
        return pd.Series([100.0] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val) * 100


# ------------------------------------------------------------
# ELIGIBILITY FILTER
# Employees excluded from winning:
#   1. Less than MIN_MONTHS_EMPLOYED tenure
#   2. Won in the immediately preceding month
# ------------------------------------------------------------

def get_last_winner_id() -> str | None:
    """Return the employee_id of last month's winner, or None."""
    history = load_history()
    if not history:
        return None
    last = sorted(history, key=lambda x: x["date"])[-1]
    return last["employee_id"]


def apply_eligibility(df: pd.DataFrame) -> pd.DataFrame:
    """Return only eligible employees with an 'eligible' flag column."""
    df = df.copy()
    last_winner = get_last_winner_id()

    df["eligible"] = True
    df["ineligibility_reason"] = ""

    # Tenure check
    tenure_mask = df["months_employed"] < MIN_MONTHS_EMPLOYED
    df.loc[tenure_mask, "eligible"] = False
    df.loc[tenure_mask, "ineligibility_reason"] = f"Tenure < {MIN_MONTHS_EMPLOYED} months"

    # Back-to-back win prevention
    if last_winner:
        repeat_mask = df["employee_id"] == last_winner
        df.loc[repeat_mask, "eligible"] = False
        df.loc[repeat_mask, "ineligibility_reason"] = "Won last month"

    return df


# ------------------------------------------------------------
# SCORING
# ------------------------------------------------------------

def calculate_scores(df: pd.DataFrame, weights: dict = None) -> pd.DataFrame:
    """
    Normalise each metric, apply weights, compute composite score.
    Returns the full dataframe with score columns added.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    df = df.copy()
    score_cols = list(weights.keys())

    # Normalise each metric
    for col in score_cols:
        df[f"{col}_norm"] = normalise(df[col])

    # Weighted composite score
    df["composite_score"] = sum(
        df[f"{col}_norm"] * w for col, w in weights.items()
    ).round(2)

    # Rank all employees (1 = highest)
    df["rank"] = df["composite_score"].rank(ascending=False, method="min").astype(int)

    return df


# ------------------------------------------------------------
# WINNER SELECTION
# ------------------------------------------------------------

def select_winner(df: pd.DataFrame, weights: dict = None) -> tuple[pd.Series | None, pd.DataFrame]:
    """
    Full pipeline: validate → eligibility → score → select winner.
    Returns (winner_row, scored_dataframe).
    Winner is None if no eligible employees exist.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    df = apply_eligibility(df)
    df = calculate_scores(df, weights)

    eligible = df[df["eligible"]].copy()

    if eligible.empty:
        return None, df

    # Winner = highest composite score among eligible employees
    winner_idx = eligible["composite_score"].idxmax()
    winner = df.loc[winner_idx]

    return winner, df


# ------------------------------------------------------------
# HISTORY PERSISTENCE
# ------------------------------------------------------------

def load_history() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_winner(winner: pd.Series, month: str = None):
    """Persist winner to history JSON file."""
    history = load_history()
    if month is None:
        month = datetime.now().strftime("%B %Y")

    entry = {
        "date": datetime.now().isoformat(),
        "month": month,
        "employee_id": str(winner["employee_id"]),
        "name": str(winner["name"]),
        "department": str(winner["department"]),
        "composite_score": float(winner["composite_score"]),
        "email": str(winner["email"]),
    }
    history.append(entry)

    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_history_df() -> pd.DataFrame:
    history = load_history()
    if not history:
        return pd.DataFrame(columns=["month", "name", "department", "composite_score"])
    return pd.DataFrame(history)
