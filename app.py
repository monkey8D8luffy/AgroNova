import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AgroNova | Smart Farming AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- PROFESSIONAL UI & ANIMATION CSS ---
st.markdown("""
<style>
    /* 1. FORCE LIGHT THEME & BACKGROUND */
    .stApp {
        background-color: #F4F8F4; /* Soft Mint Cream */
        color: #1E1E1E;
    }
    
    /* 2. TYPOGRAPHY */
    h1, h2, h3 {
        color: #1B5E20 !important; /* Forest Green */
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }
    p, div, label {
        color: #333333 !important; /* Dark Grey for readability */
    }

    /* 3. CUSTOM CARDS (White with Shadow) */
    .feature-card {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #E0E0E0;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(46, 125, 50, 0.15);
        border-color: #66BB6A;
    }

    /* 4. CHAT BUBBLES */
    .stChatMessage {
        background-color: #FFFFFF;
        border-radius: 15px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    /* User Message Difference */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #E8F5E9; /* Light Green Tint */
    }

    /* 5. SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #1B5E20;
    }
    
    /* 6. BUTTON STYLING (Pill Shape) */
    .stButton>button {
        border-radius: 50px;
        border: 1px solid #1B5E20;
        color: #1B5E20;
        background-color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #1B5E20;
        color: white;
        border-color: #1B5E20;
        transform: scale(1.02);
    }

    /* 7. CUSTOM LOADING ANIMATION (The Sprout) */
    .loader {
        width: 48px;
        height: 48px;
        display: block;
        margin: 20px auto;
        position: relative;
        border: 3px solid #1B5E20;
        border-radius: 50%;
        box-sizing: border-box;
        animation: animloader 2s linear infinite;
    }
    .loader::after {
        content: '';  
        box-sizing: border-box;
        width: 6px;
        height: 24px;
        background: #1B5E20;
        transform: rotate(-45deg);
        position: absolute;
        bottom: -20px;
        left: 46px;
    }
    @keyframes animloader {
        0% { transform: translate(-10px, -10px); }
        25% { transform: translate(-10px, 10px); }
        50% { transform: translate(10px, 10px); }
        75% { transform: translate(10px, -10px); }
        100% { transform: translate(-10px, -10px); }
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🌿 AgroNova")
    
    # API Key Handling
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 API Key", type="password")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            st.success("System Online")
        except:
            st.error("Invalid Key")
            
    st.markdown("---")
    st.markdown("### ⚙️ Preferences")
    language = st.selectbox("Language / भाषा", ["English", "Marathi (मराठी)", "Hindi (हिंदी)", "Gujarati (ગુજરાતી)"])
    st.info("📍 Region: Maharashtra, India")

# --- MODEL FUNCTION ---
def get_ai_response(prompt, lang):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        full_prompt = f"""
        Act as an expert agronomist for Maharashtra, India.
        User Language: {lang}
        Question: {prompt}
        
        Guidelines:
        1. Keep answers short, practical, and bulleted.
        2. Focus on local crops (Sugarcane, Cotton, Mango, Onion, Rice).
        3. Mention specific fertilizers/pesticides available in India.
        """
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return "⚠️ Service busy. Please try again."

# --- HERO SECTION ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.markdown("# 🌱")
with col_title:
    st.markdown("# AgroNova AI")
    st.markdown("### *Your Expert Farming Companion for Maharashtra*")

# --- FEATURE CARDS ---
c1, c2, c3 = st.columns(3)
with c1: st.markdown('<div class="feature-card">🔬 <b>Crop Doctor</b><br><small>Identify diseases instantly</small></div>', unsafe_allow_html=True)
with c2: st.markdown('<div class="feature-card">🌦️ <b>Weather</b><br><small>Local forecast & alerts</small></div>', unsafe_allow_html=True)
with c3: st.markdown('<div class="feature-card">💰 <b>Market Rates</b><br><small>Latest APMC prices</small></div>', unsafe_allow_html=True)

st.markdown("---")

# --- MAHARASHTRA PROMPTS ---
st.subheader("🔍 What would you like to know?")
st.markdown("Try one of these searches:")

# Custom Grid for Prompts
p_col1, p_col2, p_col3, p_col4 = st.columns(4)

prompt_map = {
    "🥭 Alphonso Care": "Give me a care schedule for Alphonso Mango flowering stage.",
    "🌾 Sugarcane Yield": "Best fertilizers to increase Sugarcane tonnage in Maharashtra.",
    "🦠 Cotton Pests": "Organic control for Pink Bollworm in Cotton.",
    "🧅 Onion Storage": "How to prevent rotting in stored onions during monsoon?"
}

selected_prompt = None

if p_col1.button("🥭 Alphonso Care"): selected_prompt = prompt_map["🥭 Alphonso Care"]
if p_col2.button("🌾 Sugarcane Yield"): selected_prompt = prompt_map["🌾 Sugarcane Yield"]
if p_col3.button("🦠 Cotton Pests"): selected_prompt = prompt_map["🦠 Cotton Pests"]
if p_col4.button("🧅 Onion Storage"): selected_prompt = prompt_map["🧅 Onion Storage"]

# --- CHAT UI ---
if "history" not in st.session_state:
    st.session_state.history = []

# Display History
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle Input
user_input = st.chat_input("Ask about crops, fertilizers, or diseases...", key="main_input")

# Logic: If button clicked OR text typed
final_query = selected_prompt if selected_prompt else user_input

if final_query:
    # Show user message
    with st.chat_message("user"):
        st.markdown(final_query)
    st.session_state.history.append({"role": "user", "content": final_query})

    # Show custom loading animation
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown('<div class="loader"></div>', unsafe_allow_
