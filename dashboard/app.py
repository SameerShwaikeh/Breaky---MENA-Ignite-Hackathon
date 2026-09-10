import streamlit as st
import requests

st.set_page_config(page_title="Breaky Dashboard", layout="wide")

st.title("🚨 Breaky — Early Epidemic Warning System")
st.caption("Live Health Intelligence & CAMARA Verification Feed")

# Sidebar - API Server Status
st.sidebar.header("System Status")
try:
    res = requests.get("http://127.0.0.1:8000/health", timeout=2)
    if res.status_code == 200:
        st.sidebar.success("Backend API: Online")
    else:
        st.sidebar.warning("Backend API: Degraded")
except Exception:
    st.sidebar.error("Backend API: Offline")

# Main Layout Scaffolding
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Live Anomaly Metrics & Outbreak Curve")
    st.info("Chart placeholder — Connecting to backend /aggregate endpoints...")

with col2:
    st.subheader("🔔 Real-Time Agent Alerts")
    st.info("Alert feed placeholder — Listening for triggered agent alerts...")