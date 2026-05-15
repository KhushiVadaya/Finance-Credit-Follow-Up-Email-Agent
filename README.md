# 💰 Finance Credit Follow-Up Email Agent

An AI-powered agent that automatically generates personalised, tone-escalated follow-up emails for overdue invoices — reducing Days Sales Outstanding (DSO) while maintaining professional client relationships.

---

## 🎯 Project Overview

Finance teams waste significant time manually chasing overdue payments. This agent automates the entire workflow:

1. **Ingests** overdue invoice records from a CSV/Excel source
2. **Determines** the correct escalation stage based on days overdue
3. **Generates** a personalised, stage-appropriate email using GPT-4o
4. **Logs** every action in a full audit trail (CSV + JSON)
5. **Flags** records >30 days overdue for legal/manual review

---

## 🏗️ Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  STREAMLIT DASHBOARD (app.py)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │      ORCHESTRATOR          │
         │   (agent/orchestrator.py)  │
         └──┬──────────┬─────────────┘
            │          │
   ┌────────▼────┐  ┌──▼──────────────┐
   │   DATA      │  │  EMAIL GENERATOR │
   │ INGESTION   │  │ (LangChain +     │
   │ (pandas CSV)│  │  GPT-4o)         │
   └─────────────┘  └──────┬──────────┘
                           │
                  ┌────────▼────────┐
                  │  AUDIT LOGGER   │
                  │ (CSV + JSON)    │
                  └─────────────────┘
```

---

## ⚡ Tone Escalation Matrix

| Stage | Trigger | Tone | Key CTA |
|-------|---------|------|---------|
| 1 | 1–7 days overdue | 🟢 Warm & Friendly | Pay now link |
| 2 | 8–14 days overdue | 🟡 Polite but Firm | Confirm payment date |
| 3 | 15–21 days overdue | 🟠 Formal & Serious | Respond within 48 hrs |
| 4 | 22–30 days overdue | 🔴 Stern & Urgent | Pay immediately or call |
| 5 | 30+ days overdue | 🟣 Legal Escalation | Manual review — no auto email |

---

## 🚀 Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/credit-followup-agent.git
cd credit-followup-agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 4. Run the Streamlit Dashboard
```bash
streamlit run app.py
```

### 5. Or Run from CLI
```bash
# Dry run (default — no emails sent)
python agent/orchestrator.py --csv data/invoices.csv

# Live run (sends real emails — requires SMTP config)
python agent/orchestrator.py --csv data/invoices.csv --live

# Clear previous logs
python agent/orchestrator.py --clear
```

---

## 📁 Project Structure

```
credit-followup-agent/
├── agent/
│   ├── __init__.py
│   ├── data_ingestion.py      # CSV loader & validator
│   ├── email_generator.py     # LLM email generation & tone engine
│   ├── audit_logger.py        # CSV + JSON audit trail
│   └── orchestrator.py        # Main pipeline runner
├── data/
│   └── invoices.csv           # Sample invoice data
├── logs/
│   ├── audit_log.csv          # (generated at runtime)
│   └── audit_log.json         # (generated at runtime)
├── app.py                     # Streamlit dashboard
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🔐 Security Mitigations

| Risk | Mitigation |
|------|-----------|
| **Prompt Injection** | Structured JSON output mode enforced (`response_format: json_object`). Input sanitised via pandas before passing to LLM. |
| **Data Privacy / PII** | All processing is local. PII (names, emails) is only sent to OpenAI API — use local models (Ollama/Mistral) for full data isolation. |
| **API Key Exposure** | Keys stored in `.env` via `python-dotenv`. `.env` is in `.gitignore`. Never hardcoded. |
| **Hallucination Risk** | JSON schema enforced. All invoice fields (amount, date, name) are injected from the data source — LLM cannot invent values. |
| **Unauthorised Access** | API key authentication required for any endpoint. Dry-run mode enabled by default. |
| **Email Spoofing** | Dry-run mode prevents accidental sends. For live mode: use SendGrid with verified sender domain + SPF/DKIM/DMARC. |
| **Escalation Cap** | Records >30 days are flagged for human review — agent never auto-emails beyond Stage 4. |

---

## 🛠️ Tech Stack & Decision Log

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **LLM** | GPT-4o (gpt-4o-2024-08-06) | Best JSON-mode reliability, strong instruction following, cost-effective for structured output |
| **Agent Framework** | LangChain | Industry standard; excellent tool ecosystem; familiar to most reviewers |
| **Data Source** | CSV / pandas | Simple, portable, no infrastructure needed |
| **Email Sending** | Dry-run (log to CSV/JSON) | Safe for demo; no accidental client emails |
| **UI** | Streamlit | Rapid prototyping; professional demo in minimal code |
| **Logging** | CSV + JSON dual log | CSV for human review; JSON for programmatic consumption |

---

## 📊 Sample Output

**Stage 1 — Warm & Friendly**
```
Subject: Quick Reminder – Invoice #INV-2024-006 | ₹55,000 Due

Hi Deepak, I hope you're doing well! This is a friendly reminder that Invoice 
#INV-2024-006 for ₹55,000 was due on 08 May 2025, now 5 days overdue. 
If you've already processed this payment, please disregard this note — 
otherwise, you can complete the payment here: https://pay.example.com/INV-2024-006

Thank you for your continued partnership!
```

**Stage 4 — Stern & Urgent**
```
Subject: FINAL NOTICE – Invoice #INV-2024-001 – Immediate Action Required

Dear Mr. Kapoor, This is our final automated reminder. Invoice #INV-2024-001 
for ₹45,000 is now 23 days overdue (due 20 Apr 2025). Failure to remit payment 
within 24 hours will result in escalation to our legal and recovery team. 
Please act immediately: https://pay.example.com/INV-2024-001
```

---
## Screenshots

<img width="1920" height="1020" alt="Screenshot 2026-05-15 181713" src="https://github.com/user-attachments/assets/ef976495-60c5-4f0a-9025-467a82f2ee9a" />
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/822d1b2a-6e71-4c1a-ae77-0755df13e0e5" />
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/3656b169-8c04-48c4-b2dc-758fcb809142" />
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/b4b26b37-469a-4057-9f2a-8ac78acfa8ec" />
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/722f560a-4cae-4c04-9de8-bb38f0e6aa9b" />
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/35ea2aa8-a0d5-40f1-8080-7feaa477eb53" />
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/11613b95-6918-4ef6-97a5-d67938c4a21e" />

![Uploading image.png…]()











