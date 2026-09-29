# Feline Health Assistant — Expert System

A feline disease diagnosis expert system covering 12 common cat conditions.
It uses a rule-based knowledge base (facts + rules derived from cited
veterinary sources) and an inference engine supporting both **forward
chaining** (symptoms → diagnosis) and **backward chaining** (hypothesis →
confirm/deny), with a full explanation trace for every conclusion.

A written report (PDF) covering the knowledge engineering process, testing,
and full rules annex accompanies this code and is submitted separately /
linked here: **[add link or note "see submitted PDF"]**.

## Project structure

```
.
├── backend/
│   ├── knowledge_base.py     # Facts + rules (with cited sources)
│   ├── inference_engine.py   # Forward & backward chaining                # Command-line interface
│   ├── app.py                  # FastAPI backend for the web UI
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── App.css
    └── package.json
```

## Requirements

- Python 3.10+
- Node.js 18+ and npm
- Internet access (to load the Google Fonts used by the web UI)

## Running the web version

**1. Start the backend API** (in one terminal):

```bash
cd backend
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

Check it's running: open http://127.0.0.1:8000/symptoms — you should see a
JSON list of symptoms.

**2. Start the frontend** (in a second terminal):

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (typically http://localhost:5173).

## How to use it

- **Symptom check** — tick the symptoms you've noticed (grouped into tabs:
  Eyes & Nose, Tummy, Skin & Ears, Bathroom, General) and press **Diagnose
  Cat**. You'll get a ranked list of likely conditions with a certainty
  percentage.
- **Check an illness** — pick a disease you suspect; the assistant asks a
  short series of yes/no questions and tells you whether the evidence
  confirms it.
- In both modes, the **"How it was decided"** tab shows the full reasoning:
  the facts recorded, which rules fired, how the certainty score was built
  up, and the sources behind each rule.

### Example

Input symptoms: *sneezing*, *nasal discharge*, *eye discharge*, *lethargy*
Output: Upper Respiratory Infection (URI) — 100% certainty, with the
matched symptoms, the rule that fired (R1), and the two differentiator
rules (D3, D4) that resolved the overlap with conjunctivitis.

## Knowledge base summary

- 45 facts (33 symptoms, 12 diseases)
- 32 rules (12 diagnostic, 8 differentiator, 12 urgency/recommendation)
- Every diagnostic, differentiator, and disease-specific urgency rule cites
  a real veterinary source (see `SOURCES` in `knowledge_base.py`, or the
  References section of the report).

## Disclaimer

This system is an educational expert-system assignment. It is advisory
only and does not replace professional veterinary diagnosis.