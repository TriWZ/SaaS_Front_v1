import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Triphorium SaaS V4", layout="wide")
st.title("Triphorium SaaS Energy Dashboard")

st.sidebar.header("User Login")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")
token = None

if st.sidebar.button("Login"):
    res = requests.post("http://localhost:8000/auth/login", json={"email": email, "password": password})
    if res.status_code == 200:
        token = res.json()["access_token"]
        st.session_state["token"] = token
        st.success("Login successful")
    else:
        st.error("Invalid login")

if "token" in st.session_state:
    st.success("Authenticated. You can now query building data.")
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    user_id = 1  # hardcoded for demo; should decode from token
    res = requests.get(f"http://localhost:8000/buildings/list/{user_id}")
    buildings = res.json()
    building_names = [b['name'] for b in buildings]
    building_ids = [b['id'] for b in buildings]
    selected = st.selectbox("Select Building", building_names)
    b_id = building_ids[building_names.index(selected)]

    st.subheader("📊 Energy KPI + Trends")
    hist = requests.get(f"http://localhost:8000/energy/history/{b_id}").json()
    if hist:
        df = pd.DataFrame(hist)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Electricity", f"{df['electricity_kwh'].sum():,.0f} kWh")
        k2.metric("Water", f"{df['water_tons'].sum():,.0f} tons")
        k3.metric("Gas", f"{df['gas_m3'].sum():,.0f} m3")
        k4.metric("CO2", f"{df['co2_tons'].sum():.1f} tons")

        st.plotly_chart(px.line(df, x="timestamp", y="electricity_kwh", title="Electricity Trend"), use_container_width=True)
        st.plotly_chart(px.line(df, x="timestamp", y="co2_tons", title="CO2 Emissions"), use_container_width=True)

        st.subheader("🧠 Strategy Suggestions + Feedback")
        avg = df['electricity_kwh'].mean()
        suggestion = ""
        if avg > 14000:
            suggestion = "Consider HVAC optimization and LED upgrades."
        elif avg > 12000:
            suggestion = "Performance acceptable, but lighting audit may help."
        else:
            suggestion = "Energy use is within optimal range."

        st.write(suggestion)
        accept = st.checkbox("I will implement this suggestion")

        if st.button("Submit Feedback"):
            payload = {
                "building_id": b_id,
                "user_id": user_id,
                "strategy_text": suggestion,
                "accepted": accept
            }
            r = requests.post("http://localhost:8000/feedback/add", json=payload)
            if r.status_code == 200:
                st.success("Feedback submitted.")
            else:
                st.error("Failed to submit feedback.")