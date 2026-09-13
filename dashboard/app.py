import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# Page Setup
st.set_page_config(
    page_title="Breaky: Pandemic Intelligence System",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_URL = "http://127.0.0.1:8000"

# Custom CSS matching the screenshot UI design
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #FFFFFF; }
    
    /* Top Metric Card Styling */
    .kpi-card {
        background-color: #121824;
        border: 1px solid #1F293D;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 10px;
    }
    .kpi-title { color: #8B949E; font-size: 0.85rem; font-weight: 500; }
    .kpi-value { font-size: 1.8rem; font-weight: bold; margin: 4px 0; }
    .kpi-tag-green {
        background-color: #0E3A2F; color: #34D399; font-size: 0.75rem; 
        padding: 2px 8px; border-radius: 4px; font-weight: 600; display: inline-block;
    }
    .kpi-tag-red {
        background-color: #4A151B; color: #F87171; font-size: 0.75rem; 
        padding: 2px 8px; border-radius: 4px; font-weight: 600; display: inline-block;
    }
    
    /* Threat Cards (Left Feed) */
    .threat-banner {
        background-color: #4A1D24;
        color: #F87171;
        font-weight: bold;
        padding: 10px 14px;
        border-radius: 6px 6px 0 0;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
    }
    .threat-body {
        background-color: #121824;
        border: 1px solid #2A1D24;
        border-top: none;
        padding: 12px 14px;
        border-radius: 0 0 6px 6px;
        margin-bottom: 16px;
    }
    .protocol-btn {
        background-color: #161F30;
        border: 1px solid #2B3954;
        color: #E2E8F0;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 8px;
        display: block;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Helper Data Functions
def fetch_outbreaks():
    try:
        r = requests.get(f"{BASE_URL}/outbreak-data", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    # Fallback demo data
    return [
        {"id": 1, "location": "Gaza", "lat": 31.5017, "lon": 34.4668, "agent": "Influenza-A", "risk_level": "PANDEMIC THREAT", "protocol": "Activate Quarantine Protocol: Gaza", "needed_supplies": "Tamiflu, N95 Masks, Oxygen Cylinders", "cases": 142},
        {"id": 2, "location": "Hebron", "lat": 31.5326, "lon": 35.0998, "agent": "Hepatitis", "risk_level": "PANDEMIC THREAT", "protocol": "Activate Quarantine Protocol: Hebron", "needed_supplies": "Oral Rehydration Salts (ORS), Clean Water Filters", "cases": 98},
        {"id": 3, "location": "Nablus", "lat": 32.2211, "lon": 35.2544, "agent": "Meningitis", "risk_level": "PANDEMIC THREAT", "protocol": "Activate Quarantine Protocol: Nablus", "needed_supplies": "Ceftriaxone, Antibiotics", "cases": 64},
        {"id": 4, "location": "Bethlehem", "lat": 31.7057, "lon": 35.2024, "agent": "Covid-19", "risk_level": "PANDEMIC THREAT", "protocol": "Activate Quarantine Protocol: Bethlehem", "needed_supplies": "Rapid Antigen Kits, Surgical Masks", "cases": 41}
    ]

def fetch_warehouses():
    try:
        r = requests.get(f"{BASE_URL}/warehouses", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return [
        {"warehouse": "Gaza Central Medical Depot", "city": "Gaza", "item": "Tamiflu (Oseltamivir)", "available": 85, "required": 500, "status": "CRITICAL SHORTAGE"},
        {"warehouse": "Hebron Regional Warehouse", "city": "Hebron", "item": "Oral Rehydration Salts (ORS)", "available": 120, "required": 1000, "status": "LOW STOCK"},
        {"warehouse": "Hebron Regional Warehouse", "city": "Hebron", "item": "Normal Saline IV (1L)", "available": 450, "required": 1200, "status": "LOW STOCK"},
        {"warehouse": "Nablus Northern Depot", "city": "Nablus", "item": "Ceftriaxone Injectable", "available": 310, "required": 800, "status": "LOW STOCK"},
        {"warehouse": "Ramallah Central Depot", "city": "Ramallah", "item": "Personal Protective Equipment", "available": 4500, "required": 5000, "status": "SUFFICIENT"}
    ]

# Title & Subtitle
st.title("Breaky: Pandemic Intelligence System")
st.caption("AI-powered surveillance focusing on infectious diseases and outbreak prevention.")

# Top KPI Metric Cards
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

with kpi_col1:
    st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">Connected Centers</div>
            <div class="kpi-value" style="color: #60A5FA;">9 Units</div>
            <div class="kpi-tag-green">↑ Live Feed</div>
        </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">Pandemic Risk Level</div>
            <div class="kpi-value" style="color: #93C5FD;">High Alert</div>
            <div class="kpi-tag-red">↑ Contagious Surge</div>
        </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">AI Screening Status</div>
            <div class="kpi-value" style="color: #60A5FA;">Active</div>
            <div class="kpi-tag-green">↑ Filtering 24/7</div>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# Fetch Active Outbreaks & Warehouse Data
outbreaks = fetch_outbreaks()
warehouses = fetch_warehouses()
df_outbreaks = pd.DataFrame(outbreaks)

# Main 2-Column Section (Alerts Left | Map Right)
col_alerts, col_map = st.columns([1, 1.8])

with col_alerts:
    st.markdown("### 🛡️ AI Outbreak Alerts")
    st.caption("Monitoring contagious clusters only.")
    
    for item in outbreaks:
        loc = item["location"]
        agent = item["agent"]
        protocol = item["protocol"]
        
        st.markdown(f"""
            <div class="threat-banner">PANDEMIC THREAT: {loc.upper()}</div>
            <div class="threat-body">
                <div style="color: #8B949E; font-size: 0.85rem;">Infectious Agent: <strong style="color: #FFFFFF;">{agent}</strong></div>
                <div class="protocol-btn">{protocol}</div>
            </div>
        """, unsafe_allow_html=True)

with col_map:
    st.markdown("### Infectious Disease Spread Map")
    st.caption("💡 *Hover over or click any point on the map to inspect needed supplies and outbreak metrics.*")
    
    # Custom hover formatting with Warehouse Stock Status removed
    fig_map = px.scatter_mapbox(
        df_outbreaks,
        lat="lat",
        lon="lon",
        size="cases",
        color="agent",
        hover_name="location",
        hover_data={
            "agent": True,
            "risk_level": True,
            "needed_supplies": True,
            "cases": True,
            "lat": False,
            "lon": False
        },
        labels={
            "agent": "Infectious Agent",
            "risk_level": "Threat Level",
            "needed_supplies": "Required Supplies",
            "cases": "Active Cases"
        },
        zoom=7.8,
        center={"lat": 31.8, "lon": 35.1},
        height=520
    )
    
    fig_map.update_traces(
        marker=dict(sizemin=14),
        hovertemplate="<b>%{hovertext} Region</b><br><br>" +
                      "<b>Infectious Agent:</b> %{customdata[0]}<br>" +
                      "<b>Threat Level:</b> %{customdata[1]}<br>" +
                      "<b>Required Supplies:</b> %{customdata[2]}<br>" +
                      "<b>Recorded Cases:</b> %{customdata[3]}<extra></extra>"
    )
    
    fig_map.update_layout(
        mapbox_style="carto-darkmatter",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(title="Outbreak Agent", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# Lower Section: Warehouse Stock Table & Proactive Response Plan
col_wh_table, col_plan_detail = st.columns([1.5, 1])

with col_wh_table:
    st.markdown("### 📦 Warehouse Telemetry & Stock Cautions")
    st.caption("Live monitoring of essential medication and medical supply reserves across regional depots.")
    
    wh_df = pd.DataFrame(warehouses)
    
    st.dataframe(
        wh_df,
        column_config={
            "warehouse": "Warehouse Facility",
            "city": "Region",
            "item": "Supply / Medication",
            "available": st.column_config.NumberColumn("In Stock", format="%d units"),
            "required": st.column_config.NumberColumn("Required Reserve", format="%d units"),
            "status": st.column_config.TextColumn("Caution Level")
        },
        hide_index=True,
        use_container_width=True
    )

with col_plan_detail:
    st.markdown("### 📋 Proactive Response Action Plan")
    st.caption("Automated mitigation instructions generated by AI agents based on current warehouse levels.")
    
    st.markdown("""
        <div style="background-color: #121824; border: 1px solid #1F293D; padding: 14px; border-radius: 6px;">
            <div style="color: #F87171; font-weight: bold; margin-bottom: 6px;">⚠️ Action Required: Gaza & Hebron Shortage</div>
            <ul style="color: #CBD5E1; font-size: 0.88rem; padding-left: 18px; margin-bottom: 0;">
                <li style="margin-bottom: 6px;"><strong>Dispatch Emergency Logistics:</strong> Transfer 400 Tamiflu packs from Ramallah Depot to Gaza Central.</li>
                <li style="margin-bottom: 6px;"><strong>Water Sanitation Protocols:</strong> Deploy municipal water testing kits to Hebron primary centers.</li>
                <li><strong>Quarantine Mobilization:</strong> Establish isolation triage tents at Nablus and Gaza entry points.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)