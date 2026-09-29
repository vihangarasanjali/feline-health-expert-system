"""
inference_engine.py

Feline Disease Diagnosis Expert System
Inference Engine: Forward Chaining + Backward Chaining + Explanation

Forward chaining (data-driven):
    symptoms (facts) -> rules that match -> conclusions.
    Every rule application is recorded so the result can be explained as

        User Input -> Facts -> Rules Applied -> Reasoning -> Final Conclusion

Backward chaining (goal-driven):
    hypothesis (goal disease) -> the rule that would prove it -> the symptoms
    that rule needs -> ask only those questions, stopping early as soon as the
    goal is confirmed or can no longer be reached.

Both modes return structured traces (used by the CLI text explanations here
and by the JSON API in api.py) so the reasoning can be shown to the user.
"""

from knowledge_base import (SYMPTOMS, DISEASES, DIAGNOSTIC_RULES, DIFFERENTIATOR_RULES,
                            URGENCY_RULES, SOURCES)

CONFIDENCE_THRESHOLD = 50  # minimum certainty (%) to "confirm" a disease in backward chaining

_URGENCY_RANK = {"routine": 0, "urgent": 1, "emergency": 2}


# =====================================================================
# FORWARD CHAINING
# =====================================================================
def forward_chain(confirmed_symptoms):
    """
    confirmed_symptoms: a set/list of symptom ids the cat IS showing.

    Returns a dict with:
        input                 -> sorted list of the symptoms given
        ranked                -> [(disease_id, certainty), ...] sorted desc
        base_scores           -> {disease_id: score from its diagnostic rule}
        adjustments           -> {disease_id: [{rule_id, delta, applied}, ...]}
        diagnostic_trace      -> one entry per diagnostic rule (R1..R12)
        differentiator_trace  -> the differentiator rules that fired (D1..D8)
        urgency_messages      -> the recommendation rules that fired (U1..U12)
        overall_urgency       -> "emergency" | "urgent" | "routine"
    """
    confirmed = set(confirmed_symptoms)
    unknown = confirmed - set(SYMPTOMS)
    if unknown:
        raise ValueError(f"Unknown symptom id(s): {sorted(unknown)}")

    results = {}
    base_scores = {}
    diagnostic_trace = []

    # --- Step 1: diagnostic rules (R1..R12) ---
    for rule in DIAGNOSTIC_RULES:
        disease = rule["disease"]
        matched = {s: w for s, w in rule["condition"].items() if s in confirmed}
        certainty = min(100, sum(matched.values()))
        results[disease] = certainty
        base_scores[disease] = certainty
        diagnostic_trace.append({
            "rule_id": rule["id"],
            "disease": disease,
            "matched_symptoms": list(matched.keys()),
            "matched_weights": dict(matched),
            "unmatched_symptoms": [s for s in rule["condition"] if s not in matched],
            "certainty": certainty,
            "explanation": rule["explanation"],
            "sources": rule["sources"],
        })

    # --- Step 2: differentiator rules (D1..D8) resolve look-alike diseases ---
    adjustments = {d: [] for d in results}
    differentiator_trace = []
    for d in DIFFERENTIATOR_RULES:
        if all(s in confirmed for s in d["if_symptoms"]):
            effects = []
            for disease, amt in d.get("boost", {}).items():
                before = results[disease]
                results[disease] = min(100, before + amt)
                adjustments[disease].append({"rule_id": d["id"], "delta": amt,
                                             "applied": results[disease] - before})
                effects.append({"disease": disease, "delta": amt})
            for disease, amt in d.get("penalise", {}).items():
                before = results[disease]
                results[disease] = max(0, before - amt)
                adjustments[disease].append({"rule_id": d["id"], "delta": -amt,
                                             "applied": results[disease] - before})
                effects.append({"disease": disease, "delta": -amt})
            differentiator_trace.append({
                "rule_id": d["id"],
                "explanation": d["explanation"],
                "derivation": d["derivation"],
                "effects": effects,
                "sources": d["sources"],
            })

    ranked = sorted(results.items(), key=lambda kv: -kv[1])

    # --- Step 3: urgency / recommendation rules (U1..U12) ---
    urgency_messages = []
    overall_urgency = "routine"
    top_disease, top_certainty = (ranked[0] if ranked else (None, 0))

    for u in URGENCY_RULES:
        fired = False
        if "if_symptoms" in u:
            if all(s in confirmed for s in u["if_symptoms"]):
                fired = True
                if u.get("urgency") == "emergency":
                    overall_urgency = "emergency"
        elif "min_certainty" in u:
            fired = top_certainty >= u["min_certainty"]
        elif "max_certainty" in u:
            fired = top_certainty <= u["max_certainty"]
        elif "tie_margin" in u:
            fired = (len(ranked) >= 2 and top_certainty > 0
                     and (ranked[0][1] - ranked[1][1]) <= u["tie_margin"])
        elif "disease" in u:
            fired = top_disease == u["disease"] and top_certainty > 0

        if fired:
            urgency_messages.append({
                "rule_id": u["id"],
                "message": u["message"],
                "sources": u.get("sources", []),
                "design": bool(u.get("design")),
            })

    # a confident match for a disease labelled urgent/emergency raises the overall level
    if top_disease and top_certainty >= CONFIDENCE_THRESHOLD:
        label = DISEASES[top_disease]["urgency"]
        if label in ("urgent", "emergency"):
            level = "emergency" if label == "emergency" else "urgent"
            if _URGENCY_RANK[level] > _URGENCY_RANK[overall_urgency]:
                overall_urgency = level

    return {
        "input": sorted(confirmed),
        "ranked": ranked,
        "base_scores": base_scores,
        "adjustments": adjustments,
        "diagnostic_trace": diagnostic_trace,
        "differentiator_trace": differentiator_trace,
        "urgency_messages": urgency_messages,
        "overall_urgency": overall_urgency,
    }


def _score_build(result, disease):
    """'75 (R1) +15 (D3) +10 (D4) = 100%' - how a certainty was built up."""
    trace = next(t for t in result["diagnostic_trace"] if t["disease"] == disease)
    parts = [f"{result['base_scores'][disease]} ({trace['rule_id']})"]
    total = result["base_scores"][disease]
    for a in result["adjustments"][disease]:
        parts.append(f"{a['delta']:+d} ({a['rule_id']})")
        total += a["delta"]
    final = dict(result["ranked"])[disease]
    text = " ".join(parts) + f" = {final}%"
    if total != final:
        text += " (limited to the 0-100 range)"
    return text


def explain_forward(result, top_n=3):
    """Text explanation: User Input -> Facts -> Rules Applied -> Reasoning -> Conclusion."""
    lines = []
    used_sources = []

    lines.append("=== 1. USER INPUT ===")
    for s in result["input"]:
        lines.append(f"- {SYMPTOMS[s]}")

    lines.append("\n=== 2. FACTS ASSERTED ===")
    for s in result["input"]:
        lines.append(f"has_symptom({s}).")

    lines.append("\n=== 3. RULES APPLIED ===")
    fired = [t for t in result["diagnostic_trace"] if t["matched_symptoms"]]
    for t in fired:
        parts = ", ".join(f"{s} (+{w})" for s, w in t["matched_weights"].items())
        lines.append(f"[{t['rule_id']}] {DISEASES[t['disease']]['name']}: {parts} = {t['certainty']}")
    for d in result["differentiator_trace"]:
        eff = ", ".join(f"{DISEASES[e['disease']]['name']} {e['delta']:+d}" for e in d["effects"])
        lines.append(f"[{d['rule_id']}] {d['explanation']}  ->  {eff}")
        used_sources += d["sources"]

    lines.append("\n=== 4. REASONING ===")
    shown = [(d, c) for d, c in result["ranked"][:top_n] if c > 0]
    for disease, certainty in shown:
        trace = next(t for t in result["diagnostic_trace"] if t["disease"] == disease)
        lines.append(f"- {DISEASES[disease]['name']}: {_score_build(result, disease)}")
        lines.append(f"  Why: {trace['explanation']}")
        lines.append(f"  Sources: {', '.join(trace['sources'])}")
        used_sources += trace["sources"]

    lines.append("\n=== 5. FINAL CONCLUSION ===")
    if not shown:
        lines.append("No disease pattern matched the reported symptoms.")
    else:
        top, top_c = shown[0]
        lines.append(f"Most likely: {DISEASES[top]['name']} ({top_c}% certainty)")
        lines.append(f"Urgency level: {result['overall_urgency'].upper()}")
        lines.append(f"Advice: {DISEASES[top]['recommendation']}")
    for m in result["urgency_messages"]:
        tag = "system rule" if m["design"] else "sources: " + ", ".join(m["sources"])
        lines.append(f"- [{m['rule_id']}] {m['message']} ({tag})")
        used_sources += m["sources"]

    used = sorted(set(used_sources), key=lambda x: int(x[1:]))
    if used:
        lines.append("\n=== SOURCES CITED ===")
        for sid in used:
            s = SOURCES[sid]
            lines.append(f"{sid}: {s['title']} - {s['publisher']} - {s['url']}")

    return "\n".join(lines)


# =====================================================================
# BACKWARD CHAINING
# =====================================================================
def _ordered_condition(goal_disease):
    """Return (rule, symptoms-sorted-by-weight-desc) for a disease's diagnostic rule."""
    rule = next((r for r in DIAGNOSTIC_RULES if r["disease"] == goal_disease), None)
    if rule is None:
        raise ValueError(f"No diagnostic rule found for disease '{goal_disease}'")
    ordered = sorted(rule["condition"].items(), key=lambda kv: -kv[1])
    return rule, ordered


def backward_chain_core(goal_disease, answers):
    """
    Stateless single step of backward chaining, built for UIs (web/React) that
    ask one question, wait for a click, then ask the next.

    answers: {symptom_id: bool} known so far (kept by the caller).

    Returns EITHER
      {"done": False, "next_symptom", "description", ...}   -> ask this next
    OR (goal confirmed, ruled out, or every symptom answered)
      {"done": True, "certainty", "conclusion", "trace", "stopped_reason", ...}

    Pruning: questions stop as soon as certainty reaches the threshold, or the
    threshold can no longer be reached even if every remaining answer is "yes".
    """
    rule, ordered = _ordered_condition(goal_disease)
    rule_condition = [{"symptom": s, "weight": w} for s, w in ordered]
    remaining_weight = sum(w for _, w in ordered)
    certainty = 0
    trace = []

    for symptom, weight in ordered:
        if certainty >= CONFIDENCE_THRESHOLD or certainty + remaining_weight < CONFIDENCE_THRESHOLD:
            return _finish_backward(goal_disease, rule, rule_condition, trace, certainty, True)

        if symptom not in answers:
            return {
                "done": False,
                "goal": goal_disease,
                "disease_name": DISEASES[goal_disease]["name"],
                "rule_id": rule["id"],
                "rule_condition": rule_condition,
                "next_symptom": symptom,
                "description": SYMPTOMS[symptom],
                "certainty_so_far": certainty,
                "asked": len(trace),
                "threshold": CONFIDENCE_THRESHOLD,
            }

        answer = bool(answers[symptom])
        remaining_weight -= weight
        if answer:
            certainty += weight
        trace.append({"symptom": symptom, "weight": weight, "answer": answer})

    return _finish_backward(goal_disease, rule, rule_condition, trace, certainty, False)


def _finish_backward(goal_disease, rule, rule_condition, trace, certainty, stopped_early):
    if not stopped_early:
        reason = "all_answered"
    elif certainty >= CONFIDENCE_THRESHOLD:
        reason = "confirmed_early"
    else:
        reason = "ruled_out_early"
    return {
        "done": True,
        "goal": goal_disease,
        "disease_name": DISEASES[goal_disease]["name"],
        "rule_id": rule["id"],
        "rule_condition": rule_condition,
        "certainty": certainty,
        "threshold": CONFIDENCE_THRESHOLD,
        "confirmed_symptoms": {t["symptom"] for t in trace if t["answer"]},
        "denied_symptoms": {t["symptom"] for t in trace if not t["answer"]},
        "conclusion": certainty >= CONFIDENCE_THRESHOLD,
        "stopped_early": stopped_early,
        "stopped_reason": reason,
        "trace": trace,
        "explanation": rule["explanation"],
        "recommendation": DISEASES[goal_disease]["recommendation"],
        "sources": rule["sources"],
    }


def backward_chain(goal_disease, ask_fn):
    """
    Interactive wrapper for synchronous UIs (the CLI): ask_fn(symptom_id,
    description) -> bool. Steps the stateless core until it reports "done".
    """
    answers = {}
    while True:
        step = backward_chain_core(goal_disease, answers)
        if step["done"]:
            return step
        answers[step["next_symptom"]] = bool(ask_fn(step["next_symptom"], step["description"]))


_STOP_TEXT = {
    "confirmed_early": "Stopped early: the certainty already reached the threshold, so the remaining questions were not needed.",
    "ruled_out_early": "Stopped early: even if every remaining answer were 'yes', the threshold could not be reached.",
    "all_answered": "Every symptom in the rule was asked.",
}


def explain_backward(result):
    """Text explanation: Goal -> Rule tested -> Facts gathered -> Reasoning -> Conclusion."""
    lines = []
    lines.append("=== 1. GOAL (HYPOTHESIS) ===")
    lines.append(f"Is the cat's problem: {result['disease_name']}?")

    lines.append(f"\n=== 2. RULE TESTED ({result['rule_id']}) ===")
    needs = ", ".join(f"{c['symptom']} ({c['weight']})" for c in result["rule_condition"])
    lines.append(f"Needs (weight): {needs}")
    lines.append(f"Confirmed when certainty >= {result['threshold']}%")

    lines.append("\n=== 3. FACTS GATHERED (questions asked) ===")
    for t in result["trace"]:
        ans = "YES" if t["answer"] else "no"
        pts = f"+{t['weight']}" if t["answer"] else "+0"
        lines.append(f"- {SYMPTOMS[t['symptom']]}? {ans}  ({pts})")

    lines.append("\n=== 4. REASONING ===")
    yes = [f"{t['weight']}" for t in result["trace"] if t["answer"]]
    total = " + ".join(yes) if yes else "0"
    lines.append(f"Certainty = {total} = {result['certainty']}%")
    lines.append(_STOP_TEXT[result["stopped_reason"]])
    lines.append(f"Why this rule: {result['explanation']}")
    lines.append(f"Sources: {', '.join(result['sources'])}")

    lines.append("\n=== 5. FINAL CONCLUSION ===")
    verdict = "CONFIRMED" if result["conclusion"] else "NOT CONFIRMED"
    lines.append(f"{result['disease_name']}: {verdict} ({result['certainty']}% certainty)")
    if result["conclusion"]:
        lines.append(f"Advice: {result['recommendation']}")

    lines.append("\n=== SOURCES CITED ===")
    for sid in result["sources"]:
        s = SOURCES[sid]
        lines.append(f"{sid}: {s['title']} - {s['publisher']} - {s['url']}")
    return "\n".join(lines)


# =====================================================================
# Quick self-test / demo
# =====================================================================
if __name__ == "__main__":
    print(">>> FORWARD CHAINING DEMO")
    fwd = forward_chain({"sneezing", "nasal_discharge", "eye_discharge", "lethargy"})
    print(explain_forward(fwd))

    print("\n\n>>> BACKWARD CHAINING DEMO (hypothesis: ear_mites)")
    scripted_answers = {"head_shaking": True, "ear_discharge": True, "itching": False}

    def demo_ask(symptom, description):
        answer = scripted_answers.get(symptom, False)
        print(f"  Q: {description} ({symptom})? -> {'yes' if answer else 'no'}")
        return answer

    print(explain_backward(backward_chain("ear_mites", demo_ask)))