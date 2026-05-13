"""
credit_agent/app.py
Streamlit dashboard for the Finance Credit Follow-Up Email Agent.
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.data_ingestion import load_invoices, get_overdue_records, get_summary_stats
from agent.email_generator import generate_email, get_stage, ESCALATION_STAGES
from agent.audit_logger import log_email, load_audit_log, clear_audit_log

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="Credit Follow-Up Agent",
    page_icon="💰",
    layout="wide",
)

STAGE_COLORS = {
    1: "#28a745",
    2: "#ffc107",
    3: "#fd7e14",
    4: "#dc3545",
    5: "#6f42c1",
}

STAGE_LABELS = {
    1: "🟢 Warm & Friendly",
    2: "🟡 Polite but Firm",
    3: "🟠 Formal & Serious",
    4: "🔴 Stern & Urgent",
    5: "🟣 Legal Escalation",
}

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Agent Controls")
    uploaded_file = st.file_uploader("Upload Invoice CSV", type=["csv"])
    dry_run = st.toggle("Dry Run Mode (no real emails)", value=True)
    if not dry_run:
        st.warning("⚠️ LIVE mode: emails will be sent!")
    run_btn = st.button("▶ Run Agent", type="primary", use_container_width=True)
    clear_btn = st.button("🗑 Clear Audit Log", use_container_width=True)
    st.markdown("---")
    st.markdown("**Escalation Matrix**")
    for s, info in ESCALATION_STAGES.items():
        st.markdown(f"**Stage {s}:** {info['tone']}  \n_{info['days_range']}_")
    st.markdown("**Stage 5:** Legal Escalation Flag  \n_30+ days overdue_")

# ── Main area ──────────────────────────────────────────────
st.title("💰 Finance Credit Follow-Up Email Agent")
st.caption("AI-powered invoice follow-up with tone escalation | Dry-Run Mode")

# Determine CSV path
csv_path = "data/invoices.csv"
if uploaded_file:
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.read())
        csv_path = tmp.name

# Load data
try:
    df = load_invoices(csv_path)
    stats = get_summary_stats(df)
except Exception as e:
    st.error(f"Error loading invoice data: {e}")
    st.stop()

# ── KPI Cards ──────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Invoices", stats["total_invoices"])
col2.metric("Overdue", stats["overdue_count"], delta=f"-{stats['overdue_count']}", delta_color="inverse")
col3.metric("Total Overdue Amt", f"₹{stats['total_overdue_amount']:,.0f}")
col4.metric("Legal Flags", stats["legal_escalation_count"], delta_color="inverse")
col5.metric("Current (OK)", stats["current_count"])

st.markdown("---")

# ── Invoice Table ──────────────────────────────────────────
st.subheader("📋 Invoice Queue")

overdue_df = get_overdue_records(df).copy()
overdue_df["Stage"] = overdue_df.apply(
    lambda r: get_stage(int(r["days_overdue"]), int(r["follow_up_count"])), axis=1
)
overdue_df["Tone"] = overdue_df["Stage"].map(STAGE_LABELS)
overdue_df["Amount (₹)"] = overdue_df["amount"].apply(lambda x: f"₹{int(x):,}")

display_cols = ["invoice_no", "client_name", "days_overdue", "Amount (₹)", "follow_up_count", "Tone"]
st.dataframe(
    overdue_df[display_cols].rename(columns={
        "invoice_no": "Invoice #",
        "client_name": "Client",
        "days_overdue": "Days Overdue",
        "follow_up_count": "Prior Follow-Ups",
    }),
    use_container_width=True,
    hide_index=True,
)

# ── Run Agent ──────────────────────────────────────────────
if clear_btn:
    clear_audit_log()
    st.success("Audit log cleared.")

if run_btn:
    st.markdown("---")
    st.subheader("📧 Generating Emails...")
    progress = st.progress(0)
    results = []
    overdue_records = overdue_df.to_dict("records")
    total = len(overdue_records)

    for i, row in enumerate(overdue_records):
        with st.spinner(f"Processing {row['invoice_no']}..."):
            result = generate_email(row, dry_run=dry_run)
            log_email(result)
            results.append(result)
        progress.progress((i + 1) / total)

    st.success(f"✅ Processed {total} records. Audit log updated.")

    # Show results
    st.markdown("---")
    st.subheader("📬 Generated Emails")
    for r in results:
        stage = r["stage"]
        if stage == 5:
            with st.expander(f"⚠️ {r['invoice_no']} — {r['client_name']} | LEGAL ESCALATION FLAG"):
                st.error("This record exceeds 30 days overdue. Flagged for manual legal/finance review. No automated email sent.")
                st.write(f"**Assigned Manager:** {r['assigned_manager']}")
        else:
            color = STAGE_COLORS.get(stage, "#333")
            label = STAGE_LABELS.get(stage, "")
            with st.expander(
                f"Stage {stage} | {r['invoice_no']} — {r['client_name']} | {r['days_overdue']} days overdue | {label}"
            ):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.markdown(f"**To:** {r['client_email']}")
                    st.markdown(f"**Amount:** {r['currency']} {int(float(r['amount'])):,}")
                    st.markdown(f"**Days Overdue:** {r['days_overdue']}")
                    st.markdown(f"**Tone:** {r['tone_used']}")
                    st.markdown(f"**Status:** `{r['send_status']}`")
                with col_b:
                    st.markdown(f"**Subject:** {r['subject']}")
                    st.text_area("Email Body", r["body"], height=200, key=r["invoice_no"])

# ── Audit Log ──────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Audit Log")
log = load_audit_log()
if log:
    log_df = pd.DataFrame(log)
    display_log_cols = ["timestamp", "invoice_no", "client_name", "stage", "tone_used", "subject", "send_status", "days_overdue", "amount"]
    available = [c for c in display_log_cols if c in log_df.columns]
    st.dataframe(log_df[available], use_container_width=True, hide_index=True)

    # Download button
    csv_bytes = log_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Audit Log (CSV)", csv_bytes, "audit_log.csv", "text/csv")
else:
    st.info("No audit log entries yet. Run the agent to generate emails.")
