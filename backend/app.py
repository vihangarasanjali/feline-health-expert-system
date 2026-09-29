"""
api.py

Feline Health Assistant - FastAPI backend for the React frontend.

This file contains NO diagnostic logic. It exposes knowledge_base.py and
inference_engine.py (the same modules the CLI uses) as a JSON API and adds
the explanation chain:

    User Input -> Facts -> Rules Applied -> Reasoning -> Final Conclusion

Endpoints (all on http://127.0.0.1:8000):
    GET  /symptoms         {symptom_id: description}
    GET  /diseases         [{disease_id, disease_name, category}]
    POST /diagnose         forward chaining.  Body: ["sneezing", "lethargy", ...]
    POST /backward/next    backward chaining, one question at a time.
                           Body: {"goal": "ear_mites", "answers": {"head_shaking": true}}

Run:
    pip install -r requirements.txt
    uvicorn api:app --reload --port 8000
"""

from typing import Dict, List

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from knowledge_base import SYMPTOMS, DISEASES, SOURCES
from inference_engine import forward_chain, backward_chain_core

app = FastAPI(title="Feline Health Assistant API")

# allow the Vite dev server (any localhost port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sources(ids):
    return [{"id": sid, **SOURCES[sid]} for sid in ids]


def _symptom(symptom_id, weight=None):
    item = {"id": symptom_id, "description": SYMPTOMS[symptom_id]}
    if weight is not None:
        item["weight"] = weight
    return item


@app.get("/symptoms")
def get_symptoms():
    return SYMPTOMS


@app.get("/diseases")
def get_diseases():
    return [
        {"disease_id": did, "disease_name": info["name"], "category": info["category"]}
        for did, info in DISEASES.items()
    ]


# ---------------------------------------------------------------------
# Forward chaining
# ---------------------------------------------------------------------
@app.post("/diagnose")
def diagnose(symptoms: List[str] = Body(...)):
    unknown = [s for s in symptoms if s not in SYMPTOMS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown symptom id(s): {unknown}")

    result = forward_chain(symptoms)
    trace_by_disease = {t["disease"]: t for t in result["diagnostic_trace"]}

    ranked = []
    for disease_id, certainty in result["ranked"]:
        if certainty <= 0:
            continue
        trace = trace_by_disease[disease_id]
        ranked.append({
            "disease_id": disease_id,
            "disease_name": DISEASES[disease_id]["name"],
            "category": DISEASES[disease_id]["category"],
            "certainty": certainty,
            "base_certainty": result["base_scores"][disease_id],
            "rule_id": trace["rule_id"],
            "reasoning": trace["explanation"],
            "matched_symptoms": [
                _symptom(s, trace["matched_weights"][s]) for s in trace["matched_symptoms"]
            ],
            "adjustments": result["adjustments"][disease_id],
            "recommendation": DISEASES[disease_id]["recommendation"],
            "sources": _sources(trace["sources"]),
        })

    rules_applied = {
        "diagnostic": [
            {
                "rule_id": t["rule_id"],
                "disease_name": DISEASES[t["disease"]]["name"],
                "matched": [_symptom(s, t["matched_weights"][s]) for s in t["matched_symptoms"]],
                "score": t["certainty"],
                "explanation": t["explanation"],
                "sources": _sources(t["sources"]),
            }
            for t in result["diagnostic_trace"] if t["matched_symptoms"]
        ],
        "differentiator": [
            {
                "rule_id": d["rule_id"],
                "explanation": d["explanation"],
                "effects": [
                    {"disease_name": DISEASES[e["disease"]]["name"], "delta": e["delta"]}
                    for e in d["effects"]
                ],
                "sources": _sources(d["sources"]),
            }
            for d in result["differentiator_trace"]
        ],
    }

    recommendations = [
        {
            "rule_id": m["rule_id"],
            "message": m["message"],
            "design": m["design"],
            "sources": _sources(m["sources"]),
        }
        for m in result["urgency_messages"]
    ]

    return {
        "input": [_symptom(s) for s in result["input"]],
        "facts": [f"has_symptom({s})." for s in result["input"]],
        "ranked": ranked,
        "rules_applied": rules_applied,
        "recommendations": recommendations,
        "overall_urgency": result["overall_urgency"],
    }


# ---------------------------------------------------------------------
# Backward chaining
# ---------------------------------------------------------------------
class BackwardRequest(BaseModel):
    goal: str
    answers: Dict[str, bool] = Field(default_factory=dict)


@app.post("/backward/next")
def backward_next(req: BackwardRequest):
    if req.goal not in DISEASES:
        raise HTTPException(status_code=404, detail=f"Unknown disease id '{req.goal}'")
    unknown = [s for s in req.answers if s not in SYMPTOMS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown symptom id(s): {unknown}")

    step = backward_chain_core(req.goal, req.answers)

    rule_condition = [
        {"id": c["symptom"], "description": SYMPTOMS[c["symptom"]], "weight": c["weight"]}
        for c in step["rule_condition"]
    ]

    if not step["done"]:
        return {
            "done": False,
            "goal": step["goal"],
            "disease_name": step["disease_name"],
            "rule_id": step["rule_id"],
            "rule_condition": rule_condition,
            "next_symptom": step["next_symptom"],
            "description": step["description"],
            "certainty_so_far": step["certainty_so_far"],
            "asked": step["asked"],
            "threshold": step["threshold"],
        }

    return {
        "done": True,
        "goal": step["goal"],
        "disease_name": step["disease_name"],
        "rule_id": step["rule_id"],
        "rule_condition": rule_condition,
        "certainty": step["certainty"],
        "threshold": step["threshold"],
        "conclusion": step["conclusion"],
        "stopped_early": step["stopped_early"],
        "stopped_reason": step["stopped_reason"],
        "trace": [
            {"id": t["symptom"], "description": SYMPTOMS[t["symptom"]],
             "weight": t["weight"], "answer": t["answer"]}
            for t in step["trace"]
        ],
        "reasoning": step["explanation"],
        "recommendation": step["recommendation"],
        "sources": _sources(step["sources"]),
    }