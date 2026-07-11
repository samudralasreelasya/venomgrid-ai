"""
RiskAI — Module 1

For the hackathon demo this is a transparent weighted formula over
simulated weather/vegetation/history features, run once and cached —
NOT a live ML pipeline. Be upfront about this in the pitch: production
would replace `compute_risk_score` with a model trained on real IMD
rainfall data + historical snakebite records.
"""


def compute_risk_score(village: dict) -> dict:
    """
    village: dict with rainfall_mm, vegetation_index,
             historical_bites_per_year, season_factor

    Returns a 0-100 risk score and a risk tier.
    """
    rainfall_component = min(village["rainfall_mm"] / 300, 1.0) * 30
    vegetation_component = village["vegetation_index"] * 25
    history_component = min(village["historical_bites_per_year"] / 30, 1.0) * 30
    season_component = min(village["season_factor"] / 1.5, 1.0) * 15

    raw_score = rainfall_component + vegetation_component + history_component + season_component
    score = round(min(raw_score, 100), 1)

    if score >= 70:
        tier = "High"
    elif score >= 45:
        tier = "Moderate"
    else:
        tier = "Low"

    return {"risk_score": score, "risk_tier": tier}


def rank_villages(villages: list[dict]) -> list[dict]:
    scored = []
    for v in villages:
        result = compute_risk_score(v)
        scored.append({**v, **result})
    return sorted(scored, key=lambda x: x["risk_score"], reverse=True)
