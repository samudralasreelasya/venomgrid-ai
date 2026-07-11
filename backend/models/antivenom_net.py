"""
AntiVenomNet — Module 3 (the strongest idea)

Given a patient location and severity, recommends the best hospital
considering distance, current antivenom stock, and hospital capacity.
Also predicts which hospitals are at risk of running out soon, based
on a simple burn-rate model (stock / daily_usage_rate).

NOTE: hospital stock data used here is simulated for the demo. In
production this would be a live feed from a hospital inventory system.
"""
import math


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def days_until_stockout(stock: float, daily_usage_rate: float) -> float:
    if daily_usage_rate <= 0:
        return float("inf")
    return round(stock / daily_usage_rate, 1)


def recommend_hospital(patient_lat, patient_lon, severity_label, hospitals):
    """
    hospitals: list of dicts with keys hospital_id, name, lat, lon,
               antivenom_stock, daily_usage_rate, capacity
    Returns the best hospital plus a ranked list with distance and stock-risk info.
    """
    candidates = []
    for h in hospitals:
        dist = haversine_km(patient_lat, patient_lon, h["lat"], h["lon"])
        stockout_days = days_until_stockout(h["antivenom_stock"], h["daily_usage_rate"])

        # Disqualify hospitals with zero stock for Critical cases
        viable = not (severity_label == "Critical" and h["antivenom_stock"] <= 0)

        # Simple weighted score: prioritize distance, penalize low stock
        stock_penalty = 0 if h["antivenom_stock"] > 5 else (5 - h["antivenom_stock"]) * 2
        composite_score = dist + stock_penalty

        candidates.append({
            **h,
            "distance_km": round(dist, 1),
            "stockout_days": stockout_days,
            "at_risk_of_shortage": stockout_days <= 3,
            "viable": viable,
            "composite_score": composite_score,
        })

    ranked = sorted(
        [c for c in candidates if c["viable"]],
        key=lambda c: c["composite_score"],
    )

    best = ranked[0] if ranked else None
    return {"recommended": best, "ranked": ranked}


def suggest_redistribution(hospitals):
    """
    Flags hospitals at risk of stockout and suggests which
    well-stocked nearby hospital could transfer stock to them.
    """
    at_risk = [h for h in hospitals if days_until_stockout(h["antivenom_stock"], h["daily_usage_rate"]) <= 3]
    surplus = [h for h in hospitals if days_until_stockout(h["antivenom_stock"], h["daily_usage_rate"]) > 7]

    suggestions = []
    for low in at_risk:
        nearest_surplus = None
        best_dist = float("inf")
        for high in surplus:
            d = haversine_km(low["lat"], low["lon"], high["lat"], high["lon"])
            if d < best_dist:
                best_dist = d
                nearest_surplus = high

        if nearest_surplus:
            suggestions.append({
                "from_hospital": nearest_surplus["name"],
                "to_hospital": low["name"],
                "distance_km": round(best_dist, 1),
                "suggested_units": 5,
            })

    return suggestions
