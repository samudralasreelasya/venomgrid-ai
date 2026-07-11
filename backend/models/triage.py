"""
Smart Triage AI — Module 2

For the hackathon prototype this is a transparent rule-based scorer.
Swap `score_from_symptoms` for a trained classifier later if you get
labeled clinical data (keep the same function signature so nothing
else in the app has to change).
"""

CRITICAL_SIGNS = {
    "difficulty_breathing",
    "drooping_eyelids",
    "slurred_speech",
    "bleeding_gums",
    "no_urine_output",
    "seizure",
}

HIGH_SIGNS = {
    "severe_swelling",
    "blistering",
    "vomiting",
    "dizziness",
    "blurred_vision",
}

MODERATE_SIGNS = {
    "local_pain",
    "mild_swelling",
    "redness",
    "puncture_marks",
}


def score_from_symptoms(symptoms: list[str], time_since_bite_minutes: int = 0) -> dict:
    """
    symptoms: list of symptom tags selected in the UI, e.g.
        ["severe_swelling", "vomiting"]
    time_since_bite_minutes: how long ago the bite occurred

    Returns: {"score": float 0-1, "label": "Critical"/"High"/"Moderate", "reasons": [...]}
    """
    symptoms = set(symptoms)
    reasons = []

    score = 0.0

    critical_hits = symptoms & CRITICAL_SIGNS
    high_hits = symptoms & HIGH_SIGNS
    moderate_hits = symptoms & MODERATE_SIGNS

    if critical_hits:
        score += 0.6 + 0.1 * min(len(critical_hits), 3)
        reasons.append(f"Critical signs present: {', '.join(sorted(critical_hits))}")

    if high_hits:
        score += 0.15 * min(len(high_hits), 3)
        reasons.append(f"High-severity signs: {', '.join(sorted(high_hits))}")

    if moderate_hits and not critical_hits:
        score += 0.05 * min(len(moderate_hits), 3)
        reasons.append(f"Moderate signs: {', '.join(sorted(moderate_hits))}")

    # Time decay factor: longer since bite without treatment raises urgency
    if time_since_bite_minutes >= 60:
        score += 0.15
        reasons.append("More than 60 minutes since bite — urgency increased")
    elif time_since_bite_minutes >= 30:
        score += 0.05
        reasons.append("30-60 minutes since bite")

    score = min(score, 1.0)

    if score >= 0.6:
        label = "Critical"
    elif score >= 0.3:
        label = "High"
    else:
        label = "Moderate"

    return {"score": round(score, 2), "label": label, "reasons": reasons}
