# 🏆 Employee of the Month — Automated Recognition System

> **HR Portfolio Project** | Built with Python, Streamlit & Plotly

A fully automated employee recognition system that ingests HR performance data,
runs a weighted scoring engine, surfaces a ranked leaderboard, and notifies the
winner by email — all through a clean web dashboard.

---

## Features

| Feature | Description |
|---|---|
| 📂 **CSV / Excel Upload** | Drop in any employee data file matching the schema |
| ⚖️ **Configurable Weights** | Adjust how much each metric contributes to the score |
| 🧮 **Scoring Engine** | Normalised, weighted composite scoring with eligibility rules |
| 📊 **Interactive Dashboard** | Leaderboard, radar chart, department breakdown, fairness check |
| 📧 **Email Notifications** | Auto-sends congratulations to winner + summary to HR |
| 📜 **Winner History** | Persists monthly winners with trend visualisation |

---

## Quick Start

```bash
# 1. Clone / download the project
cd employee_recognition

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## Data Format

Upload a CSV or Excel file with these columns:

| Column | Type | Range | Description |
|---|---|---|---|
| `employee_id` | string | — | Unique identifier |
| `name` | string | — | Full name |
| `department` | string | — | Department name |
| `performance_score` | number | 0–100 | KPI / target attainment score |
| `peer_nominations` | integer | 0+ | Number of peer nominations received |
| `attendance_pct` | number | 0–100 | Attendance percentage |
| `manager_rating` | number | 0–10 | Direct manager rating |
| `months_employed` | integer | 0+ | Tenure in months |
| `email` | string | — | Employee email address |

A sample file is included at `data/employees_sample.csv` and downloadable from the app sidebar.

---

## Scoring Methodology

Each metric is **min-max normalised** to a 0–100 scale before weighting,
ensuring metrics with different units are fairly compared.

```
composite_score = Σ (normalised_metric × weight)
```

**Default weights:**

| Metric | Weight | HR Rationale |
|---|---|---|
| Performance Score | 40% | Primary KPI attainment |
| Peer Nominations | 30% | Collaboration & culture contribution |
| Attendance % | 20% | Reliability & commitment |
| Manager Rating | 10% | Direct supervisor assessment |

Weights are fully configurable via the sidebar sliders.

---

## Eligibility Rules

Two fairness rules are enforced automatically:

1. **Minimum tenure** — employees with fewer than 6 months are excluded
2. **No back-to-back wins** — the previous month's winner is excluded

Ineligible employees still appear in the leaderboard but are clearly flagged.

---

## Email Setup (Gmail)

1. Enable 2-factor authentication on your Gmail account
2. Generate an **App Password**: Google Account → Security → App Passwords
3. Enter your Gmail address and App Password in the sidebar
4. Add the HR manager's email to receive the summary report

> For production use, replace `smtplib` with SendGrid or AWS SES for
> improved deliverability and logging.

---

## Project Structure

```
employee_recognition/
├── app.py                    # Main Streamlit application
├── requirements.txt
├── data/
│   ├── employees_sample.csv  # Sample data
│   └── winner_history.json   # Auto-generated winner log
└── utils/
    ├── scoring_engine.py     # Core scoring & eligibility logic
    ├── email_notifier.py     # Email templates & SMTP sender
    └── charts.py             # All Plotly visualisations
```

---

## HR Considerations & Limitations

This system is designed as a **decision-support tool**, not a final arbiter.
HR practitioners should be aware of:

- **Recency bias** — data should cover the full month, not recent weeks only
- **Remote worker bias** — peer nominations may under-represent remote employees
- **Small department bias** — normalisation means scores are relative to the uploaded cohort
- **Metric gaming** — employees aware of criteria may optimise superficially

A manual override / review step before publishing results is recommended.

---


