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
        'water_condition': 'Good', 'language': 'English',
        'name': 'Saurav', # Updated default name
        'gemini_key': os.getenv('GOOGLE_API_KEY', ''),
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
    'English': {'home': 'Home', 'profile': 'Profile', 'setting': 'Setting', 'search_placeholder': 'Ask anything about farming...', 'personalized_prompts': 'Personalized Prompts', 'weather': 'Weather', 'tips': 'Farming Tips', 'harvest': 'Harvest Countdown', 'seeds': 'Recommended Seeds', 'save': 'Save Settings', 'history': 'History', 'news': 'Local Ag News'},
}
def t(key):
    lang = st.session_state.settings.get('language', 'English')
    return translations.get(lang, translations['English']).get(key, key)

# --- PROFESSIONAL UI/UX CSS (GLASSMORPHISM & ANIMATIONS) ---
leaf_bg_url = "https://images.unsplash.com/photo-1555037015-1498966bcd7c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80" # High-quality dark wet leaves

st.markdown(f"""
<style>
    /* Smooth Fade-in Animation */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Global App Background */
    .stApp {{
        background-image: url('{leaf_bg_url}');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }}
    
    /* Hide standard header/footer */
    #MainMenu, footer, header {{visibility: hidden;}}

    /* Enforce Global Text Colors for Visibility */
    h1, h2, h3, h4, h5, h6, p, span, label, div {{
        color: #FFFFFF !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }}
    .stMarkdown p, .stCaption p, small {{
        color: #E2E8E0 !important;
    }}

    /* Glassmorphism Cards & Containers */
    [data-testid="stVerticalBlockBorderWrapper"], .custom-card, [data-testid="stExpander"] {{
        background: rgba(30, 50, 35, 0.45) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        padding: 15px;
        animation: fadeIn 0.6s ease-out;
    }}
    .custom-card {{ padding: 24px; margin-bottom: 20px; }}

    /* Streamlit Buttons (Glass style + Animations) */
    .stButton > button {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(5px) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 25px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        font-weight: 600 !important;
    }}
    .stButton > button:hover {{
        background: rgba(144, 238, 144, 0.25) !important;
        border-color: #90EE90 !important;
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 20px rgba(144, 238, 144, 0.2) !important;
    }}

    /* Chat Inputs & Selectboxes */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background: rgba(20, 30, 20, 0.6) !important;
        color: #FFFFFF !important;
        border-radius: 25px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(8px) !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
    }}
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus {{
        border-color: #A3E635 !important;
        box-shadow: 0 0 10px rgba(163, 230, 53, 0.4) !important;
        background: rgba(30, 50, 35, 0.8) !important;
    }}
    
    /* Placeholder Text Color */
    ::placeholder {{ color: rgba(255, 255, 255, 0.6) !important; opacity: 1; }}

    /* Chat Messages */
    [data-testid="stChatMessage"] {{
        background: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 12px;
        animation: fadeIn 0.4s ease-out;
    }}
</style>
""", unsafe_allow_html=True)

# --- HELPER: API INTEGRATIONS ---
def configure_gemini():
    key = st.session_state.settings.get('gemini_key')
    if key: genai.configure(api_key=key)
    return key is not None and key != ''

def get_gemini_response(prompt, image=None):
    if not configure_gemini(): return "⚠️ Please set your Google Gemini API Key in your .env file."
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        settings_context = f"Context: Farmer in {st.session_state.settings['state']}. Soil: {st.session_state.settings['soil_type']}."
        full_prompt = f"{settings_context}\nQuestion: {prompt}"
        response = model.generate_content([full_prompt, image]) if image else model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error connecting to AI: {e}"

def get_personalized_prompts():
    return ["Best crop rotation plan?", "Organic soil health tips?", "Water saving techniques?", "Pest control for Fall Armyworm."]

def get_weather_data(): return {"temp": "28°C", "condition": "Partly Cloudy", "humidity": "65%"}
def get_agri_news(): return [{"title": "New MSP announced for Kharif crops", "source": "AgriNews"}]
def get_seed_recommendations(): return ["Hybrid Wheat DBW 187", "Drought Tolerant Maize PMH 1"]

# --- NAVIGATION LOGIC ---
st.markdown("<br>", unsafe_allow_html=True) # Top padding
c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
with c2:
    if st.button(t('home'), use_container_width=True):
        st.session_state.page = 'Home'
        st.session_state.searching = False
        st.rerun()
with c3:
    if st.button(t('profile'), use_container_width=True):
        st.session_state.page = 'Profile'
        st.rerun()
with c4:
    if st.button(t('setting'), use_container_width=True):
        st.session_state.page = 'Setting'
        st.rerun()

st.markdown("<br><br>", unsafe_allow_html=True)

# ================= PAGE: HOME =================
if st.session_state.page == 'Home':

    if not st.session_state.searching:
        st.markdown(f"<h1 style='text-align: center; font-size: 5rem; font-family: serif; letter-spacing: 4px; text-shadow: 2px 4px 10px rgba(0,0,0,0.5);'>AGRO NOVA</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.2rem; margin-bottom: 40px;'>Your AI Farming Tool for {st.session_state.settings['state']}</p>", unsafe_allow_html=True)

        with st.container():
            col_hist, col_search, col_news = st.columns([1, 6, 1])
            with col_hist:
                if st.button("⏱️", help="History"):
                    st.session_state.update(searching=True, show_history=True, show_news=False)
                    st.rerun()
            with col_search:
                search_query = st.chat_input(t('search_placeholder'))
                with st.expander("📷 Add Image for analysis", expanded=False):
                     uploaded_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
                     if uploaded_file:
                         st.session_state.uploaded_image = Image.open(uploaded_file)
                         st.image(st.session_state.uploaded_image, width=150)
            with col_news:
                if st.button("🌍", help="News"):
                    st.session_state.update(searching=True, show_news=True, show_history=False)
                    st.rerun()

        if search_query:
            st.session_state.update(searching=True, show_history=False, show_news=False)
            with st.spinner("Analyzing..."):
                response = get_gemini_response(search_query, st.session_state.uploaded_image)
                st.session_state.chat_history.append([search_query, response])
                st.session_state.uploaded_image = None
            st.rerun()

        st.markdown(f"<br><h4 style='text-align:center; color: #A3E635 !important;'>{t('personalized_prompts')}</h4>", unsafe_allow_html=True)
        p_cols = st.columns(4)
        for i, prompt in enumerate(get_personalized_prompts()):
            with p_cols[i]:
                 if st.button(prompt, use_container_width=True):
                     st.session_state.searching = True
                     with st.spinner("Thinking..."):
                        response = get_gemini_response(prompt)
                        st.session_state.chat_history.append([prompt, response])
                     st.rerun()

    # --- POST-SEARCH / CHAT VIEW ---
    else:
        c_hist, c_chat, c_news = st.columns([2 if st.session_state.show_history else 0.1, 8, 2 if st.session_state.show_news else 0.1])

        with c_hist:
            if st.session_state.show_history:
                if st.button("← Close"): st.session_state.show_history=False; st.rerun()
                with st.container(height=550, border=True):
                    st.markdown(f"<h3>{t('history')}</h3>", unsafe_allow_html=True)
                    for i, (user_msg, _) in enumerate(reversed(st.session_state.chat_history)):
                        st.markdown(f"**Q:** {user_msg[:30]}...")
                        st.markdown("---")
            else:
                 if st.button("📜 History"): st.session_state.update(show_history=True, show_news=False); st.rerun()

        with c_chat:
             with st.container(height=550, border=True):
                 for user_msg, ai_msg in st.session_state.chat_history:
                     with st.chat_message("user"): st.write(user_msg)
                     with st.chat_message("assistant", avatar="🌿"): st.write(ai_msg)

             new_query = st.chat_input("Ask follow-up...", key="chat_followup")
             if new_query:
                 with st.spinner("Thinking..."):
                    response = get_gemini_response(new_query)
                    st.session_state.chat_history.append([new_query, response])
                 st.rerun()

        with c_news:
            if st.session_state.show_news:
                if st.button("Close →"): st.session_state.show_news=False; st.rerun()
                with st.container(height=550, border=True):
                    st.markdown(f"<h3>{t('news')}</h3>", unsafe_allow_html=True)
                    for item in get_agri_news():
                        st.markdown(f"**{item['title']}**<br><small>{item['source']}</small>", unsafe_allow_html=True)
                        st.markdown("---")
            else:
                 if st.button("📰 News"): st.session_state.update(show_news=True, show_history=False); st.rerun()

# ================= PAGE: PROFILE =================
elif st.session_state.page == 'Profile':
    col_p_left, col_p_right = st.columns([1, 2])

    with col_p_left:
        st.markdown(f"<div class='custom-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=120)
        # BUG FIXED HERE: Added unsafe_allow_html to properly parse the <h3> tag
        st.markdown(f"<h3 style='margin-top:10px;'>{st.session_state.settings['name']}</h3>", unsafe_allow_html=True)

        st.markdown("<div style='text-align: left; margin-top: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"**📍 Location:** {st.session_state.settings['state']}, {st.session_state.settings['country']}")
        st.markdown(f"**🌱 Soil:** {st.session_state.settings['soil_type']}")
        st.markdown(f"**💧 Water:** {st.session_state.settings['water_condition']}")
        st.markdown("</div></div>", unsafe_allow_html=True)

        with st.expander("✏️ Edit Name"):
             new_name = st.text_input("Name", st.session_state.settings['name'])
             if st.button("Update"):
                 st.session_state.settings['name'] = new_name
                 st.rerun()

    with col_p_right:
        st.markdown(f"<div class='custom-card'>", unsafe_allow_html=True)
        w_data = get_weather_data()
        c_w1, c_w2 = st.columns([1,3])
        with c_w1: st.markdown(f"<h1 style='color:#A3E635 !important; font-size:3rem;'>{w_data['temp']}</h1>", unsafe_allow_html=True)
        with c_w2: st.markdown(f"<h3>{t('weather')}</h3><p>{w_data['condition']}, Humidity: {w_data['humidity']}</p>", unsafe_allow_html=True)
        st.markdown("---")

        c_h1, c_h2 = st.columns(2)
        with c_h1:
             st.markdown(f"<h3>⏳ {t('harvest')}</h3><h2>45 Days</h2><p>*(Wheat)*</p>", unsafe_allow_html=True)
        with c_h2:
             st.markdown(f"<h3>🌾 {t('seeds')}</h3>", unsafe_allow_html=True)
             for seed in get_seed_recommendations(): st.markdown(f"- {seed}")
        st.markdown("</div>", unsafe_allow_html=True)

# ================= PAGE: SETTING =================
elif st.session_state.page == 'Setting':
    st.markdown(f"<div class='custom-card'><h2 style='text-align:center;'>⚙️ {t('setting')}</h2></div>", unsafe_allow_html=True)

    with st.form("settings_form"):
        c_s1, c_s2 = st.columns(2)

        with c_s1:
            st.markdown("<div class='custom-card'><h3>🌍 Location & Soil</h3>", unsafe_allow_html=True)
            sel_country = st.selectbox("Country", ["India", "United States", "Netherlands"], index=0)
            sel_state = st.selectbox("State/Region", ["Maharashtra", "Punjab", "Karnataka"], index=0)
            sel_soil = st.selectbox("Soil Type", ['Red Soil', 'Black Cotton Soil', 'Alluvial Soil'], index=0)
            sel_water = st.selectbox("Water Condition", ['Excellent', 'Good', 'Average', 'Poor'], index=1)
            st.markdown("</div>", unsafe_allow_html=True)

        with c_s2:
            # API Options removed entirely from UI for cleaner UX
            st.markdown("<div class='custom-card'><h3>📱 App Preferences</h3>", unsafe_allow_html=True)
            sel_lang = st.selectbox("Language", ['English', 'Hindi', 'Marathi'], index=0)
            st.caption("Note: API configurations have been moved to backend environment variables for security.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button(t('save'), use_container_width=True):
            st.session_state.settings.update({'country': sel_country, 'state': sel_state, 'soil_type': sel_soil, 'water_condition': sel_water, 'language': sel_lang})
            st.success("Settings Saved Successfully!")
            st.rerun()
