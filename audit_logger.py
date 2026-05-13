"""
credit_agent/agent/audit_logger.py
Logs every generated email with full metadata for audit trail.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
AUDIT_CSV = LOG_DIR / "audit_log.csv"
AUDIT_JSON = LOG_DIR / "audit_log.json"

CSV_HEADERS = [
    "timestamp", "invoice_no", "client_name", "client_email",
    "amount", "currency", "due_date", "days_overdue",
    "stage", "tone_used", "subject", "send_status",
    "dry_run", "assigned_manager", "error"
]


def ensure_log_dir():
    LOG_DIR.mkdir(exist_ok=True)


def log_email(result: dict):
    """Append a result dict to both CSV and JSON audit logs."""
    ensure_log_dir()

    # ── CSV append ──
    file_exists = AUDIT_CSV.exists()
    with open(AUDIT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)

    # ── JSON append ──
    records = []
    if AUDIT_JSON.exists():
        try:
            with open(AUDIT_JSON, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []
    records.append(result)
    with open(AUDIT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def load_audit_log() -> list:
    """Load full audit log as list of dicts."""
    if not AUDIT_JSON.exists():
        return []
    try:
        with open(AUDIT_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def clear_audit_log():
    """Clear both log files (for fresh runs)."""
    if AUDIT_CSV.exists():
        AUDIT_CSV.unlink()
    if AUDIT_JSON.exists():
        AUDIT_JSON.unlink()
