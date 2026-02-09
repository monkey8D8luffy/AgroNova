import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from PIL import Image

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AgroNova | Smart Farm",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM THEME CSS ---
st.markdown("""
<style>
    /* 1. MAIN BACKGROUND */
    .stApp {
        background-color: #658364 !important; /* Sage Green */
    }

    /* 2. SIDEBAR BACKGROUND */
    [data-testid="stSidebar"] {
        background-color: #2D4B2E !important; /* Dark Forest Green */
        color: white !important;
    }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: white !important;
    }

    /* 3. DASHBOARD CARDS/BOXES */
    .dashboard-card {
        background-color: #2D4B2E;
        border: 1px solid #3E5C3F;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        color: white;
    }
    .card-title {
        color: #A0CFA0; /* Light Green for titles */
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    .metric-value {
        color: white;
        font-size: 28px;
        font-weight: 700;
    }
    .metric-subtext {
        color: #C0E0C0;
        font-size: 14px;
    }

    /* 4. CHAT INTERFACE */
    .stTextArea textarea {
        background-color: #3E5C3F !important;
        color: white !important;
        border: 1px solid #507051 !important;
        border-radius: 12px !important;
    }
    .stTextArea textarea::placeholder {
        color: #A0CFA0 !important;
    }
    
    /* Chat Bubbles */
    .chat-user {
        background-color: #4CAF50; /* Bright Green */
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 0 18px;
        margin: 8px 0;
        float: right;
        clear: both;
        font-size: 15px;
        max-width: 80%;
    }
    .chat-ai {
        background-color: #3E5C3F;
        color: white;
        padding: 12px 18px;
        border-radius: 0 18px 18px 18px;
        margin: 8px 0;
        float: left;
        clear: both;
        font-size: 15px;
        max-width: 80%;
    }

    /* 5. GENERAL TEXT & BUTTONS */
    h1, h2, h3, h4, p, label, span, div {
        color: white;
    }
    .stButton>button {
        background-color: #4CAF50 !important;
        color: white !important;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #45a049 !important;
    }
    
    /* Remove default padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Profile Photo Style */
    .profile-img {
        border-radius: 50%;
        border: 3px solid #4CAF50;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- MOCK DATA HELPERS ---
def get_location_data(state):
    data = {
        "Maharashtra": {"region": "Pune", "weather": {"temp": "28°C", "cond": "Sunny", "hum": "45%"}, "crops": ["Sugarcane", "Cotton", "Mango"], "harvest_days": 12},
        "Punjab": {"region": "Amritsar", "weather": {"temp": "34°C", "cond": "Clear", "hum": "30%"}, "crops": ["Wheat", "Rice", "Maize"], "harvest_days": 45},
        "Karnataka": {"region": "Bengaluru", "weather": {"temp": "24°C", "cond": "Cloudy", "hum": "65%"}, "crops": ["Coffee", "Ragi", "Sunflower"], "harvest_days": 30}
    }
    return data.get(state, data["Maharashtra"])

def get_soil_moisture(water_cond):
    return "High (Optimal)" if water_cond == "Irrigated" else "Medium (Needs Rain)"

# --- SIDEBAR: PROFILE & SETTINGS ---
with st.sidebar:
    st.markdown("## 👤 Farmer Profile")
    
    # 1. Profile Photo
    uploaded_file = st.file_uploader("Upload Photo", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, width=120, output_format='PNG', use_column_width=False, clamp=True, channels='RGB', caption=None, className="profile-img")
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=120, className="profile-img")
        
    # 2. Name
    farmer_name = st.text_input("Name", value=st.session_state.get("name", "Rajesh Kumar"))
    st.session_state["name"] = farmer_name
    
    st.markdown("---")
    st.markdown("### ⚙️ Farm Settings")

    # 3. API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Google API Key", type="password")
    if api_key: genai.configure(api_key=api_key)

    # 4. Language (Real-time update)
    language = st.selectbox("🗣️ Language", ["English", "Hindi (हिंदी)", "Marathi (मराठी)", "Punjabi (ਪੰਜਾਬੀ)"])
    
    # 5. Location & Conditions (Drives Dashboard Data)
    state = st.selectbox("📍 State", ["Maharashtra", "Punjab", "Karnataka"])
    
    loc_data = get_location_data(state)
    region = st.text_input("Region/District", value=loc_data["region"], disabled=True)
    
    water_cond = st.selectbox("💧 Water Source", ["Irrigated", "Rainfed"])

    st.success(f"Settings Updated for {state}!")

# --- MAIN DASHBOARD ---

# 1. Header
st.markdown(f"# 🌿 Welcome, {farmer_name}!")
st.markdown(f"### *Farm Dashboard for {region}, {state}*")
st.write("") # Spacer

# 2. Main Grid
col_left, col_center, col_right = st.columns([1, 2, 1])

# ================= LEFT COLUMN: STATUS & TASKS =================
with col_left:
    # Dynamic Soil Health Card
    moisture_status = get_soil_moisture(water_cond)
    st.markdown(f"""
    <div class="dashboard-card">
        <div class="card-title">🌱 Soil Status</div>
        <div class="metric-value">{moisture_status}</div>
        <div class="metric-subtext">Based on: {water_cond}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Dynamic Harvest Card
    st.markdown(f"""
    <div class="dashboard-card">
        <div class="card-title">🚜 Next Harvest</div>
        <div class="metric-value">{loc_data['harvest_days']} Days</div>
        <div class="metric-subtext">Primary Crop: {loc_data['crops'][0]}</div>
    </div>
    """, unsafe_allow_html=True)

    # Task Checklist
    st.markdown('<div class="dashboard-card"><div class="card-title">📋 This Week\'s Tasks</div>', unsafe_allow_html=True)
    st.checkbox("Apply fertilizer (Field B)")
    st.checkbox("Check irrigation pumps")
    st.checkbox(f"Scout for pests in {loc_data['crops'][1]}")
    st.markdown('</div>', unsafe_allow_html=True)

# ================= CENTER COLUMN: AI CHAT (Shifted Here) =================
with col_center:
    st.markdown('<div class="dashboard-card" style="min-height: 600px;">', unsafe_allow_html=True)
    st.markdown('<div class="card-title" style="font-size:20px;">🤖 AgroNova AI Assistant</div>', unsafe_allow_html=True)
    st.markdown(f"*(Responding in {language} for {state} region)*")
    st.write("---")

    # Chat History Container
    chat_container = st.container()
    if "profile_history" not in st.session_state:
        st.session_state.profile_history = []
        # Initial greeting
        st.session_state.profile_history.append({"role": "assistant", "content": f"Hello {farmer_name}! I'm set up for your farm in {state}. How can I help you today?"})

    with chat_container:
        for chat in st.session_state.profile_history:
            role_class = "chat-user" if chat["role"] == "user" else "chat-ai"
            st.markdown(f'<div class="{role_class}">{chat["content"]}</div>', unsafe_allow_html=True)
        st.markdown('<div style="clear:both;"></div>', unsafe_allow_html=True)

    # Chat Input
    st.write("") # Spacer
    with st.form(key="profile_chat_form"):
        user_input = st.text_area("Message", height=100, label_visibility="collapsed", placeholder="Ask about crops, weather, or pests...")
        cols = st.columns([5, 1])
        with cols[1]:
            submit_btn = st.form_submit_button("Send ➔")

    if submit_btn and user_input:
        if not api_key:
            st.error("⚠️ Please enter API Key in sidebar.")
        else:
            # Add User Msg
            st.session_state.profile_history.append({"role": "user", "content": user_input})
            
            # Generate AI Response with Profile Context
            with st.spinner("Thinking..."):
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    context_prompt = f"""
                    Act as an expert agronomist.
                    **Farmer Profile:**
                    - Name: {farmer_name}
                    - Location: {region}, {state}, India
                    - Water Source: {water_cond}
                    - Key Crops: {', '.join(loc_data['crops'])}
                    - Language Preference: {language}
                    
                    **User Query:** {user_input}
                    
                    **Instructions:**
                    - Respond in {language}.
                    - Be practical, brief, and specific to their location and conditions.
                    """
                    response = model.generate_content(context_prompt)
                    st.session_state.profile_history.append({"role": "assistant", "content": response.text})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# ================= RIGHT COLUMN: WEATHER & INSIGHTS =================
with col_right:
    # Dynamic Weather Card
    w = loc_data['weather']
    st.markdown(f"""
    <div class="dashboard-card">
        <div class="card-title">🌤️ Weather in {region}</div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size:36px; font-weight:bold;">{w['temp']}</span><br>
                <span style="font-size:16px;">{w['cond']}</span>
            </div>
            <div style="text-align:right; font-size:14px;">
                <div>💧 Hum: {w['hum']}</div>
                <div>💨 Wind: 15 km/h</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Crop Recommendations Card
    st.markdown(f"""
    <div class="dashboard-card">
        <div class="card-title">🌾 Recommended Crops</div>
        <div class="metric-subtext">Best for {state}'s current season:</div>
        <ul style="padding-left: 20px; margin-top: 10px; font-size: 15px;">
            <li><b>{loc_data['crops'][0]}</b> (Primary)</li>
            <li>{loc_data['crops'][1]}</li>
            <li>{loc_data['crops'][2]}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Quick Prompts Card
    st.markdown('<div class="dashboard-card"><div class="card-title">💡 Quick Ideas</div>', unsafe_allow_html=True)
    if st.button(f"Pest control for {loc_data['crops'][0]}?"):
        # You can add logic to auto-submit this to chat
        pass
    st.write("")
    if st.button(f"Fertilizer plan for {water_cond} soil?"):
        pass
    st.markdown('</div>', unsafe_allow_html=True)
