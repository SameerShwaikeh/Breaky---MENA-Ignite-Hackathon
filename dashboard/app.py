import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# Page Setup
st.set_page_config(
    page_title="Breaky — Early Epidemic Warning System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration - Hardcoded to loopback
BASE_URL = "http://127.0.0.1:8000"

# Custom Styling
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .badge-outbreak {
        background-color: #7D1212;
        color: #FFD1D1;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-warning {
        background-color: #7D5A12;
        color: #FFEAA7;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

# Data Fetching Functions
def get_backend_health():
    try:
        r = requests.get(f"{BASE_URL}/alerts/latest", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def get_alerts():
    try:
        r = requests.get(f"{BASE_URL}/alerts/latest", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

# Sidebar Controls
st.sidebar.title("System Controls")
is_online = get_backend_health()
if is_online:
    st.sidebar.success("Backend API: Online")
else:
    st.sidebar.error("Backend API: Offline")

st.sidebar.divider()
st.sidebar.subheader("Filter Live Data")
selected_risk = st.sidebar.multiselect(
    "Filter by Risk Level", 
    options=["OUTBREAK", "WARNING", "EVALUATE", "TRIGGERED"], 
    default=["OUTBREAK", "WARNING", "TRIGGERED"]
)

# Main Dashboard Header
st.title("Breaky — Early Epidemic Warning System")
st.caption("Real-Time Epidemiological Intelligence & Automated Surveillance Engine")
st.divider()

# Load API Data
alerts_data = get_alerts()
alerts_df = pd.DataFrame(alerts_data)

# KPI Summary Bar
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_alerts = len(alerts_df) if not alerts_df.empty else 0
outbreak_count = 0
if not alerts_df.empty:
    if 'risk_level' in alerts_df.columns:
        outbreak_count = len(alerts_df[alerts_df['risk_level'] == 'OUTBREAK'])
    elif 'status' in alerts_df.columns:
        outbreak_count = len(alerts_df[alerts_df['status'] == 'TRIGGERED'])

with kpi1:
    st.metric("Total Active Alerts", total_alerts)
with kpi2:
    st.metric("Outbreak Triggers", outbreak_count)
with kpi3:
    st.metric("Monitored Facilities", "12 Centers")
with kpi4:
    st.metric("System Status", "ACTIVE" if is_online else "DISCONNECTED")

st.divider()

# Main Visual Split
col_main, col_feed = st.columns([1.7, 1])

with col_main:
    st.subheader("Geospatial Surveillance Map")
    
    facility_coords = {
        "Nablus Medical Center": {"lat": 32.2211, "lon": 35.2544},
        "Hebron Medical Center": {"lat": 31.5326, "lon": 35.0998},
        "Ramallah Medical Center": {"lat": 31.9038, "lon": 35.2034},
        "Ramallah Central Hospital": {"lat": 31.9038, "lon": 35.2034},
        "Jenin Specialty Hospital": {"lat": 32.4590, "lon": 35.2954},
        "Gaza Primary Health": {"lat": 31.5017, "lon": 34.4668}
    }
    
    map_rows = []
    if not alerts_df.empty:
        for idx, row in alerts_df.iterrows():
            fac = row.get('facility', row.get('location', 'Ramallah Central Hospital'))
            coords = facility_coords.get(fac, {"lat": 31.9038, "lon": 35.2034})
            map_rows.append({
                "facility": fac,
                "lat": coords["lat"],
                "lon": coords["lon"],
                "risk": row.get('risk_level', row.get('status', 'TRIGGERED')),
                "syndrome": row.get('syndrome_code', row.get('syndrome', 'ILI')),
                "z_score": max(abs(row.get('z_score', row.get('anomaly_score', 1.0))) * 8, 12)
            })
    else:
        for fac, coords in facility_coords.items():
            map_rows.append({"facility": fac, "lat": coords["lat"], "lon": coords["lon"], "risk": "NORMAL", "syndrome": "NONE", "z_score": 10})

    geo_df = pd.DataFrame(map_rows)
    
    fig_map = px.scatter_mapbox(
        geo_df,
        lat="lat",
        lon="lon",
        size="z_score",
        color="risk",
        hover_name="facility",
        hover_data=["syndrome"],
        color_discrete_map={"OUTBREAK": "#FF4B4B", "TRIGGERED": "#FF4B4B", "WARNING": "#FFAA00", "NORMAL": "#00CC96", "EVALUATE": "#1E90FF"},
        zoom=7.8,
        center={"lat": 31.9, "lon": 35.2},
        height=360
    )
    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.subheader("Syndrome Density Heatmap")
    
    if not alerts_df.empty and 'syndrome_code' in alerts_df.columns and 'facility' in alerts_df.columns:
        heatmap_data = pd.crosstab(
            alerts_df['facility'],
            alerts_df['syndrome_code']
        )
        fig_heat = px.imshow(
            heatmap_data,
            color_continuous_scale="Reds",
            aspect="auto",
            height=280
        )
    else:
        fig_heat = px.imshow(
            [[12, 4, 2], [5, 18, 1], [2, 8, 15]],
            x=['ILI', 'GASTRO', 'FEVER'],
            y=['Nablus MC', 'Ramallah MC', 'Hebron MC'],
            color_continuous_scale="Reds",
            aspect="auto",
            height=280
        )
        
    fig_heat.update_layout(
        margin={"r": 0, "t": 20, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with col_feed:
    st.subheader("Live Agent Alert Log")
    
    if not alerts_df.empty:
        for idx, row in alerts_df.iterrows():
            risk = row.get('risk_level', row.get('status', 'TRIGGERED'))
            border_color = "#FF4B4B" if risk in ["OUTBREAK", "TRIGGERED"] else "#FFAA00"
            badge_class = "badge-outbreak" if risk in ["OUTBREAK", "TRIGGERED"] else "badge-warning"
            
            syndrome = row.get('syndrome_code', row.get('syndrome', 'UNKNOWN_SYNDROME'))
            score = row.get('z_score', row.get('anomaly_score', 0.0))
            alert_id = row.get('id', idx + 1)
            
            st.markdown(f"""
                <div style="background-color: #161B22; border-left: 4px solid {border_color}; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="{badge_class}">{risk}</span>
                        <small style="color: #8B949E;">Alert #{alert_id}</small>
                    </div>
                    <div style="margin-top: 8px;">
                        <strong style="font-size: 1.05rem;">{syndrome}</strong>
                    </div>
                    <div style="color: #8B949E; font-size: 0.85rem; margin-top: 4px;">
                        Score: <code style="color: #58A6FF;">{score:.2f}</code>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active outbreak signals returned from API.")