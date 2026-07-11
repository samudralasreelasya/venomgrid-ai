# VenomGrid AI — Predict. Prepare. Prioritize.

An AI-powered snakebite emergency management platform: prevention (RiskAI),
response (Smart Triage AI), and treatment coordination (AntiVenomNet).

## Structure

```
venomgrid-ai/
├── backend/
│   ├── app.py              # Flask API: triage, hospital routing, stock rebalancing
│   ├── db.py                # SQLite setup + helpers
│   ├── models/
│   │   ├── triage.py         # Smart Triage AI (rule-based + simple ML hook)
│   │   ├── antivenom_net.py  # Hospital routing + stock prediction
│   │   └── risk_ai.py        # Hotspot risk scoring (static/pre-computed for demo)
│   └── data/
│       ├── hospitals.csv     # Simulated hospital + antivenom stock data
│       ├── villages.csv       # Simulated village risk factors
│       └── seed.py           # Populates SQLite from the CSVs
├── dashboard/
│   └── app.py                # Streamlit dashboard (map + live case view = "Digital Twin")
├── notebooks/
│   └── risk_model.ipynb      # Where you'd pre-compute the RiskAI heat map
└── requirements.txt
```

## Honest scope (say this out loud in your demo)

- **Smart Triage**: real rule-based scoring logic (swap in a trained classifier later if you get time/data).
- **AntiVenomNet**: routing + stock logic is real; the underlying hospital inventory data is **simulated** — flagged clearly as a mock dataset standing in for a future hospital-system API.
- **RiskAI**: pre-computed from a static/simulated dataset for the demo, described as what a live weather+historical-data pipeline would look like in production.

## Quickstart

```bash
cd venomgrid-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python backend/data/seed.py       # creates + seeds SQLite db
python backend/app.py             # runs Flask API on :5000

# in a second terminal
streamlit run dashboard/app.py    # runs dashboard on :8501
```

## Demo flow (matches the pitch deck)

1. Dashboard shows tomorrow's predicted high-risk district (RiskAI, static).
2. Dashboard shows antivenom stock is low there (AntiVenomNet).
3. AI suggests redistributing stock from a neighboring hospital.
4. Simulate a patient report via the dashboard form.
5. Smart Triage AI scores it Critical/High/Moderate.
6. AntiVenomNet routes the patient to nearest hospital with stock.
7. Dashboard's "Digital Twin" case view updates live.
