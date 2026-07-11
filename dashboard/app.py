import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

API = "https://venomgrid-ai.onrender.com/api"
st.set_page_config(page_title="VenomGrid AI", layout="wide")
st.title("🏆 VenomGrid AI")
st.caption("Predict. Prepare. Prioritize.")

# ---------- Cached data fetchers ----------
# TTL means these only actually hit the backend once every 30s, instead of
# on every single button click across every tab (which is what was happening
# before — Streamlit reruns the whole script top-to-bottom on ANY interaction,
# so a Tab 3 click was silently re-fetching + re-rendering Tab 1 and Tab 2 too).

@st.cache_data(ttl=30)
def get_risk_data():
    return requests.get(f"{API}/risk").json()

@st.cache_data(ttl=30)
def get_hospitals():
    return requests.get(f"{API}/hospitals").json()

@st.cache_data(ttl=30)
def get_redistribution():
    return requests.get(f"{API}/redistribution").json()

@st.cache_data(ttl=15)
def get_cases():
    return requests.get(f"{API}/cases").json()


def render_as_markdown(rows, columns=None):
    """Render a list of dicts as a markdown table instead of st.table().
    Avoids the pandas/pyarrow conversion path entirely, which is what was
    causing segfaults under repeated reruns on Streamlit Cloud."""
    if not rows:
        st.info("No data to display.")
        return
    cols = columns or list(rows[0].keys())
    header = "| " + " | ".join(cols) + " |"
    divider = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines = [header, divider]
    for row in rows:
        values = [str(row.get(c, "")) for c in cols]
        lines.append("| " + " | ".join(values) + " |")
    st.markdown("\n".join(lines))


tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ RiskAI — Hotspots",
    "💉 AntiVenomNet — Stock & Routing",
    "🚑 Report a Case (Smart Triage)",
    "🩺 Digital Twin — Live Cases",
])

# ---------- Tab 1: RiskAI ----------
with tab1:
    st.subheader("Predicted snakebite risk by village")
    try:
        risk_data = get_risk_data()
    except Exception:
        st.error("Backend not reachable. Run `python backend/app.py` first.")
        risk_data = []

    if risk_data:
        # Cache the map object itself so it isn't rebuilt from scratch on
        # every rerun (e.g. clicking "Report Case" in Tab 3). Only rebuilds
        # when risk_data actually changes, since risk_data is passed in as
        # the cache key.
        @st.cache_resource(hash_funcs={list: lambda v: str(v)})
        def build_risk_map(data):
            m = folium.Map(location=[17.5, 80.0], zoom_start=8)
            color_map = {"High": "red", "Moderate": "orange", "Low": "green"}
            for v in data:
                folium.CircleMarker(
                    location=[v["lat"], v["lon"]],
                    radius=10,
                    popup=f"{v['village']} — {v['risk_tier']} ({v['risk_score']})",
                    color=color_map.get(v["risk_tier"], "blue"),
                    fill=True,
                ).add_to(m)
            return m

        m = build_risk_map(risk_data)
        st_folium(m, width=900, height=450)
        render_as_markdown(risk_data)
        st.info("Note: risk scores are computed from a simulated dataset for this demo. "
                 "In production this pulls live rainfall/vegetation data and historical case records.")

# ---------- Tab 2: AntiVenomNet ----------
with tab2:
    st.subheader("Hospital antivenom stock levels")
    try:
        hosp_data = get_hospitals()
        redist = get_redistribution()
    except Exception:
        st.error("Backend not reachable.")
        hosp_data, redist = [], []

    if hosp_data:
        render_as_markdown([
            {
                "Hospital": h["name"],
                "District": h["district"],
                "Stock": h["antivenom_stock"],
                "Daily usage": h["daily_usage_rate"],
                "Capacity": h["capacity"],
            } for h in hosp_data
        ])

    st.subheader("⚠️ Suggested stock redistribution")
    if redist:
        for r in redist:
            st.warning(f"Move {r['suggested_units']} units from **{r['from_hospital']}** "
                       f"to **{r['to_hospital']}** ({r['distance_km']} km away) before shortage hits.")
    else:
        st.success("No hospitals currently at risk of stockout.")

    st.caption("Note: hospital stock data is simulated for this demo, standing in for a future "
               "live hospital-inventory API integration.")

# ---------- Tab 3: Report a case ----------
with tab3:
    st.subheader("Simulate a reported snakebite case")

    # Reuse the cached risk_data fetched in Tab 1's block above, falling back
    # if Tab 1 hasn't populated it for some reason.
    try:
        village_options = [v["village"] for v in get_risk_data()]
    except Exception:
        village_options = ["Demo Village"]

    village = st.selectbox("Village", village_options)
    lat = st.number_input("Latitude", value=17.6, format="%.4f")
    lon = st.number_input("Longitude", value=80.0, format="%.4f")
    time_since_bite = st.slider("Minutes since bite", 0, 180, 20)

    symptom_options = [
        "local_pain", "mild_swelling", "redness", "puncture_marks",
        "severe_swelling", "blistering", "vomiting", "dizziness", "blurred_vision",
        "difficulty_breathing", "drooping_eyelids", "slurred_speech",
        "bleeding_gums", "no_urine_output", "seizure",
    ]
    symptoms = st.multiselect("Symptoms", symptom_options)

    if st.button("Report Case"):
        payload = {
            "village": village,
            "lat": lat,
            "lon": lon,
            "symptoms": symptoms,
            "time_since_bite_minutes": time_since_bite,
        }
        try:
            resp = requests.post(f"{API}/report_case", json=payload).json()
            st.success(f"Case #{resp['case_id']} — Severity: **{resp['triage']['label']}** "
                       f"(score {resp['triage']['score']})")
            for reason in resp["triage"]["reasons"]:
                st.write(f"- {reason}")

            best = resp["routing"]["recommended"]
            if best:
                st.info(f"➡️ Routed to **{best['name']}** ({best['distance_km']} km away, "
                        f"{best['antivenom_stock']} units in stock)")
            else:
                st.error("No viable hospital found with available antivenom stock.")

            # New case was reported — clear the cases cache so Tab 4 shows it
            # on next view, without forcing every other tab to also refetch.
            get_cases.clear()
        except Exception as e:
            st.error(f"Could not reach backend: {e}")

# ---------- Tab 4: Digital Twin ----------
with tab4:
    st.subheader("Live incident view")
    try:
        cases = get_cases()
    except Exception:
        st.error("Backend not reachable.")
        cases = []

    if not cases:
        st.info("No cases reported yet. Report one in the previous tab.")
    for c in cases:
        with st.container(border=True):
            st.markdown(f"**Case #{c['case_id']}** — {c['village']} — "
                        f"Severity: `{c['severity_label']}` ({c['severity_score']})")
            st.write(f"Symptoms: {c['symptoms']}")
            st.write(f"Assigned hospital: {c['assigned_hospital']}")
            st.write(f"Status: {c['status']} | Reported at: {c['reported_at']}")
