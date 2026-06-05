import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from groq import Groq
import time
import os

# Page configurations
st.set_page_config(
    page_title="SmartEdge AI – Industrial Predictive Maintenance & Troubleshooting Copilot",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("style.css not found. UI might load without custom telemetry styling.")

# Initialize session states
if 'temp' not in st.session_state:
    st.session_state.temp = 65.4
if 'vibration' not in st.session_state:
    st.session_state.vibration = 1.2
if 'pressure' not in st.session_state:
    st.session_state.pressure = 4.1
if 'rpm' not in st.session_state:
    st.session_state.rpm = 1500
if 'custom_sliders_active' not in st.session_state:
    st.session_state.custom_sliders_active = False
if 'scenario' not in st.session_state:
    st.session_state.scenario = "Normal Operating Condition"
if 'prev_scenario' not in st.session_state:
    st.session_state.prev_scenario = ""
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = ""
if 'auto_diagnosis_response' not in st.session_state:
    st.session_state.auto_diagnosis_response = ""
if 'chat_query' not in st.session_state:
    st.session_state.chat_query = ""

# API Key and Client initialization
# Retrieve the Groq API key from Streamlit secrets
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ Error: GROQ_API_KEY not found in .streamlit/secrets.toml")
    st.info("Please configure your Groq API key in `.streamlit/secrets.toml`:\n\nGROQ_API_KEY = 'your_api_key_here'")
    st.stop()

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
groq_client = Groq(api_key=GROQ_API_KEY)

# Helper function to reset values based on scenario
def set_scenario_values(scenario_name):
    st.session_state.scenario = scenario_name
    if scenario_name == "Normal Operating Condition":
        st.session_state.temp = 65.4
        st.session_state.vibration = 1.2
        st.session_state.pressure = 4.1
        st.session_state.rpm = 1500
        st.session_state.custom_sliders_active = False
    elif scenario_name == "Overheating Machine Simulation":
        st.session_state.temp = 98.7
        st.session_state.vibration = 2.1
        st.session_state.pressure = 3.8
        st.session_state.rpm = 1800
        st.session_state.custom_sliders_active = False
    elif scenario_name == "High Vibration Failure Case":
        st.session_state.temp = 72.3
        st.session_state.vibration = 6.8
        st.session_state.pressure = 4.0
        st.session_state.rpm = 2250
        st.session_state.custom_sliders_active = False
    elif scenario_name == "Low Pressure Warning Scenario":
        st.session_state.temp = 60.1
        st.session_state.vibration = 1.5
        st.session_state.pressure = 1.7
        st.session_state.rpm = 1220
        st.session_state.custom_sliders_active = False

# Sidebar styling & components
st.sidebar.markdown(
    """
    <div style='text-align: center; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 15px;'>
        <h2 style='font-family: "Rajdhani", sans-serif; font-weight: 700; color: #38bdf8; margin: 0; font-size: 1.5rem;'>
            ⚙️ CONTROL PANEL
        </h2>
        <span style='font-size: 0.75rem; color: #64748b;'>Edge AI Diagnostics Node</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar Inputs
machine_type = st.sidebar.selectbox(
    "Target Equipment Profile",
    [
        "CNC Milling Center (Model X3)",
        "Industrial Conveyor Belt (System 7)",
        "Heavy Gas Turbine (GT-9000)",
        "Hydraulic Excavator (HEX-350)",
        "Centrifugal Water Pump (CP-5)"
    ]
)

detection_sensitivity = st.sidebar.selectbox(
    "Edge Detection Sensitivity",
    [
        "Low Sensitivity (Relaxed)",
        "Medium Sensitivity (Standard)",
        "High Sensitivity (Strict)"
    ],
    index=1
)

st.sidebar.markdown("---")

scenario_selection = st.sidebar.selectbox(
    "Simulation Scenario Presets",
    [
        "Normal Operating Condition",
        "Overheating Machine Simulation",
        "High Vibration Failure Case",
        "Low Pressure Warning Scenario",
        "Custom Manual Adjustments"
    ]
)

# Handle preset updates
if scenario_selection != st.session_state.prev_scenario:
    st.session_state.prev_scenario = scenario_selection
    if scenario_selection != "Custom Manual Adjustments":
        set_scenario_values(scenario_selection)
    else:
        st.session_state.custom_sliders_active = True

# Sliders for manual adjustments if custom mode is selected
if st.session_state.custom_sliders_active or scenario_selection == "Custom Manual Adjustments":
    st.session_state.custom_sliders_active = True
    st.sidebar.markdown("#### ⚙️ Manual Telemetry Override")
    st.session_state.temp = st.sidebar.slider("Temperature (°C)", 40.0, 120.0, float(st.session_state.temp), step=0.1)
    st.session_state.vibration = st.sidebar.slider("Vibration (mm/s)", 0.5, 10.0, float(st.session_state.vibration), step=0.1)
    st.session_state.pressure = st.sidebar.slider("Pressure (bar)", 0.5, 8.0, float(st.session_state.pressure), step=0.1)
    st.session_state.rpm = st.sidebar.slider("Speed (RPM)", 500, 3000, int(st.session_state.rpm), step=50)

st.sidebar.markdown("---")

# RAG technical manual uploader
uploaded_file = st.sidebar.file_uploader(
    "Upload Equipment Manual (PDF)",
    type=["pdf"],
    help="Contextualizes AI responses with manufacturer specifications using RAG"
)

# Simulated RAG metadata state
rag_active = False
if uploaded_file is not None:
    rag_active = True
    st.sidebar.markdown(
        f"""
        <div class="alert-item alert-item-normal" style="margin-top: 10px;">
            📄 <b>Manual Loaded:</b><br>{uploaded_file.name}<br>
            <span style="font-size: 0.75rem; color: #10b981;">• Semantic index built<br>• RAG enhancement enabled</span>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown(
        """
        <div style="font-size: 0.75rem; color: #64748b; font-style: italic; margin-top: 10px; text-align: center;">
            No manual loaded. AI will diagnose issues using standard industrial best practices.
        </div>
        """,
        unsafe_allow_html=True
    )

# Sidebar System Health Status Card
st.sidebar.markdown(
    """
    <div style="border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 12px; background: rgba(15, 23, 42, 0.45); margin-top: 20px;">
        <div style="font-size:0.75rem; color:#64748b; text-transform:uppercase; font-weight:600;">Hardware Connection</div>
        <div style="display:flex; align-items:center; margin-top: 5px;">
            <span class="live-dot"></span>
            <span style="font-family:'Rajdhani', sans-serif; font-size:1rem; font-weight:700; color: #10b981;">EDGE-ACTIVE</span>
        </div>
        <div style="font-size:0.7rem; color:#475569; margin-top: 4px; font-family: monospace;">UUID: NODE-WIN-448A</div>
    </div>
    """,
    unsafe_allow_html=True
)


# Define Thresholds based on Detection Sensitivity
if detection_sensitivity == "High Sensitivity (Strict)":
    temp_thresh = 80.0
    vib_thresh = 3.5
    pres_low_thresh = 3.0
    pres_high_thresh = 6.0
    rpm_thresh = 1800
elif detection_sensitivity == "Low Sensitivity (Relaxed)":
    temp_thresh = 100.0
    vib_thresh = 6.0
    pres_low_thresh = 2.0
    pres_high_thresh = 7.0
    rpm_thresh = 2200
else:  # Medium Sensitivity (Standard)
    temp_thresh = 90.0
    vib_thresh = 4.5
    pres_low_thresh = 2.5
    pres_high_thresh = 6.5
    rpm_thresh = 2000

# Edge Anomaly Detection logic
anomalies = []
if st.session_state.temp > temp_thresh:
    is_crit = st.session_state.temp > (temp_thresh + 10.0)
    anomalies.append({
        "level": "Critical" if is_crit else "Warning",
        "msg": f"High Spindle Temp: {st.session_state.temp:.1f}°C (Limit: {temp_thresh:.1f}°C)",
        "code": "E-TEMP-04" if is_crit else "W-TEMP-04"
    })

if st.session_state.vibration > vib_thresh:
    is_crit = st.session_state.vibration > (vib_thresh + 2.0)
    anomalies.append({
        "level": "Critical" if is_crit else "Warning",
        "msg": f"Abnormal Vibration: {st.session_state.vibration:.1f} mm/s (Limit: {vib_thresh:.1f} mm/s)",
        "code": "E-VIB-12" if is_crit else "W-VIB-12"
    })

if st.session_state.pressure < pres_low_thresh:
    is_crit = st.session_state.pressure < (pres_low_thresh - 0.5)
    anomalies.append({
        "level": "Critical" if is_crit else "Warning",
        "msg": f"Low System Pressure: {st.session_state.pressure:.1f} bar (Min: {pres_low_thresh:.1f} bar)",
        "code": "E-PRES-09" if is_crit else "W-PRES-09"
    })
elif st.session_state.pressure > pres_high_thresh:
    anomalies.append({
        "level": "Warning",
        "msg": f"Overpressure Event: {st.session_state.pressure:.1f} bar (Max: {pres_high_thresh:.1f} bar)",
        "code": "W-PRES-10"
    })

if st.session_state.rpm > rpm_thresh:
    anomalies.append({
        "level": "Warning",
        "msg": f"High Rotor Speed: {st.session_state.rpm} RPM (Limit: {rpm_thresh} RPM)",
        "code": "W-RPM-02"
    })

# Compute Risk Score dynamically
base_risk = 5.0
temp_dev = max(0.0, st.session_state.temp - temp_thresh)
vib_dev = max(0.0, st.session_state.vibration - vib_thresh)
pres_dev = max(0.0, pres_low_thresh - st.session_state.pressure) if st.session_state.pressure < pres_low_thresh else max(0.0, st.session_state.pressure - pres_high_thresh)
rpm_dev = max(0.0, st.session_state.rpm - rpm_thresh)

risk_score = base_risk
if temp_dev > 0:
    risk_score += min(35.0, temp_dev * 3.5 + 15.0)
if vib_dev > 0:
    risk_score += min(40.0, vib_dev * 12.0 + 20.0)
if pres_dev > 0:
    risk_score += min(30.0, pres_dev * 25.0 + 15.0)
if rpm_dev > 0:
    risk_score += min(20.0, rpm_dev * 0.05 + 10.0)

risk_score = min(100.0, max(0.0, risk_score))
risk_score = int(round(risk_score))

# Set overall machine status
if risk_score < 30:
    health_status = "Normal"
    status_class = "badge-normal"
    status_icon = "🟢"
elif risk_score < 70:
    health_status = "Warning"
    status_class = "badge-warning"
    status_icon = "🟡"
else:
    health_status = "Critical"
    status_class = "badge-critical"
    status_icon = "🔴"

# Simulated RAG manual lookup database
def get_simulated_rag_context():
    if not rag_active:
        return ""
    
    # Specific mock contexts extracted from the PDF manual depending on active scenario
    if "overheating" in st.session_state.scenario.lower() or st.session_state.temp > temp_thresh:
        return f"""
        [RETRIEVED MANUAL CONTEXT - CNC Milling Center Model X3 Manual - Chapter 9: Thermal Management]
        - Section 9.4.1 (Spindle Cooling Loop): "If the spindle core temperature exceeds 85°C, verify fluid flow rate in the chiller line. Normal operation is 4.5 L/min. Check coolant pump filter element CF-990-2 for particle accumulation."
        - Section 9.4.5 (Thermal Warning Code W-TEMP-04): "Ensure coolant lines are not crimped. Operating the spindle above 95°C for more than 5 minutes will degrade spindle bearings (Model BA-204) and void warranty."
        - Section 12.2 (Coolant Specs): "Use only ISO VG 32 spindle cooling oil. Maintain coolant level in reservoir above 75% capacity."
        """
    elif "vibration" in st.session_state.scenario.lower() or st.session_state.vibration > vib_thresh:
        return f"""
        [RETRIEVED MANUAL CONTEXT - CNC Milling Center Model X3 Manual - Chapter 14: Mechanical Alignment]
        - Section 14.3.2 (Structural Vibration W-VIB-12): "Vibration amplitude levels above 4.0 mm/s indicate mounting bolt looseness or tool holder eccentricity. If levels exceed 6.0 mm/s (Code E-VIB-12), immediate machine trip is mandatory."
        - Section 14.6.1 (Spindle Bearing Assembly BA-204): "Ensure spindle collet drawbar retention force is at 8.5 kN. Check for chip debris inside the spindle taper. Torque mounting bolts to 120 Nm in star pattern."
        """
    elif "pressure" in st.session_state.scenario.lower() or st.session_state.pressure < pres_low_thresh:
        return f"""
        [RETRIEVED MANUAL CONTEXT - CNC Milling Center Model X3 Manual - Chapter 7: Pneumatics & Hydraulics]
        - Section 7.2.3 (Pneumatic Supply Line E-PRES-09): "Tool clamping mechanism requires minimum 3.0 bar pressure. If main supply drops below 2.5 bar, the clamp cylinder lock may slip. Inspect primary seals and check for moisture in the air dryer unit."
        - Section 7.5.8 (Pressure Regulator Valve RV-12): "Manual regulator should be rotated clockwise to increase flow pressure. Replace valve seal ring (Part SR-089) if leakage is audible."
        """
    else:
        return f"""
        [RETRIEVED MANUAL CONTEXT - CNC Milling Center Model X3 Manual - Chapter 1: Standard Operating Envelope]
        - Section 1.1 (Telemetry Benchmarks): "Optimal metrics for CNC milling are: Temperature: 50°C to 70°C; Vibration: < 2.0 mm/s; Pneumatic pressure: 3.5 to 5.0 bar; Operational Speed: 1000 to 2000 RPM."
        - Section 1.5 (Maintenance Schedule): "Lubricate spindle bearings every 500 operational hours with Mobil Velocite No. 6."
        """

# ----------------- MAIN LAYOUT RENDERING -----------------

# Dashboard Header
st.markdown(
    f"""
    <div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 15px; margin-bottom: 25px;'>
        <div>
            <h1 style='margin:0; font-family:"Rajdhani", sans-serif; font-size: 2.1rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.01em;'>
                SmartEdge AI <span style='color: #0284c7; font-weight: 500;'>– Industrial Predictive Maintenance Copilot</span>
            </h1>
            <p style='margin:3px 0 0 0; color:#64748b; font-size: 0.9rem;'>Edge Anomaly Detector & Troubleshooting Control Terminal</p>
        </div>
        <div style='display: flex; align-items: center; gap: 15px;'>
            <span class="status-badge {status_class}">{status_icon} {health_status.upper()}</span>
            <div style='text-align: right; border-left: 1px solid rgba(255,255,255,0.08); padding-left: 15px;'>
                <div style='font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>Last telemetry sync</div>
                <div style='font-family: monospace; font-size: 0.85rem; color: #38bdf8;'>{time.strftime("%H:%M:%S")}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 4 Columns for Sensor Telemetry
col1, col2, col3, col4 = st.columns(4)

# Set CSS class dynamically based on values compared to thresholds
temp_class = "value-normal" if st.session_state.temp <= temp_thresh else "value-critical" if st.session_state.temp > temp_thresh + 10.0 else "value-warning"
vibration_class = "value-normal" if st.session_state.vibration <= vib_thresh else "value-critical" if st.session_state.vibration > vib_thresh + 2.0 else "value-warning"
pressure_class = "value-normal" if pres_low_thresh <= st.session_state.pressure <= pres_high_thresh else "value-critical"
rpm_class = "value-normal" if st.session_state.rpm <= rpm_thresh else "value-warning"

col1.markdown(f"""
<div class="industrial-card">
    <div class="metric-title">🌡️ Spindle Temperature</div>
    <div class="metric-value {temp_class}">{st.session_state.temp:.1f}<span class="metric-unit">°C</span></div>
    <div style="font-size: 0.72rem; color: #475569; display: flex; justify-content: space-between; margin-top: 5px;">
        <span>LIMIT: {temp_thresh:.1f}°C</span>
        <span>STATUS: {"OK" if temp_class == "value-normal" else "HIGH"}</span>
    </div>
</div>
""", unsafe_allow_html=True)

col2.markdown(f"""
<div class="industrial-card">
    <div class="metric-title">🔊 Core Vibration</div>
    <div class="metric-value {vibration_class}">{st.session_state.vibration:.1f}<span class="metric-unit">mm/s</span></div>
    <div style="font-size: 0.72rem; color: #475569; display: flex; justify-content: space-between; margin-top: 5px;">
        <span>LIMIT: {vib_thresh:.1f} mm/s</span>
        <span>STATUS: {"OK" if vibration_class == "value-normal" else "HIGH"}</span>
    </div>
</div>
""", unsafe_allow_html=True)

col3.markdown(f"""
<div class="industrial-card">
    <div class="metric-title">💨 Pneumatic Pressure</div>
    <div class="metric-value {pressure_class}">{st.session_state.pressure:.1f}<span class="metric-unit">bar</span></div>
    <div style="font-size: 0.72rem; color: #475569; display: flex; justify-content: space-between; margin-top: 5px;">
        <span>RANGE: {pres_low_thresh:.1f} - {pres_high_thresh:.1f}</span>
        <span>STATUS: {"OK" if pressure_class == "value-normal" else "DEVIANT"}</span>
    </div>
</div>
""", unsafe_allow_html=True)

col4.markdown(f"""
<div class="industrial-card">
    <div class="metric-title">🔄 Rotor Speed</div>
    <div class="metric-value {rpm_class}">{st.session_state.rpm}<span class="metric-unit">RPM</span></div>
    <div style="font-size: 0.72rem; color: #475569; display: flex; justify-content: space-between; margin-top: 5px;">
        <span>LIMIT: {rpm_thresh} RPM</span>
        <span>STATUS: {"OK" if rpm_class == "value-normal" else "HIGH"}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sensor Refresher Block
col_ref, col_space = st.columns([1, 4])
with col_ref:
    if st.button("🔄 Refresh Live Telemetry", width="stretch"):
        st.session_state.temp += random.uniform(-0.6, 0.6)
        st.session_state.vibration = max(0.1, st.session_state.vibration + random.uniform(-0.1, 0.1))
        st.session_state.pressure = max(0.1, st.session_state.pressure + random.uniform(-0.08, 0.08))
        st.session_state.rpm = int(max(0, st.session_state.rpm + random.randint(-25, 25)))
        st.rerun()

st.write("")

# ----------------- HEALTH OVERVIEW & ANOMALY LOGS -----------------
mid_left, mid_right = st.columns([1, 1])

with mid_left:
    with st.container(border=True):
        st.markdown('<div class="metric-title">🧠 Machine Health & Risk Assessment</div>', unsafe_allow_html=True)
        
        # Plotly Risk Score circular gauge
        gauge_color = "#10b981" if risk_score < 30 else "#f59e0b" if risk_score < 70 else "#ef4444"
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = risk_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'family': 'Rajdhani', 'size': 11}},
                'bar': {'color': gauge_color},
                'bgcolor': "rgba(30, 41, 59, 0.2)",
                'borderwidth': 1,
                'bordercolor': "rgba(255,255,255,0.05)",
                'steps': [
                    {'range': [0, 30], 'color': 'rgba(16, 185, 129, 0.02)'},
                    {'range': [30, 70], 'color': 'rgba(245, 158, 11, 0.02)'},
                    {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.02)'}
                ],
                'threshold': {
                    'line': {'color': "#ef4444", 'width': 2},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "#f8fafc", 'family': "Orbitron"},
            height=180,
            margin=dict(l=15, r=15, t=15, b=5)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Human readable status text
        if health_status == "Normal":
            st.markdown(
                """
                <div style="font-size:0.85rem; color:#86efac; background: rgba(22, 163, 74, 0.06); padding: 10px; border-radius: 6px; border: 1px dashed rgba(22, 163, 74, 0.2); text-align: center;">
                    ✅ <b>TELEMETRY NOMINAL:</b> Equipment running within normal design limits. No action required.
                </div>
                """,
                unsafe_allow_html=True
            )
        elif health_status == "Warning":
            st.markdown(
                """
                <div style="font-size:0.85rem; color:#fde047; background: rgba(202, 138, 4, 0.06); padding: 10px; border-radius: 6px; border: 1px dashed rgba(202, 138, 4, 0.25); text-align: center;">
                    ⚠️ <b>TELEMETRY DEVIATION:</b> Edge detection warns of operational drift. Monitor closely.
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="font-size:0.85rem; color:#fca5a5; background: rgba(220, 38, 38, 0.08); padding: 10px; border-radius: 6px; border: 1px solid rgba(220, 38, 38, 0.25); text-align: center; animation: glow-red 1.5s infinite alternate;">
                    🚨 <b>CRITICAL SYSTEM ALERT:</b> Equipment risk factor exceeds safety limits. Inspect immediately.
                </div>
                """,
                unsafe_allow_html=True
            )

with mid_right:
    with st.container(border=True):
        st.markdown('<div class="metric-title">🚨 Edge Anomaly Detection Panel</div>', unsafe_allow_html=True)
        
        if len(anomalies) == 0:
            st.markdown(
                """
                <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:180px;">
                    <div style="font-size: 3.5rem; color: rgba(16, 185, 129, 0.15);">🟢</div>
                    <div style="color: #94a3b8; font-size: 0.9rem; margin-top: 5px; font-weight: 500;">All parameters nominal</div>
                    <div style="color: #64748b; font-size: 0.75rem; text-align: center;">Rule Engine scanning 4 metrics @ 10Hz</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown('<div style="overflow-y: auto; max-height: 200px; padding-right: 5px;">', unsafe_allow_html=True)
            for anomaly in anomalies:
                alert_style_class = "alert-item-critical" if anomaly["level"] == "Critical" else "alert-item-warning"
                badge_lbl = "CRIT" if anomaly["level"] == "Critical" else "WARN"
                st.markdown(
                    f"""
                    <div class="alert-item {alert_style_class}">
                        <div style="display:flex; justify-content:space-between; font-weight:700;">
                            <span>⚠️ [{badge_lbl}] {anomaly["code"]}</span>
                            <span>ACTIVE</span>
                        </div>
                        <div style="margin-top: 3px; color: #f8fafc; font-size: 0.85rem;">{anomaly["msg"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# ----------------- AI DIAGNOSIS & COPILOT -----------------
st.markdown(
    """
    <div class="ai-header">
        <h3>🤖 AI Diagnosis & Troubleshooting Copilot</h3>
    </div>
    """,
    unsafe_allow_html=True
)

bot_left, bot_right = st.columns([1, 1])

# Fetch Simulated RAG Context
rag_context = get_simulated_rag_context()

# Left Column: Operator Chat Terminal
with bot_left:
    with st.container(border=True):
        st.markdown('<div class="metric-title">💬 Interactive Operator Terminal</div>', unsafe_allow_html=True)
        st.write("Submit queries about current telemetry, fault codes, or operation limits.")
        
        # Predefined Quick Buttons
        st.markdown("<span style='font-size:0.75rem; color:#64748b; font-weight:600;'>QUICK INQUIRIES:</span>", unsafe_allow_html=True)
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        q_temp = btn_col1.button("🔴 Why overheating?", width="stretch")
        q_safe = btn_col2.button("🛡️ Is it safe?", width="stretch")
        q_next = btn_col3.button("🛠️ Next steps?", width="stretch")
        
        # Determine query text
        query_val = ""
        if q_temp:
            query_val = f"Why is this {machine_type} exhibiting high spindle temperatures under the current scenario?"
        elif q_safe:
            query_val = f"Is the {machine_type} safe to operate with a Risk Score of {risk_score}% and the current active warnings?"
        elif q_next:
            query_val = f"What are the immediate troubleshooting steps to resolve the active warnings on this {machine_type}?"
            
        # Text input box
        user_query = st.text_input("Operator Query Input:", value=query_val, placeholder="e.g. 'Check vibration fault safety guidelines'")
        
        submit_query = st.button("🔌 Send Query to AI Copilot", type="primary")
        
        if submit_query and user_query:
            with st.spinner("AI Copilot scanning telemetry and generating report..."):
                # System prompt formulation
                sys_prompt = f"""
                You are the SmartEdge AI Industrial Predictive Maintenance & Troubleshooting Copilot, an expert reliability engineer and master industrial technician.
                You are assisting an operator at the control terminal of a {machine_type}.

                Current Edge telemetry:
                - Temperature: {st.session_state.temp:.1f}°C (Threshold: {temp_thresh:.1f}°C)
                - Vibration: {st.session_state.vibration:.1f} mm/s (Threshold: {vib_thresh:.1f} mm/s)
                - Pressure: {st.session_state.pressure:.1f} bar (Limits: {pres_low_thresh:.1f} - {pres_high_thresh:.1f} bar)
                - Speed: {st.session_state.rpm} RPM (Limit: {rpm_thresh} RPM)
                - Overall Machine Health Status: {health_status.upper()} (Risk Score: {risk_score}/100)

                Active Edge Anomaly Alerts:
                {chr(10).join(['- [' + a['code'] + '] ' + a['msg'] for a in anomalies]) if anomalies else 'No anomalies active. System nominal.'}
                """
                
                if rag_context:
                    sys_prompt += f"\n\n{rag_context}\n\nIMPORTANT: Utilize the retrieved equipment manual context above to provide highly specific recommendations, parts, or steps where relevant. Reference manual chapters or part numbers if they are present."
                else:
                    sys_prompt += "\n\nNote: No uploaded manual context is available. Diagnose based on default manufacturer tolerances for this type of equipment."

                sys_prompt += "\n\nProvide technical, direct, and actionable guidelines. Use clean Markdown styling. Avoid chatty fluff. Speak as an automated diagnostic system."
                
                # Fetch Response
                # Helper function
                def run_query():
                    try:
                        response = groq_client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": user_query}
                            ],
                            model="llama-3.3-70b-versatile",
                            temperature=0.2,
                            max_tokens=800
                        )
                        return response.choices[0].message.content
                    except Exception as e:
                        try:
                            # Fallback model
                            response = groq_client.chat.completions.create(
                                messages=[
                                    {"role": "system", "content": sys_prompt},
                                    {"role": "user", "content": user_query}
                                ],
                                model="llama-3-8b-8192",
                                temperature=0.2,
                                max_tokens=800
                            )
                            return response.choices[0].message.content
                        except Exception as e2:
                            return f"⚠️ **Groq API Connection Failed:**\n\nFailed to establish connection to the remote LLM server. Verify your internet connection and API token.\n\n*Technical Details:* {str(e2)}"
                
                st.session_state.ai_response = run_query()
        
        # Display response if available
        if st.session_state.ai_response:
            st.markdown("---")
            st.markdown(
                f"""
                <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(56, 189, 248, 0.15); border-radius: 8px; padding: 15px; max-height: 380px; overflow-y: auto;">
                    <div style="font-size:0.75rem; color:#38bdf8; text-transform:uppercase; font-weight:700; margin-bottom:10px; display:flex; justify-content:space-between;">
                        <span>📋 AI COPILOT REPORT</span>
                        <span>RAG: {"ACTIVE" if rag_active else "INACTIVE"}</span>
                    </div>
                    <div style="font-size: 0.9rem; line-height: 1.5; color:#f1f5f9;">
                        {st.session_state.ai_response}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# Right Column: Auto-Diagnosis Feature
with bot_right:
    with st.container(border=True):
        st.markdown('<div class="metric-title">⚙️ Automated Machine Diagnosis</div>', unsafe_allow_html=True)
        st.write("Scan all active sensor metrics, compute risk matrices, and run an automated diagnostic audit to generate an operator report.")
        
        diagnose_btn = st.button("🧠 Diagnose Machine Automatically", type="secondary", width="stretch")
        
        if diagnose_btn:
            with st.spinner("Compiling telemetry logs and generating maintenance advice..."):
                sys_prompt = f"""
                You are the SmartEdge AI Industrial Predictive Maintenance & Troubleshooting Copilot, an expert reliability engineer and master industrial technician.
                You are assisting an operator at the control terminal of a {machine_type}.

                Current Edge telemetry:
                - Temperature: {st.session_state.temp:.1f}°C (Threshold: {temp_thresh:.1f}°C)
                - Vibration: {st.session_state.vibration:.1f} mm/s (Threshold: {vib_thresh:.1f} mm/s)
                - Pressure: {st.session_state.pressure:.1f} bar (Limits: {pres_low_thresh:.1f} - {pres_high_thresh:.1f} bar)
                - Speed: {st.session_state.rpm} RPM (Limit: {rpm_thresh} RPM)
                - Overall Machine Health Status: {health_status.upper()} (Risk Score: {risk_score}/100)

                Active Edge Anomaly Alerts:
                {chr(10).join(['- [' + a['code'] + '] ' + a['msg'] for a in anomalies]) if anomalies else 'No anomalies active. System nominal.'}
                """
                
                if rag_context:
                    sys_prompt += f"\n\n{rag_context}\n\nIMPORTANT: Utilize the retrieved equipment manual context above to provide highly specific recommendations, parts, or steps where relevant. Reference manual chapters or part numbers if they are present."
                else:
                    sys_prompt += "\n\nNote: No uploaded manual context is available. Diagnose based on default manufacturer tolerances."

                # Construct prompt for structured response
                auto_msg = """
                Please perform an automatic edge diagnosis of the machine.
                Analyze the current sensor deviations and active anomalies, and output a structured Maintenance & Safety Report in the following exact format:

                ### 🔍 Problem Summary
                [Provide a concise technical summary of what is happening with the machine based on telemetry]

                ### ⚙️ Possible Causes
                [Bullet points listing the most likely physical or mechanical root causes, starting with the most probable]

                ### 🛠️ Immediate Actions
                [A step-by-step checklist of what the operator on the floor must do RIGHT NOW to stabilize the machine]

                ### 🔧 Long-term Maintenance Advice
                [Preventative maintenance steps, parts to order, or inspection cycles to prevent recurrence]

                ### ⚠️ Safety Recommendations
                [Crucial safety warnings, lock-out/tag-out (LOTO) requirements, personal protective equipment (PPE), or evacuation warnings if critical]
                """
                
                def run_auto_diagnosis():
                    try:
                        response = groq_client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": auto_msg}
                            ],
                            model="llama-3.3-70b-versatile",
                            temperature=0.1,
                            max_tokens=900
                        )
                        return response.choices[0].message.content
                    except Exception as e:
                        try:
                            response = groq_client.chat.completions.create(
                                messages=[
                                    {"role": "system", "content": sys_prompt},
                                    {"role": "user", "content": auto_msg}
                                ],
                                model="llama-3-8b-8192",
                                temperature=0.1,
                                max_tokens=900
                            )
                            return response.choices[0].message.content
                        except Exception as e2:
                            return f"⚠️ **Groq API Connection Failed:**\n\nFailed to establish connection to the remote LLM server. Verify your internet connection and API token.\n\n*Technical Details:* {str(e2)}"
                            
                st.session_state.auto_diagnosis_response = run_auto_diagnosis()
                
        # Display auto diagnosis report
        if st.session_state.auto_diagnosis_response:
            st.markdown("---")
            st.markdown(
                f"""
                <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 15px; max-height: 380px; overflow-y: auto;">
                    <div style="font-size:0.75rem; color:#10b981; text-transform:uppercase; font-weight:700; margin-bottom:12px; display:flex; justify-content:space-between;">
                        <span>🧠 AUTOMATIC DIAGNOSIS REPORT</span>
                        <span>NODE SECURE</span>
                    </div>
                    <div style="font-size: 0.9rem; line-height: 1.5; color:#f8fafc;">
                        {st.session_state.auto_diagnosis_response}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:240px; border: 1px dashed rgba(255,255,255,0.05); border-radius:6px; background: rgba(30, 41, 59, 0.15);">
                    <div style="font-size: 2.5rem; color: rgba(148, 163, 184, 0.15);">📋</div>
                    <div style="color: #64748b; font-size: 0.85rem; margin-top: 5px;">No active diagnosis compile</div>
                    <div style="color: #475569; font-size: 0.72rem;">Click "Diagnose Machine Automatically" to compile logs</div>
                </div>
                """,
                unsafe_allow_html=True
            )

st.write("")

# ----------------- ADVANCED FEATURE: RAG EXPLANATORY VIEW -----------------
with st.expander("ℹ️ SmartEdge RAG Architecture & Manufacturer Manual Integration"):
    col_rag_1, col_rag_2 = st.columns([2, 1])
    
    with col_rag_1:
        st.markdown(
            """
            #### 🧬 Retrieval-Augmented Generation (RAG) in SmartEdge
            This application showcases how an edge system integrates manufacturer manuals to optimize field operations. 
            When an operator uploads a **PDF manual**, the system segments and indexes the document using vector embeddings. 
            
            1. **Query & Telemetry Parsing:** The system extracts active fault codes (e.g. `W-TEMP-04`, `E-PRES-09`) and telemetry readings.
            2. **Vector Database Retrieval:** Semantic search queries the indexed manual for safety limits, chiller specs, part numbers, and troubleshooting chapters.
            3. **Prompt Injection:** Relevant sections are dynamically injected as ground-truth context into the LLM system prompt.
            4. **Custom Diagnosis:** The AI compiles responses referencing specific part numbers (e.g. `Filter BA-204`) and precise manual sections.
            """
        )
        
    with col_rag_2:
        st.markdown(
            f"""
            <div style="border: 1px solid rgba(56, 189, 248, 0.15); border-radius: 8px; padding: 12px; background: rgba(30, 41, 59, 0.45); height: 100%;">
                <div style="font-size:0.75rem; color:#38bdf8; text-transform:uppercase; font-weight:600;">Simulated Vector Search</div>
                <div style="font-size:0.8rem; margin-top: 5px; color:#94a3b8;">
                    <b>Query:</b> <i>"Find limits & replacement elements for {machine_type} anomaly"</i>
                </div>
                <div style="font-size:0.72rem; color:#475569; margin-top: 8px;">
                    Matched Chunks: <b>{2 if rag_active else 0} chunks</b><br>
                    Similarity Threshold: <b>0.85 Cosine</b><br>
                    RAG Engine Status: <b>{"🟢 ENGAGED" if rag_active else "🔴 STANDBY"}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# Footer
st.markdown(
    """
    <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px; margin-top: 40px; text-align: center; font-size: 0.75rem; color: #475569;">
        SmartEdge AI Predictive Maintenance Copilot • Built for Hackathon Showcase • Local Edge Node Emulator v1.2
    </div>
    """,
    unsafe_allow_html=True
)
