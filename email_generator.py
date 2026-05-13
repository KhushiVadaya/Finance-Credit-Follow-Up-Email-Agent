"""
credit_agent/agent/email_generator.py
Core LLM-powered email generation with tone escalation engine.
Uses Google Gemini (free tier).
"""

import os
import json
from datetime import datetime
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

ESCALATION_STAGES = {
    1: {"label": "1st Follow-Up", "tone": "Warm & Friendly", "days_range": "1–7 days overdue",
        "key_message": "Gentle reminder, assume oversight", "cta": "Pay now link / bank details"},
    2: {"label": "2nd Follow-Up", "tone": "Polite but Firm", "days_range": "8–14 days overdue",
        "key_message": "Payment still pending; request confirmation", "cta": "Confirm payment date"},
    3: {"label": "3rd Follow-Up", "tone": "Formal & Serious", "days_range": "15–21 days overdue",
        "key_message": "Escalating concern; mention impact", "cta": "Respond within 48 hrs"},
    4: {"label": "4th Follow-Up", "tone": "Stern & Urgent", "days_range": "22–30 days overdue",
        "key_message": "Final reminder before escalation", "cta": "Pay immediately or call us"},
}


def get_stage(days_overdue: int, follow_up_count: int) -> int:
    if days_overdue > 30: return 5
    elif days_overdue >= 22: return 4
    elif days_overdue >= 15: return 3
    elif days_overdue >= 8: return 2
    else: return 1


def build_prompt(stage: int, invoice: dict) -> str:
    stage_info = ESCALATION_STAGES[stage]
    return f"""You are a professional finance collections assistant for a reputable Indian company.
Generate a {stage_info['tone']} follow-up email for this overdue invoice.

STRICT RULES:
1. Use ONLY the invoice details below. Do NOT invent any data.
2. Every email MUST include: client name, invoice number, amount due, due date, days overdue, and payment link.
3. Tone must be exactly: {stage_info['tone']}
4. Key message: {stage_info['key_message']}
5. CTA: {stage_info['cta']}
6. Output ONLY a valid JSON object — no explanation, no markdown, no ```json fences.

Invoice Details:
- Client Name: {invoice['client_name']}
- Invoice Number: {invoice['invoice_no']}
- Amount Due: {invoice['currency']} {int(float(invoice['amount'])):,}
- Due Date: {invoice['due_date']}
- Days Overdue: {invoice['days_overdue']}
- Follow-Up Stage: {stage} ({stage_info['tone']})
- Payment Link: {invoice['payment_link']}
- Contact Person: {invoice['contact_person']}
- Finance Manager: {invoice.get('assigned_manager', 'Finance Manager')}

Required JSON schema:
{{
  "subject": "email subject line here",
  "body": "full email body here with \\n for line breaks",
  "tone_used": "{stage_info['tone']}",
  "stage": {stage}
}}"""


def generate_email(invoice: dict, dry_run: bool = True) -> dict:
    days_overdue = int(invoice["days_overdue"])
    follow_up_count = int(invoice["follow_up_count"])
    stage = get_stage(days_overdue, follow_up_count)

    if stage == 5:
        return {
            "invoice_no": invoice["invoice_no"], "client_name": invoice["client_name"],
            "client_email": invoice["client_email"], "days_overdue": days_overdue,
            "amount": invoice["amount"], "currency": invoice["currency"],
            "due_date": invoice.get("due_date", ""), "stage": 5,
            "tone_used": "ESCALATED – Legal Review",
            "subject": "N/A – Flagged for Legal Review",
            "body": "This record has been flagged for manual legal/finance review. No automated email will be sent.",
            "send_status": "FLAGGED_FOR_LEGAL", "timestamp": datetime.now().isoformat(),
            "assigned_manager": invoice.get("assigned_manager", "Finance Manager"),
            "dry_run": dry_run, "error": None,
        }

    stage_info = ESCALATION_STAGES[stage]
    try:
        response = model.generate_content(build_prompt(stage, invoice))
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        parsed = json.loads(raw.strip())
        return {
            "invoice_no": invoice["invoice_no"], "client_name": invoice["client_name"],
            "client_email": invoice["client_email"], "days_overdue": days_overdue,
            "amount": invoice["amount"], "currency": invoice["currency"],
            "due_date": invoice.get("due_date", ""),
            "stage": parsed.get("stage", stage), "tone_used": parsed.get("tone_used", stage_info["tone"]),
            "subject": parsed["subject"], "body": parsed["body"],
            "send_status": "DRY_RUN" if dry_run else "SENT",
            "timestamp": datetime.now().isoformat(),
            "assigned_manager": invoice.get("assigned_manager", "Finance Manager"),
            "dry_run": dry_run, "error": None,
        }
    except Exception as e:
        return {
            "invoice_no": invoice["invoice_no"], "client_name": invoice["client_name"],
            "client_email": invoice["client_email"], "days_overdue": days_overdue,
            "amount": invoice["amount"], "currency": invoice["currency"],
            "due_date": invoice.get("due_date", ""), "stage": stage,
            "tone_used": stage_info["tone"], "subject": "ERROR",
            "body": f"Email generation failed: {str(e)}",
            "send_status": "ERROR", "timestamp": datetime.now().isoformat(),
            "assigned_manager": invoice.get("assigned_manager", "Finance Manager"),
            "dry_run": dry_run, "error": str(e),
        }
