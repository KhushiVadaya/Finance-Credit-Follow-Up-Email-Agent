"""
credit_agent/agent/orchestrator.py
Main agent pipeline: load → identify overdue → generate emails → log.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.data_ingestion import load_invoices, get_overdue_records
from agent.email_generator import generate_email, get_stage, ESCALATION_STAGES
from agent.audit_logger import log_email, clear_audit_log, load_audit_log


def run_agent(csv_path: str, dry_run: bool = True, clear_logs: bool = False) -> list:
    """
    Full agent run.
    Returns list of result dicts (one per overdue invoice).
    """
    if clear_logs:
        clear_audit_log()

    print(f"\n{'='*60}")
    print(f"  Finance Credit Follow-Up Email Agent")
    print(f"  Mode: {'DRY RUN (no emails sent)' if dry_run else 'LIVE SEND'}")
    print(f"{'='*60}\n")

    df = load_invoices(csv_path)
    overdue = get_overdue_records(df)

    print(f"  Loaded {len(df)} invoices | {len(overdue)} overdue records found\n")

    results = []
    for _, row in overdue.iterrows():
        invoice = row.to_dict()
        days = int(invoice["days_overdue"])
        stage = get_stage(days, int(invoice["follow_up_count"]))

        if stage == 5:
            stage_label = "⚠️  LEGAL ESCALATION"
        else:
            stage_label = f"Stage {stage} — {ESCALATION_STAGES[stage]['tone']}"

        print(f"  [{invoice['invoice_no']}] {invoice['client_name']} | "
              f"{days} days overdue | {stage_label}")

        result = generate_email(invoice, dry_run=dry_run)
        log_email(result)
        results.append(result)

    print(f"\n  ✅ Processed {len(results)} records.")
    print(f"  📋 Audit log saved to logs/audit_log.csv & logs/audit_log.json\n")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Finance Credit Follow-Up Email Agent")
    parser.add_argument("--csv", default="data/invoices.csv", help="Path to invoice CSV")
    parser.add_argument("--live", action="store_true", help="Send real emails (default: dry run)")
    parser.add_argument("--clear", action="store_true", help="Clear previous audit logs")
    args = parser.parse_args()

    results = run_agent(
        csv_path=args.csv,
        dry_run=not args.live,
        clear_logs=args.clear,
    )

    # Print sample output
    print("\n── SAMPLE OUTPUT (first record) ──────────────────────\n")
    if results:
        r = results[0]
        print(f"To: {r['client_email']}")
        print(f"Subject: {r['subject']}")
        print(f"\n{r['body']}")
        print(f"\nStatus: {r['send_status']} | Stage: {r['stage']} | Tone: {r['tone_used']}")
