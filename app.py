import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AgroNova | AI Farming",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- FIGMA-STYLE MINIMALIST CSS ---
st.markdown("""
<style>
    /* 1. GLOBAL RESET & WHITE THEME */
    .stApp {
        background-color: #FFFFFF !important;
        color: #111111 !important;
    }
    
    /* 2. REMOVE STREAMLIT DEFAULT PADDING to center things */
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 5rem !important;
        max_width: 900px !important;
    }

    /* 3. HERO TYPOGRAPHY (Like the Figma Headline) */
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-size: 64px !important;
        font-weight: 700;
        text-align: center;
        background: -webkit-linear-gradient(45deg, #1B5E20, #4CAF50);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
        line-height: 1.1;
    }
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 20px;
        color: #666666;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* 4. CENTERED INPUT BOX STYLING */
    /* This hacks the default streamlit text area to look like a centerpiece */
    .stTextArea textarea {
        background-color: #F8F9FA !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 20px !important;
        font-size: 18px;
        padding: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        transition: box-shadow 0.3s ease;
        height: 150px !important; /* Make it tall like the Figma box */
    }
    .stTextArea textarea:focus {
        box-shadow: 0 8px 24px rgba(0,0,0,0.1) !important;
        border-color: #1B5E20 !important;
    }

    /* 5. PILL BUTTONS (The quick prompts below input) */
    div.stButton > button {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #E0E0E0;
        border-radius: 30px;
        padding: 10px 24px;
        font-size: 14px;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #F1F8E9;
        border-color: #1B5E20;
        color: #1B5E20;
        transform: translateY(-2px);
    }
    
    /* 6. RESPONSE CARD STYLE */
    .response-box {
        background-color: #F1F8E9;
        border-radius: 16px;
        padding: 30px;
        margin-top: 30px;
        border: 1px solid #C8E6C9;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }

    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (Hidden by default, for settings) ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Enter API Key", type="password")
    
    if api_key:
        genai.configure(api_key=api_key)
    
    language = st.selectbox("Language", ["English", "Hindi", "Marathi", "Spanish"])

# --- MAIN HERO SECTION ---
# 1. Big Headline
st.markdown('<div class="hero-title">Your AI Farming Tool,<br>Now in AgroNova</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Ask about crops, pests, or weather in Maharashtra</div>', unsafe_allow_html=True)

# --- CENTERED INPUT LOGIC ---
# We use a form so the user can type and hit "Ctrl+Enter" or click a button
with st.form(key='search_form'):
    col_center = st.columns([1, 10, 1])[1] # Center align hack
    with col_center:
        user_input = st.text_area(
            label="Input", 
            label_visibility="collapsed",
            placeholder="Describe your farming issue here... (e.g., 'White spots on tomato leaves')",
        )
        
        # Action Row inside the form (Submit button on right)
        c1, c2, c3 = st.columns([6, 1, 1])
        with c3:
            submit_button = st.form_submit_button(label="Ask AI ➔")

# --- QUICK PROMPT PILLS (Like Figma's bottom buttons) ---
st.markdown("<br>", unsafe_allow_html=
