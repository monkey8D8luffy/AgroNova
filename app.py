from dotenv import load_dotenv
import os
import streamlit as st
import google.generativeai as genai
import requests
import ast
from PIL import Image
import datetime

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
        'name': 'Saurav',
        'crop': 'Wheat', 'sowing_date': datetime.date.today() - datetime.timedelta(days=30),
        'gemini_key': os.getenv('GOOGLE_API_KEY', ''),
    }
    if 'settings' not in st.session_state: st.session_state.settings = default_settings.copy()
    if 'page' not in st.session_state: st.session_state.page = 'Home'
    if 'searching' not in st.session_state: st.session_state.searching = False
    if 'chat_history' not in st.session_state: st.session_state.chat_history = []
    if 'show_history' not in st.session_state: st.session_state.show_history = False
    if 'show_news' not in st.session_state: st.session_state.show_news = False
    if 'uploaded_image' not in st.session_state: st.session_state.uploaded_image = None
    if 'weather_alert' not in st.session_state: st.session_state.weather_alert = None

init_session_state()

# --- HELPER: TRANSLATIONS & CONSTANTS ---
LANGUAGES = ["English", "Hindi", "Marathi", "Gujarati", "Tamil", "Telugu", "Spanish", "French"]
CROP_DURATIONS = { # In days (approximate averages)
    'Wheat': 120, 'Rice (Paddy)': 150, 'Maize (Corn)': 100, 'Sugarcane': 365,
    'Cotton': 160, 'Soybean': 95, 'Tomato': 70, 'Potato': 90
}

translations = {
    'English': {'home': 'Home', 'profile': 'Profile', 'setting': 'Setting', 'search_placeholder': 'Ask anything about farming...', 'personalized_prompts': 'Personalized Prompts', 'weather': 'Weather', 'tips': 'Harvesting Tips', 'harvest': 'Harvest Countdown', 'seeds': 'Recommended Seeds', 'save': 'Save Settings', 'history': 'History', 'news': 'Local Ag News'},
}
def t(key):
    lang = st.session_state.settings.get('language', 'English')
    return translations.get(lang, translations['English']).get(key, key)

# --- HELPER: API INTEGRATIONS ---
@st.cache_data(ttl=86400)
def get_countries_and_states():
    try:
        response = requests.get("https://countriesnow.space/api/v0.1/countries/states", timeout=5)
        if response.status_code == 200:
            data = response.json()['data']
            return {item['name']: [state['name'] for state in item['states']] for item in data if item['states']}
    except Exception: pass
    return {"India": ["Maharashtra", "Punjab"], "United States": ["California", "Texas"]}

# --- WEATHER API (wttr.in - Free, No Key) ---
def get_weather_warning(location):
    try:
        # Using wttr.in format=j1 for JSON output. A free, keyless API.
        sanitized_loc = location.replace(" ", "+")
        url = f"https://wttr.in/{sanitized_loc}?format=j1"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            current_condition = data['current_condition'][0]['weatherDesc'][0]['value'].lower()
            temp_c = float(data['current_condition'][0]['temp_C'])

            SEVERE_CONDITIONS = ['thunder', 'torrential', 'heavy rain', 'snow', 'blizzard', 'flood']
            
            alert = None
            if any(cond in current_condition for cond in SEVERE_CONDITIONS):
                alert = f"⚠️ SEVERE WEATHER ALERT: {current_condition.title()} detected in your area. Take precautions."
            elif temp_c > 40:
                alert = f"⚠️ HEATWAVE ALERT: Extreme temperatures ({temp_c}°C) detected. Ensure crop irrigation."
            
            return alert, temp_c, current_condition.title()
    except Exception: pass
    return None, "N/A", "Data Unavailable"

def configure_gemini():
    key = st.session_state.settings.get('gemini_key')
    if key: genai.configure(api_key=key)
    return key is not None and key != ''

def get_gemini_response(prompt, image=None):
    if not configure_gemini(): return "⚠️ Please set your Google Gemini API Key in your .env file or settings."
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        s = st.session_state.settings
        settings_context = f"Context: Farmer in {s['state']}, {s['country']}. Soil: {s['soil_type']}. Water: {s['water_condition']}. Crop: {s['crop']}. Respond in {s['language']}."
        full_prompt = f"{settings_context}\nQuestion: {prompt}"
        response = model.generate_content([full_prompt, image]) if image else model.generate_content(full_prompt)
        return response.text
    except Exception as e: return f"Error: {e}"

# Simplified for brevity - using static list instead of API call for now
def get_dynamic_prompts():
    s = st.session_state.settings
    return [f"Pest control for {s['crop']}?", f"Fertilizer schedule for {s['soil_type']}?", "Water saving techniques?", "Market price trends?"]

# Simplified harvest tip
def get_harvesting_tips():
     s = st.session_state.settings
     return f"Based on your {s['crop']} and {s['water_condition']} water, ensure grain moisture is below 14% before harvesting to prevent spoilage. Check weather for a 3-day dry spell."

def get_agri_news():
    # Expanded News List
    return [
        {"title": "New agricultural subsidies announced for drip irrigation", "source": "Ministry of Agriculture"},
        {"title": "Monsoon forecast upgraded to 'Above Normal'", "source": "Meteorological Dept"},
        {"title": "Global fertilizer prices see a 5% drop this month", "source": "Agri-Market Watch"},
        {"title": "New pest resistant cotton variety approved for trials", "source": "Research Council"},
        {"title": "Local mandi prices for Wheat show upward trend", "source": "Local Mandi Samiti"}
    ]

# --- PROFESSIONAL UI/UX CSS ---
# Using a URL that matches the dense, dark foliage of image_8.png
leaf_bg_url = "https://images.unsplash.com/photo-1611252954203-569cb17a4e3d?q=80&w=1974&auto=format&fit=crop"

st.markdown(f"""
<style>
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .stApp {{
        background-image: url('{leaf_bg_url}');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }}
    #MainMenu, footer, header {{visibility: hidden;}}
    /* Force high contrast white text */
    h1, h2, h3, h4, h5, h6, p, span, label, div, .stMarkdown p {{ color: #FFFFFF !important; font-family: 'Inter', sans-serif; }}
    .stCaption p, small {{ color: #E2E8E0 !important; }}

    [data-testid="stVerticalBlockBorderWrapper"], .custom-card, [data-testid="stExpander"] {{
        background: rgba(15, 25, 20, 0.75) !important; /* Darker glass */
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
        padding: 15px;
        animation: fadeIn 0.5s ease-out;
    }}
    .custom-card {{ padding: 24px; margin-bottom: 20px; }}
    
    /* Alert Box Styling */
    [data-testid="stAlert"] {{ background: rgba(220, 38, 38, 0.8) !important; color: white !important; border: none; }}

    .stButton > button {{
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(5px) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 25px !important;
        transition: all 0.3s ease !important;
        font-weight: 600;
    }}
    .stButton > button:hover {{
        background: rgba(163, 230, 53, 0.4) !important;
        border-color: #A3E635 !important;
        transform: translateY(-2px);
    }}
    
    .icon-btn > button {{ border-radius: 50% !important; height: 50px; width: 50px; padding: 0 !important; display: flex; justify-content: center; align-items: center; font-size: 1.4rem; }}

    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input {{
        background: rgba(5, 15, 5, 0.6) !important;
        color: #FFFFFF !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 10px 15px !important;
    }}
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus {{ border-color: #A3E635 !important; }}
    ::placeholder {{ color: rgba(255, 255, 255, 0.6) !important; }}

    [data-testid="stChatMessage"] {{
        background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1); border-radius: 15px;
        padding: 15px; margin-bottom: 12px;
    }}
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
st.markdown("<br>", unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
with c2:
    if st.button(t('home'), use_container_width=True): st.session_state.update(page='Home', searching=False); st.rerun()
with c3:
    if st.button(t('profile'), use_container_width=True): st.session_state.page = 'Profile'; st.rerun()
with c4:
    if st.button(t('setting'), use_container_width=True): st.session_state.page = 'Setting'; st.rerun()
st.markdown("<br>", unsafe_allow_html=True)

# ================= PAGE: HOME =================
if st.session_state.page == 'Home':
    
    # Fetch weather warning on home page load
    location_str = f"{st.session_state.settings['state']},{st.session_state.settings['country']}"
    alert_msg, temp_val, cond_val = get_weather_warning(location_str)
    
    if alert_msg:
        st.error(alert_msg, icon="⛈️")

    if not st.session_state.searching:
        st.markdown(f"<h1 style='text-align: center; font-size: 6rem; font-family: serif; letter-spacing: 5px; text-shadow: 2px 4px 15px rgba(0,0,0,0.8); margin-bottom: 0;'>AGRO NOVA</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.3rem; margin-bottom: 50px; opacity: 0.9; font-weight: 300;'>AI Farming Companion for {st.session_state.settings['state']}</p>", unsafe_allow_html=True)

        with st.container():
            # Layout for Search Bar area
            col_hist, col_search, col_news = st.columns([1, 6, 1])
            with col_hist:
                st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
                if st.button("⏱️", help="History"): st.session_state.update(searching=True, show_history=True, show_news=False); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with col_search:
                search_query = st.chat_input(t('search_placeholder'))
                with st.expander("📷 Add Image for analysis", expanded=False):
                     uploaded_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
                     if uploaded_file:
                         st.session_state.uploaded_image = Image.open(uploaded_file)
                         st.image(st.session_state.uploaded_image, width=150)
            with col_news:
                st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
                if st.button("📰", help="News"): st.session_state.update(searching=True, show_news=True, show_history=False); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        if search_query:
            st.session_state.update(searching=True, show_history=False, show_news=False)
            with st.spinner("Analyzing..."):
                response = get_gemini_response(search_query, st.session_state.uploaded_image)
                st.session_state.chat_history.append([search_query, response])
                st.session_state.uploaded_image = None
            st.rerun()

        st.markdown(f"<br><h4 style='text-align:center; color: #A3E635 !important; font-weight:400; letter-spacing: 1px;'>{t('personalized_prompts')}</h4>", unsafe_allow_html=True)
        p_cols = st.columns(4)
        for i, prompt in enumerate(get_dynamic_prompts()):
            with p_cols[i]:
                 if st.button(prompt, use_container_width=True, key=f"p_{i}"):
                     st.session_state.searching = True
                     with st.spinner("Thinking..."):
                        response = get_gemini_response(prompt)
                        st.session_state.chat_history.append([prompt, response])
                     st.rerun()

    # --- POST-SEARCH / CHAT VIEW ---
    else:
        # DYNAMIC COLUMN LAYOUT LOGIC
        show_h = st.session_state.show_history
        show_n = st.session_state.show_news
        
        if show_h and show_n:
            # Both open: Sidebars bigger, chat smaller
            col_widths = [2.5, 7, 2.5]
        elif show_h:
            col_widths = [3, 8.5, 0.5]
        elif show_n:
            col_widths = [0.5, 8.5, 3]
        else:
            col_widths = [0.1, 11.8, 0.1]

        c_hist, c_chat, c_news = st.columns(col_widths)

        with c_hist:
            if show_h:
                if st.button("✖ Close History", key="cl_h", use_container_width=True): st.session_state.show_history=False; st.rerun()
                with st.container(height=600, border=True):
                    st.markdown(f"### {t('history')}")
                    if not st.session_state.chat_history: st.caption("No history yet.")
                    for i, (user_msg, _) in enumerate(reversed(st.session_state.chat_history)):
                        st.markdown(f"<div style='background:rgba(255,255,255,0.1); padding:10px; border-radius:10px; margin-bottom:10px;'><small><strong>Q:</strong> {user_msg[:40]}...</small></div>", unsafe_allow_html=True)
            else:
                 st.markdown("<div class='icon-btn' style='margin-top: 20px;'>", unsafe_allow_html=True)
                 if st.button("⏱️", key="op_h"): st.session_state.update(show_history=True, show_news=False); st.rerun()
                 st.markdown("</div>", unsafe_allow_html=True)

        with c_chat:
             with st.container(height=600, border=True):
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
            if show_n:
                if st.button("✖ Close News", key="cl_n", use_container_width=True): st.session_state.show_news=False; st.rerun()
                with st.container(height=600, border=True):
                    st.markdown(f"### {t('news')}")
                    for item in get_agri_news():
                        st.markdown(f"<div style='background:rgba(255,255,255,0.1); padding:12px; border-radius:10px; margin-bottom:10px;'><strong>{item['title']}</strong><br><small style='opacity:0.7;'>Source: {item['source']}</small></div>", unsafe_allow_html=True)
            else:
                 st.markdown("<div class='icon-btn' style='margin-top: 20px;'>", unsafe_allow_html=True)
                 if st.button("📰", key="op_n"): st.session_state.update(show_news=True, show_history=False); st.rerun()
                 st.markdown("</div>", unsafe_allow_html=True)

# ================= PAGE: PROFILE =================
elif st.session_state.page == 'Profile':
    col_p_left, col_p_right = st.columns([1, 2.2])

    with col_p_left:
        st.markdown(f"<div class='custom-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=110)
        st.markdown(f"<h2 style='margin-top:15px; font-weight: 700;'>{st.session_state.settings['name']}</h2>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: left; margin-top: 25px; line-height: 1.6;'>", unsafe_allow_html=True)
        st.markdown(f"📍 **Location:** {st.session_state.settings['state']}, {st.session_state.settings['country']}")
        st.markdown(f"🌱 **Soil:** {st.session_state.settings['soil_type']}")
        st.markdown(f"🌾 **Active Crop:** {st.session_state.settings['crop']}")
        st.markdown("</div></div>", unsafe_allow_html=True)

    with col_p_right:
        st.markdown(f"<div class='custom-card'>", unsafe_allow_html=True)
        
        # Fetch fresh weather data for profile
        location_str = f"{st.session_state.settings['state']},{st.session_state.settings['country']}"
        _, temp_val, cond_val = get_weather_warning(location_str)
        
        c_w1, c_w2 = st.columns([1,3])
        w_color = "#A3E635" if str(temp_val).replace('.','',1).isdigit() and float(temp_val) < 35 else "#ff6b6b"
        with c_w1: st.markdown(f"<h1 style='color:{w_color} !important; font-size:3.5rem; margin:0;'>{temp_val}°C</h1>", unsafe_allow_html=True)
        with c_w2: st.markdown(f"<h3 style='margin-bottom:5px;'>{t('weather')}</h3><p style='font-size: 1.2rem; opacity: 0.9;'>{cond_val}</p>", unsafe_allow_html=True)
        st.markdown("---")

        # HARVEST COUNTDOWN CALCULATION
        sowing_date = st.session_state.settings['sowing_date']
        crop = st.session_state.settings['crop']
        total_days = CROP_DURATIONS.get(crop, 120)
        days_passed = (datetime.date.today() - sowing_date).days
        days_remaining = max(0, total_days - days_passed)
        
        progress = min(1.0, days_passed / total_days) if total_days > 0 else 0

        c_h1, c_h2 = st.columns([1.5, 1])
        with c_h1:
             st.markdown(f"<h3>⏳ {t('harvest')}</h3>", unsafe_allow_html=True)
             if days_remaining > 0:
                 st.markdown(f"<h1 style='color:#A3E635 !important; font-size:3rem; margin:0;'>{days_remaining} Days</h1>", unsafe_allow_html=True)
                 st.progress(progress)
                 st.caption(f"Sown on: {sowing_date.strftime('%d %b %Y')}")
             else:
                 st.markdown(f"<h2 style='color:#A3E635 !important;'>Ready for Harvest!</h2>", unsafe_allow_html=True)
        with c_h2:
             st.markdown(f"<h3>🌾 {t('tips')}</h3>", unsafe_allow_html=True)
             st.info(get_harvesting_tips(), icon="💡")
        st.markdown("</div>", unsafe_allow_html=True)

# ================= PAGE: SETTING =================
elif st.session_state.page == 'Setting':
    st.markdown(f"<div class='custom-card'><h2 style='text-align:center; margin:0;'>⚙️ {t('setting')}</h2></div>", unsafe_allow_html=True)
    
    country_dict = get_countries_and_states()
    country_list = list(country_dict.keys())
    
    c_s1, c_s2 = st.columns(2)

    with c_s1:
        st.markdown("<div class='custom-card'><h3>🌍 Location & Soil</h3>", unsafe_allow_html=True)
        current_country = st.session_state.settings['country']
        c_idx = country_list.index(current_country) if current_country in country_list else 0
        sel_country = st.selectbox("Country", country_list, index=c_idx)
        
        state_list = country_dict.get(sel_country, ["Select State"])
        current_state = st.session_state.settings['state']
        s_idx = state_list.index(current_state) if current_state in state_list else 0
        sel_state = st.selectbox("State/Region", state_list, index=s_idx)
        
        soil_types = ['Red Soil', 'Black Cotton Soil', 'Alluvial Soil', 'Sandy Loam', 'Clayey', 'Laterite']
        s_type_idx = soil_types.index(st.session_state.settings['soil_type']) if st.session_state.settings['soil_type'] in soil_types else 0
        sel_soil = st.selectbox("Soil Type", soil_types, index=s_type_idx)
        
        water_conds = ['Excellent (Irrigated)', 'Good (Seasonal)', 'Average', 'Poor (Rainfed)', 'Very Bad']
        w_cond_idx = water_conds.index(st.session_state.settings['water_condition']) if st.session_state.settings['water_condition'] in water_conds else 1
        sel_water = st.selectbox("Water Condition", water_conds, index=w_cond_idx)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_s2:
        st.markdown("<div class='custom-card'><h3>🌾 Crop & Preferences</h3>", unsafe_allow_html=True)
        
        # NEW: Crop Selection & Sowing Date
        crop_list = list(CROP_DURATIONS.keys())
        crop_idx = crop_list.index(st.session_state.settings['crop']) if st.session_state.settings['crop'] in crop_list else 0
        sel_crop = st.selectbox("Current Crop", crop_list, index=crop_idx)
        
        sel_date = st.date_input("Sowing Date", value=st.session_state.settings['sowing_date'], max_value=datetime.date.today())

        st.markdown("---")
        l_idx = LANGUAGES.index(st.session_state.settings['language']) if st.session_state.settings['language'] in LANGUAGES else 0
        sel_lang = st.selectbox("Language", LANGUAGES, index=l_idx)
        st.caption("AI responses will automatically translate to your selected language.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 " + t('save'), use_container_width=True):
        st.session_state.settings.update({
            'country': sel_country, 'state': sel_state, 
            'soil_type': sel_soil, 'water_condition': sel_water, 
            'language': sel_lang, 'crop': sel_crop, 'sowing_date': sel_date
        })
        st.success("Settings Saved Successfully!")
        # Clear cached weather warning to force an update on home page
        st.session_state.weather_alert = None
        st.rerun()
