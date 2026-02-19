from dotenv import load_dotenv
import os
import streamlit as st
import google.generativeai as genai
import requests
import json
from PIL import Image
import base64
import io
from country_list import countries_for_language

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AgroNova AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SESSION STATE INITIALIZATION ---
def init_session_state():
    default_settings = {
        'country': 'India', 'state': 'Maharashtra', 'soil_type': 'Red Soil',
        'water_condition': 'Good', 'language': 'English', 'dark_mode': False,
        'name': 'Farmer John',
        'gemini_key': os.getenv('GOOGLE_API_KEY', ''),
        'weather_key': os.getenv('OPENWEATHER_KEY', ''),
        'news_key': os.getenv('NEWS_API_KEY', '')
    }
    if 'settings' not in st.session_state: st.session_state.settings = default_settings
    if 'page' not in st.session_state: st.session_state.page = 'Home'
    if 'searching' not in st.session_state: st.session_state.searching = False
    if 'chat_history' not in st.session_state: st.session_state.chat_history = []
    if 'show_history' not in st.session_state: st.session_state.show_history = False
    if 'show_news' not in st.session_state: st.session_state.show_news = False
    if 'uploaded_image' not in st.session_state: st.session_state.uploaded_image = None

init_session_state()

# --- HELPER: TRANSLATIONS ---
translations = {
    'English': {'home': 'Home', 'profile': 'Profile', 'setting': 'Setting', 'search_placeholder': 'Ask anything about farming...', 'personalized_prompts': 'Personalized Prompts for your Area', 'weather': 'Weather', 'tips': 'Farming Tips', 'harvest': 'Harvest Countdown', 'seeds': 'Recommended High-Yield Seeds', 'save': 'Save Settings', 'dark_mode': 'Dark Mode', 'history': 'History', 'news': 'Local Ag News', 'send': 'Send'},
}
def t(key):
    lang = st.session_state.settings.get('language', 'English')
    return translations.get(lang, translations['English']).get(key, key)

# --- HELPER: CSS & ASSETS ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# FIXED: Looking for the exact JPEG file name you uploaded!
image_filename = "green-and-colored-tropical-leaves-on-bright-colorful-background-photo.jpg"
try:
    img_base64 = get_base64_of_bin_file(image_filename)
    bg_image_css = f'url("data:image/jpeg;base64,{img_base64}")'
except FileNotFoundError:
    st.error(f"⚠️ Image '{image_filename}' not found. Make sure it is saved in the exact same folder as this Python script!")
    bg_image_css = ""

dark_mode_css = """
    --bg-overlay: rgba(0, 0, 0, 0.75);
    --glass-bg: rgba(0, 0, 0, 0.5);
    --text-color: #e0e0e0;
    --input-bg: rgba(255, 255, 255, 0.1);
""" if st.session_state.settings['dark_mode'] else """
    --bg-overlay: rgba(255, 255, 255, 0.5);
    --glass-bg: rgba(255, 255, 255, 0.7);
    --text-color: #0b3d0b;
    --input-bg: rgba(255, 255, 255, 0.8);
"""

st.markdown(f"""
<style>
    :root {{
        {dark_mode_css}
    }}
    .stApp {{
        background-image: linear-gradient(var(--bg-overlay), var(--bg-overlay)), {bg_image_css};
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .glass-container {{
        background: var(--glass-bg);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 20px;
        margin-bottom: 15px;
        color: var(--text-color);
    }}
    .nav-pills {{
        display: flex;
        justify-content: center;
        gap: 10px;
        padding-bottom: 20px;
    }}
    .nav-pill-btn {{
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 30px;
        padding: 8px 25px;
        color: var(--text-color);
        cursor: pointer;
        transition: 0.3s;
        text-align: center;
        font-weight: 500;
    }}
    .nav-pill-btn:hover {{ background: rgba(255,255,255,0.4); color: #1a4a1c; }}
    .nav-active {{ background: #aed581 !important; color: #1a4a1c !important; font-weight: bold; }}
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {{
        background-color: var(--input-bg) !important;
        color: var(--text-color) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }}
    h1, h2, h3, h4, p, label, .stMarkdown p {{ color: var(--text-color) !important; }}
    #MainMenu, footer, header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# --- HELPER: API INTEGRATIONS ---
def configure_gemini():
    key = st.session_state.settings.get('gemini_key')
    if key: 
        genai.configure(api_key=key)
        return True
    return False

def get_gemini_response(prompt, image=None):
    if not configure_gemini(): 
        return "⚠️ Please go to the 'Setting' tab above and enter your Google Gemini API Key."
    try:
        # Using the exact model name supported by your API key
        model_name = 'gemini-2.0-flash'
        model = genai.GenerativeModel(model_name)

        settings_context = f"Context: User is a farmer in {st.session_state.settings['state']}, {st.session_state.settings['country']}. Respond in {st.session_state.settings['language']}."
        full_prompt = f"{settings_context}\nQuestion: {prompt}"

        if image:
            response = model.generate_content([full_prompt, image])
        else:
            response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def get_personalized_prompts():
    loc = f"{st.session_state.settings['state']}, {st.session_state.settings['country']}"
    return [
        f"Best crop rotation plan for {loc}?",
        f"How to improve {st.session_state.settings['soil_type']} health organically?",
        "Pest control measures for Fall Armyworm.",
        "Optimal fertilizer schedule for sugarcane.",
    ]

# --- NAVIGATION LOGIC ---
c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
with c2:
    if st.button(t('home'), key='nav_home', use_container_width=True):
        st.session_state.searching = False
        st.session_state.page = 'Home'
        st.rerun()
with c3:
    if st.button(t('profile'), key='nav_profile', use_container_width=True):
        st.session_state.page = 'Profile'
        st.session_state.searching = False
        st.rerun()
with c4:
    if st.button(t('setting'), key='nav_setting', use_container
