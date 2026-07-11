from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from db import get_connection  # noqa: E402
from models.triage import score_from_symptoms  # noqa: E402
from models.antivenom_net import recommend_hospital, suggest_redistribution  # noqa: E402
from models.risk_ai import rank_villages  # noqa: E402

app = Flask(__name__)
CORS(app)


def fetch_hospitals():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM hospitals").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_villages():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM villages").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.route("/api/risk", methods=["GET"])
def risk():
    villages = fetch_villages()
    ranked = rank_villages(villages)
    return jsonify(ranked)


@app.route("/api/hospitals", methods=["GET"])
def hospitals():
    return jsonify(fetch_hospitals())


@app.route("/api/redistribution", methods=["GET"])
def redistribution():
    return jsonify(suggest_redistribution(fetch_hospitals()))


@app.route("/api/triage", methods=["POST"])
def triage():
    body = request.get_json(force=True)
    symptoms = body.get("symptoms", [])
    time_since_bite = body.get("time_since_bite_minutes", 0)
    result = score_from_symptoms(symptoms, time_since_bite)
    return jsonify(result)


@app.route("/api/report_case", methods=["POST"])
def report_case():
    """
    Full pipeline: score severity, recommend hospital, log the case.
    Expects: village, lat, lon, symptoms, time_since_bite_minutes
    """
    body = request.get_json(force=True)
    village = body.get("village", "Unknown")
    lat = body["lat"]
    lon = body["lon"]
    symptoms = body.get("symptoms", [])
    time_since_bite = body.get("time_since_bite_minutes", 0)

    triage_result = score_from_symptoms(symptoms, time_since_bite)
    routing = recommend_hospital(lat, lon, triage_result["label"], fetch_hospitals())
    best = routing["recommended"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO cases
           (reported_at, village, symptoms, severity_score, severity_label, assigned_hospital, status)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.utcnow().isoformat(),
            village,
            ",".join(symptoms),
            triage_result["score"],
            triage_result["label"],
            best["name"] if best else None,
            "Routed" if best else "No hospital available",
        ),
    )
    conn.commit()
    case_id = cur.lastrowid
    conn.close()

    return jsonify({
        "case_id": case_id,
        "triage": triage_result,
        "routing": routing,
    })


@app.route("/api/cases", methods=["GET"])
def cases():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM cases ORDER BY case_id DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
