import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Breaky Dashboard", layout="wide")

st.title("🚨 Breaky — Early Epidemic Warning System")
st.caption("Live Health Intelligence & CAMARA Verification Feed")

# Sidebar Status & Controls
st.sidebar.header("System Status")
try:
    res = requests.get("http://127.0.0.1:8000/health", timeout=2)
    if res.status_code == 200:
        st.sidebar.success("Backend API: Online")
    else:
        st.sidebar.warning("Backend API: Degraded")
except Exception:
    st.sidebar.error("Backend API: Offline")

days = st.sidebar.slider("Historical Window (Days)", min_value=3, max_value=30, value=14)

# Layout Columns
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Live Anomaly Metrics & Outbreak Curve")
    try:
        agg_res = requests.get(f"http://127.0.0.1:8000/aggregate?days={days}")
        if agg_res.status_code == 200:
            data = agg_res.json()
            timeline = data.get("timeline", [])
            
            if timeline:
                df = pd.DataFrame(timeline)
                df.set_index("date", inplace=True)
                st.line_chart(df["count"])
                st.metric("Total Ingested Reports", data.get("total_reports", 0))
            else:
                st.info("No report records found for the selected timeframe.")
        else:
            st.error("Failed to fetch aggregate metrics.")
    except Exception as e:
        st.error(f"Cannot connect to /aggregate endpoint: {e}")

with col2:
    st.subheader("🔔 Real-Time Agent Alerts")
    try:
        alert_res = requests.get("http://127.0.0.1:8000/alerts/latest")
        if alert_res.status_code == 200:
            alerts = alert_res.json()
            for alert in alerts:
                with st.expander(f"⚠️ {alert['syndrome']} Outbreak Alert - {alert['location']}"):
                    st.write(f"**Anomaly Score:** {alert['anomaly_score']}")
                    st.write(f"**Status:** {alert['status']}")
                    st.write(f"**CAMARA Verification:** SIM Swap {alert['camara_verification']['sim_swap']} | Location {alert['camara_verification']['location']}")
                    st.caption(f"Time: {alert['timestamp']}")
        else:
            st.error("Failed to fetch alerts.")
    except Exception as e:
        st.error(f"Cannot connect to /alerts/latest endpoint: {e}")