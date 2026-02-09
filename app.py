import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import time

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AgroNova | Farm Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DARK DASHBOARD THEME CSS ---
st.markdown("""
<style>
    /* 1. MAIN BACKGROUND - Dark Blue-Grey */
    .stApp {
        background-color: #1a1c24 !important;
        color: #e0e0e0 !important;
    }

    /* 2. NAVBAR (Custom HTML) */
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #252836;
        padding: 15px 30px;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .nav-logo { font-size: 24px; font-weight: bold; color: #4CAF50; font-family: 'Arial'; }
    .nav-links { font-size: 16px; color: #b0b0b0; }

    /* 3. CARDS (Glassmorphism Style) */
    .dashboard-card {
        background-color: #252836;
        border: 1px solid #2f3342;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    .card-title {
        color: #8c8fa3;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    .metric-value {
        color: #ffffff;
        font-size: 28px;
        font-weight: 700;
    }
    .metric-delta {
        font-size: 14px;
        font-weight: 500;
    }
    .delta-pos { color: #4CAF50; }
    .delta-neg { color: #FF5252; }

    /* 4. CHAT INTERFACE (Center Stage) */
    .stTextArea textarea {
        background-color: #1f212d !important;
        color: #ffffff !important;
        border: 1px solid #3a3f55 !important;
        border-radius: 12px !important;
    }
    .stTextArea textarea:focus {
        border-color: #4CAF50 !important;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.2) !important;
    }
    
    /* Chat Bubbles */
    .chat-user {
        background-color: #4CAF50;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        margin: 5px 0;
        float: right;
        clear: both;
        font-size: 14px;
    }
    .chat-ai {
        background-color: #353a4f;
        color: #e0e0e0;
        padding: 10px 15px;
        border-radius: 0 15px 15px 15px;
        margin: 5px 0;
        float: left;
        clear: both;
        font-size: 14px;
    }

    /* 5. BUTTONS */
    .stButton>button {
        background-color: #4CAF50 !important;
        color: white !important;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    
    /* Hide Default Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Chart Text Color */
    text { fill: #b0b0b0 !important; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=50)
    st.markdown("### AgroNova Settings")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 API Key", type="password")
    
    if api_key:
        genai.configure(api_key=api_key)
    
    language = st.selectbox("Language", ["English", "Hindi", "Marathi"])

# --- TOP NAVIGATION ---
st.markdown("""
<div class="nav-container">
    <div class="nav-logo">🌿 AgroNova <span style="font-size:14px; color:#888;">| HarvestAI Dashboard</span></div>
    <div class="nav-links">Dashboard &nbsp;&nbsp; Crops &nbsp;&nbsp; Analytics &nbsp;&nbsp; <b>Market</b></div>
</div>
""", unsafe_allow_html=True)

# --- MAIN GRID LAYOUT ---
# Create 3 Columns: Left (Stats), Center (Chat/Map), Right (Analytics)
col_left, col_center, col_right = st.columns([1, 2, 1])

# ================= LEFT COLUMN: QUICK INSIGHTS =================
with col_left:
    # Card 1: Soil Health
    st.markdown("""
    <div class="dashboard-card">
        <div class="card-title">🌱 Soil Moisture</div>
        <div class="metric-value">68%</div>
        <div class="metric-delta delta-pos">▲ Optimal</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Card 2: Next Harvest
    st.markdown("""
    <div class="dashboard-card">
        <div class="card-title">🌾 Next Harvest</div>
        <div class="metric-value">12 Days</div>
        <div class="metric-delta" style="color:#FFC107;">Wheat (Nashik)</div>
    </div>
    """, unsafe_allow_html=True)

    # Task List (Static for Demo)
    st.markdown('<div class="dashboard-card"><div class="card-title">📋 Task Manager</div>', unsafe_allow_html=True)
    st.checkbox("Check Drone Batteries", value=True)
    st.checkbox("Fertilize Field A", value=False)
    st.checkbox("Pest Inspection", value=False)
    st.markdown("</div>", unsafe_allow_html=True)

# ================= CENTER COLUMN: AI COMMAND & MAP =================
with col_center:
    # 1. HERO BANNER (Simple Text Overlay)
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f4037, #99f2c8); padding: 20px; border-radius: 15px; margin-bottom: 20px; color: #1a1c24;">
        <h2 style="margin:0; color:#0f2027;">Optimize Yields with AI</h2>
        <p style="margin:0; color:#1a1c24;">Ask AgroNova about crop diseases, weather, or market trends.</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. AI CHAT INTERFACE (The Core Feature)
    st.markdown('<div class="dashboard-card" style="min-height: 400px;">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🤖 AI Farm Assistant</div>', unsafe_allow_html=True)
    
    # Chat History
    if "dash_history" not in st.session_state:
        st.session_state.dash_history = []
    
    # Display last 3 messages to keep it compact
    for chat in st.session_state.dash_history[-3:]:
        role_class = "chat-user" if chat["role"] == "user" else "chat-ai"
        st.markdown(f'<div class="{role_class}">{chat["content"]}</div>', unsafe_allow_html=True)
    st.markdown('<div style="clear:both;"></div>', unsafe_allow_html=True)

    # Chat Input
    with st.form(key="dash_chat"):
        user_input = st.text_area("Ask AI...", height=70, label_visibility="collapsed", placeholder="e.g., 'Best fertilizer for cotton?'")
        cols = st.columns([4, 1])
        with cols[1]:
            submit = st.form_submit_button("Send")
    
    if submit and user_input:
        if not api_key:
            st.warning("⚠️ API Key needed.")
        else:
            # Add User Msg
            st.session_state.dash_history.append({"role": "user", "content": user_input})
            
            # Get Response
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(f"Act as AgroNova, an expert farm assistant. Keep answer short (max 50 words). Language: {language}. Query: {user_input}")
                st.session_state.dash_history.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception as e:
                st.error("AI Error")

    st.markdown('</div>', unsafe_allow_html=True)

    # 3. FIELD MAP (Visual)
    st.markdown('<div class="dashboard-card"><div class="card-title">📍 Field View (Maharashtra)</div>', unsafe_allow_html=True)
    # Mock Coordinates for Maharashtra
    map_data = pd.DataFrame(
        np.random.randn(5, 2) / [50, 50] + [19.75, 75.71],
        columns=['lat', 'lon'])
    st.map(map_data, zoom=6, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ================= RIGHT COLUMN: ANALYTICS =================
with col_right:
    # 1. WEATHER WIDGET
    st.markdown("""
    <div class="dashboard-card">
        <div class="card-title">☀️ Weather (Pune)</div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size:32px; color:white;">28°C</span><br>
                <span style="color:#b0b0b0;">Sunny</span>
            </div>
            <div style="text-align:right;">
                <div>💧 45% Hum</div>
                <div>💨 12 km/h</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. ANALYTICS CHART (Yield Forecast)
    st.markdown('<div class="dashboard-card"><div class="card-title">📊 Yield Forecast</div>', unsafe_allow_html=True)
    chart_data = pd.DataFrame(
        np.random.randn(20, 2),
        columns=['Wheat', 'Rice'])
    st.line_chart(chart_data, height=150)
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. MARKET TRENDS
    st.markdown('<div class="dashboard-card"><div class="card-title">💰 Market Rates (APMC)</div>', unsafe_allow_html=True)
    st.bar_chart({"Onion": 2500, "Cotton": 6800, "Soy": 4200}, height=150, color="#4CAF50")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("<div style='text-align:center; color:#555; margin-top:20px;'>AgroNova Dashboard v2.0</div>", unsafe_allow_html=True)
