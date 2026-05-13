"""
credit_agent/agent/data_ingestion.py
Reads invoice CSV, validates fields, identifies overdue records.
"""

import pandas as pd
from pathlib import Path


REQUIRED_COLUMNS = [
    "invoice_no", "client_name", "client_email", "amount",
    "currency", "due_date", "days_overdue", "follow_up_count",
    "payment_link", "contact_person", "assigned_manager"
]


def load_invoices(filepath: str) -> pd.DataFrame:
    """Load and validate invoice CSV. Returns cleaned DataFrame."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Invoice file not found: {filepath}")

    df = pd.read_csv(filepath)

    # Validate required columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Clean and type-cast
    df["days_overdue"] = pd.to_numeric(df["days_overdue"], errors="coerce").fillna(0).astype(int)
    df["follow_up_count"] = pd.to_numeric(df["follow_up_count"], errors="coerce").fillna(0).astype(int)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    return df


def get_overdue_records(df: pd.DataFrame) -> pd.DataFrame:
    """Filter records that are overdue (days_overdue > 0)."""
    return df[df["days_overdue"] > 0].copy()


def get_summary_stats(df: pd.DataFrame) -> dict:
    """Return summary counts for the dashboard."""
    from agent.email_generator import get_stage

    overdue = get_overdue_records(df)

    stage_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for _, row in overdue.iterrows():
        s = get_stage(int(row["days_overdue"]), int(row["follow_up_count"]))
        stage_counts[s] = stage_counts.get(s, 0) + 1

    return {
        "total_invoices": len(df),
        "overdue_count": len(overdue),
        "current_count": len(df) - len(overdue),
        "total_overdue_amount": overdue["amount"].sum(),
        "stage_1_count": stage_counts[1],
        "stage_2_count": stage_counts[2],
        "stage_3_count": stage_counts[3],
        "stage_4_count": stage_counts[4],
        "legal_escalation_count": stage_counts[5],
    }
