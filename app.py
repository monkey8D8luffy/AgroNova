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
    'Hindi': {'home': 'होम', 'profile': 'प्रोफाइल', 'setting': 'सेटिंग', 'search_placeholder': 'खेती के बारे में कुछ भी पूछें...', 'personalized_prompts': 'आपके क्षेत्र के लिए व्यक्तिगत सुझाव', 'weather': 'मौसम', 'tips': 'खेती के टिप्स', 'harvest': 'फसल की उल्टी गिनती', 'seeds': 'अनुशंसित उच्च उपज वाले बीज', 'save': 'सेटिंग्स सहेजें', 'dark_mode': 'डार्क मोड', 'history': 'इतिहास', 'news': 'स्थानीय कृषि समाचार', 'send': 'भेजें'},
}
def t(key):
    lang = st.session_state.settings.get('language', 'English')
    return translations.get(lang, translations['English']).get(key, key)

# --- HELPER: NEW MODERN UI/UX THEMES ---

# Light Theme: Fresh, high-contrast, clean
light_theme = """
    --bg-main: #F4F7F5;          /* Very soft grey-green background */
    --bg-card: #FFFFFF;          /* Pure white cards */
    --text-main: #1C2B23;        /* Very dark green/grey for ultimate readability */
    --text-muted: #5A6D62;       /* Medium green/grey for secondary text */
    --accent-primary: #2E7D32;   /* Strong agricultural green */
    --accent-hover: #1B5E20;     /* Darker green for hover states */
    --border-color: #E0E8E3;     /* Soft border */
    --input-bg: #FFFFFF;         /* White input boxes */
    --shadow: 0 4px 12px rgba(46, 125, 50, 0.08);
"""

# Dark Theme: Deep, rich, low eye-strain
dark_theme = """
    --bg-main: #0B120E;          /* Very dark forest background */
    --bg-card: #14221A;          /* Slightly lighter dark green for cards */
    --text-main: #E8F5E9;        /* Soft mint white for high readability */
    --text-muted: #A3B8AC;       /* Muted mint for secondary text */
    --accent-primary: #66BB6A;   /* Bright natural green */
    --accent-hover: #81C784;     /* Lighter green for hover states */
    --border-color: #21362A;     /* Dark border */
    --input-bg: #0B120E;         /* Dark input boxes */
    --shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
"""

current_theme = dark_theme if st.session_state.settings['dark_mode'] else light_theme

st.markdown(f"""
<style>
    :root {{
        {current_theme}
    }}
    
    /* Backgrounds */
    .stApp {{
        background-color: var(--bg-main);
    }}
    
    /* Enforce Global Text Colors for Readability */
    h1, h2, h3, h4, h5, h6, p, span, label, div {{
        color: var(--text-main) !important;
        font-family: 'Inter', sans-serif;
    }}
    .stMarkdown p, .stCaption p {{
        color: var(--text-muted) !important;
    }}

    /* Card Containers */
    [data-testid="stVerticalBlockBorderWrapper"], .custom-card {{
        background-color: var(--bg-card) !important;
        border-radius: 16px !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: var(--shadow) !important;
        padding: 5px;
    }}
    .custom-card {{
        padding: 24px;
        margin-bottom: 20px;
    }}

    /* Navigation Pills */
    .nav-pills {{
        display: flex;
        justify-content: center;
        gap: 12px;
        padding-bottom: 24px;
    }}
    .nav-pill-btn {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        padding: 10px 24px;
        color: var(--text-main);
        cursor: pointer;
        transition: all 0.2s ease;
        font-weight: 600;
        box-shadow: var(--shadow);
    }}
    .nav-pill-btn:hover {{
        border-color: var(--accent-primary);
        color: var(--accent-primary);
    }}
    .nav-active {{
        background-color: var(--accent-primary) !important;
        color: #ffffff !important; /* Always white text on active pill */
        border-color: var(--accent-primary) !important;
    }}

    /* Inputs & Selectboxes */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
    }}
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 1px var(--accent-primary) !important;
    }}
    .stSelectbox div[data-baseweb="select"] span {{
        color: var(--text-main) !important;
    }}

    /* Chat Elements */
    [data-testid="stChatMessage"] {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
    }}

    /* Hide standard header/footer */
    #MainMenu, footer, header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# --- HELPER: API INTEGRATIONS ---
def configure_gemini():
    key = st.session_state.settings.get('gemini_key')
    if key: genai.configure(api_key=key)
    return key is not None and key != ''

def get_gemini_response(prompt, image=None):
    if not configure_gemini(): return "⚠️ Please set your Google Gemini API Key in Settings."
    try:
        model_name = 'gemini-2.0-flash'
        model = genai.GenerativeModel(model_name)
        settings_context = f"Context: User is a farmer in {st.session_state.settings['state']}, {st.session_state.settings['country']}. Soil: {st.session_state.settings['soil_type']}. Water: {st.session_state.settings['water_condition']}. Respond in {st.session_state.settings['language']}."
        full_prompt = f"{settings_context}\nQuestion: {prompt}"

        if image:
            response = model.generate_content([full_prompt, image])
        else:
            response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        error_msg = f"Error: {e}."
        if "404" in str(e) or "not found" in str(e).lower():
            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                error_msg += f" \nAvailable models: {', '.join(available_models)}"
            except: pass
        return error_msg

def get_personalized_prompts():
    loc = f"{st.session_state.settings['state']}, {st.session_state.settings['country']}"
    return [
        f"Best crop rotation plan for {loc}?",
        f"How to improve {st.session_state.settings['soil_type']} health organically?",
        f"Water saving techniques for {st.session_state.settings['water_condition']} availability.",
        "Current market prices for major crops in my mandi.",
        "Pest control measures for Fall Armyworm.",
        "Government subsidies available for drip irrigation.",
        "Weather forecast impact on sowing this week.",
        "Optimal fertilizer schedule for sugarcane.",
    ]

def get_weather_data():
    return {"temp": "28°C", "condition": "Partly Cloudy", "humidity": "65%"}

def get_agri_news():
    return [
        {"title": "New MSP announced for Kharif crops", "source": "AgriNews"},
        {"title": "Monsoon expected to be normal this year", "source": "WeatherDept"},
        {"title": "New organic farming scheme launched in state", "source": "Govt press"},
    ]

def get_seed_recommendations():
    return ["Hybrid Wheat DBW 187 (High Yield)", "Drought Tolerant Maize PMH 1"]

# --- NAVIGATION LOGIC ---
c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
with c2:
    if st.button(t('home'), key='nav_home', use_container_width=True):
        if st.session_state.page == 'Home' and st.session_state.searching:
             st.session_state.searching = False
        st.session_state.page = 'Home'
        st.rerun()
with c3:
    if st.button(t('profile'), key='nav_profile', use_container_width=True):
        st.session_state.page = 'Profile'
        st.session_state.searching = False
        st.rerun()
with c4:
    if st.button(t('setting'), key='nav_setting', use_container_width=True):
        st.session_state.page = 'Setting'
        st.session_state.searching = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ================= PAGE: HOME =================
if st.session_state.page == 'Home':

    if not st.session_state.searching:
        # Accent color applied directly to main title
        st.markdown(f"<h1 style='text-align: center; font-size: 3.5rem; font-weight: 800; color: var(--accent-primary) !important;'>AGRO NOVA</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.2rem;'>Your AI Farming Tool for {st.session_state.settings['state']}</p><br>", unsafe_allow_html=True)

        with st.container():
            col_hist, col_search, col_news = st.columns([1, 6, 1])
            with col_hist:
                if st.button("📜", help="History"):
                    st.session_state.searching = True
                    st.session_state.show_history = True
                    st.session_state.show_news = False
                    st.rerun()
            with col_search:
                search_query = st.chat_input(t('search_placeholder'))
                with st.expander("➕ Add Image/File for analysis", expanded=False):
                     uploaded_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
                     if uploaded_file:
                         st.session_state.uploaded_image = Image.open(uploaded_file)
                         st.image(st.session_state.uploaded_image, width=200)
            with col_news:
                if st.button("📰", help="News"):
                    st.session_state.searching = True
                    st.session_state.show_news = True
                    st.session_state.show_history = False
                    st.rerun()

        if search_query:
            st.session_state.searching = True
            st.session_state.show_history = False
            st.session_state.show_news = False

            with st.spinner("Analyzing..."):
                response = get_gemini_response(search_query, st.session_state.uploaded_image)
                st.session_state.chat_history.append([search_query, response])
                st.session_state.uploaded_image = None
            st.rerun()

        st.markdown(f"<br><h3>{t('personalized_prompts')}</h3>", unsafe_allow_html=True)
        prompts = get_personalized_prompts()

        p_cols = st.columns(2)
        for i, prompt in enumerate(prompts):
            col_idx = i % 2
            with p_cols[col_idx]:
                 if st.button(prompt, key=f"prompt_{i}", use_container_width=True):
                     st.session_state.searching = True
                     with st.spinner("Thinking..."):
                        response = get_gemini_response(prompt)
                        st.session_state.chat_history.append([prompt, response])
                     st.rerun()

    # --- POST-SEARCH / CHAT VIEW ---
    else:
        hist_col_width = 2 if st.session_state.show_history else 0.1
        news_col_width = 2 if st.session_state.show_news else 0.1
        chat_col_width = 8

        c_hist, c_chat, c_news = st.columns([hist_col_width, chat_col_width, news_col_width])

        with c_hist:
            if st.session_state.show_history:
                if st.button("← Close", key="close_hist"):
                    st.session_state.show_history=False
                    st.rerun()

                with st.container(height=550, border=True):
                    st.markdown(f"<h3>{t('history')}</h3>", unsafe_allow_html=True)
                    for i, (user_msg, ai_msg) in enumerate(reversed(st.session_state.chat_history)):
                        st.markdown(f"**Q:** {user_msg[:30]}...")
                        if st.button("🗑️ Delete", key=f"del_{i}", help="Delete Chat"):
                            actual_idx = len(st.session_state.chat_history) - 1 - i
                            st.session_state.chat_history.pop(actual_idx)
                            st.rerun()
                        st.markdown("---")
            else:
                 if st.button("📜 History", key="open_hist", use_container_width=True):
                     st.session_state.show_history = True
                     st.session_state.show_news = False
                     st.rerun()

        with c_chat:
             chat_container = st.container(height=550, border=True)
             with chat_container:
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
                if st.button("Close →", key="close_news"):
                     st.session_state.show_news=False
                     st.rerun()

                with st.container(height=550, border=True):
                    st.markdown(f"<h3>{t('news')}</h3>", unsafe_allow_html=True)
                    news_items = get_agri_news()
                    for item in news_items:
                        st.markdown(f"**{item['title']}**")
                        st.markdown(f"<small>{item['source']}</small>", unsafe_allow_html=True)
                        st.markdown("---")
            else:
                 if st.button("📰 News", key="open_news", use_container_width=True):
                     st.session_state.show_news = True
                     st.session_state.show_history = False
                     st.rerun()

# ================= PAGE: PROFILE =================
elif st.session_state.page == 'Profile':
    col_p_left, col_p_right = st.columns([1, 2])

    with col_p_left:
        st.markdown(f"<div class='custom-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=120)
        st.markdown(f"<h3>{st.session_state.settings['name']}</h3>")

        st.markdown("<div style='text-align: left; margin-top: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"**📍 Location:** {st.session_state.settings['state']}, {st.session_state.settings['country']}")
        st.markdown(f"**🌱 Soil:** {st.session_state.settings['soil_type']}")
        st.markdown(f"**💧 Water:** {st.session_state.settings['water_condition']}")
        st.markdown("</div></div>", unsafe_allow_html=True)

        with st.expander("Edit Basic Info"):
             new_name = st.text_input("Name", st.session_state.settings['name'])
             if st.button("Update Name"):
                 st.session_state.settings['name'] = new_name
                 st.rerun()

    with col_p_right:
        st.markdown(f"<div class='custom-card'>", unsafe_allow_html=True)

        w_data = get_weather_data()
        c_w1, c_w2 = st.columns([1,3])
        with c_w1: st.markdown(f"<h1 style='color: var(--accent-primary) !important;'>{w_data['temp']}</h1>", unsafe_allow_html=True)
        with c_w2: st.markdown(f"<h3>{t('weather')}</h3><p>{w_data['condition']}, Humidity: {w_data['humidity']}</p>", unsafe_allow_html=True)
        st.markdown("---")

        c_h1, c_h2 = st.columns(2)
        with c_h1:
             st.markdown(f"<h3>⏳ {t('harvest')}</h3>", unsafe_allow_html=True)
             st.markdown("<h2 style='color: var(--accent-primary) !important;'>45 Days</h2>", unsafe_allow_html=True)
             st.markdown("<p>*(Wheat)*</p>", unsafe_allow_html=True)
        with c_h2:
             st.markdown(f"<h3>🌾 {t('seeds')}</h3>", unsafe_allow_html=True)
             for seed in get_seed_recommendations():
                 st.markdown(f"- {seed}")
        st.markdown("---")

        st.markdown(f"<h3>💡 {t('tips')}</h3>", unsafe_allow_html=True)
        tip_prompt = f"Give 3 short, critical farming tips for {st.session_state.settings['state']} right now considering {st.session_state.settings['water_condition']} water."
        if 'profile_tips' not in st.session_state:
             with st.spinner("Loading personalized tips..."):
                 st.session_state.profile_tips = get_gemini_response(tip_prompt)

        st.write(st.session_state.profile_tips)
        st.markdown("</div>", unsafe_allow_html=True)

# ================= PAGE: SETTING =================
elif st.session_state.page == 'Setting':
    st.markdown(f"<div class='custom-card'><h2>{t('setting')}</h2></div>", unsafe_allow_html=True)

    with st.form("settings_form"):
        c_s1, c_s2 = st.columns(2)

        with c_s1:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Location & Soil</h3>", unsafe_allow_html=True)

            all_countries = dict(countries_for_language('en'))
            country_names = list(all_countries.values())
            current_country_idx = country_names.index(st.session_state.settings['country']) if st.session_state.settings['country'] in country_names else 0

            sel_country = st.selectbox("Country", country_names, index=current_country_idx)

            states = ["Maharashtra", "Punjab", "Karnataka", "California", "Texel"] if sel_country in ['India', 'United States', 'Netherlands'] else ["Region 1", "Region 2"]
            current_state_idx = states.index(st.session_state.settings['state']) if st.session_state.settings['state'] in states else 0
            sel_state = st.selectbox("State/Region", states, index=current_state_idx)

            soil_types = ['Red Soil', 'Black Cotton Soil', 'Alluvial Soil', 'Sandy Loam', 'Clayey']
            sel_soil = st.selectbox("Soil Type", soil_types, index=soil_types.index(st.session_state.settings['soil_type']))

            water_conditions = ['Excellent (Irrigated)', 'Good (Seasonal)', 'Average', 'Poor (Rainfed)', 'Very Bad (Drought Prone)']
            water_idx = 1
            if 'Good' in st.session_state.settings['water_condition']: water_idx = 1
            elif 'Excellent' in st.session_state.settings['water_condition']: water_idx = 0

            sel_water = st.selectbox("Water Condition", water_conditions, index=water_idx)
            st.markdown("</div>", unsafe_allow_html=True)

        with c_s2:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.markdown("<h3>App Preferences</h3>", unsafe_allow_html=True)

            langs = ['English', 'Hindi', 'Marathi', 'Spanish', 'French']
            sel_lang = st.selectbox("Language", langs, index=langs.index(st.session_state.settings['language']))

            sel_dark_mode = st.toggle(t('dark_mode'), value=st.session_state.settings['dark_mode'])

            st.markdown("---")
            st.markdown("<h3>🔑 API Keys</h3>", unsafe_allow_html=True)
            key_gemini = st.text_input("Google Gemini API Key", value=st.session_state.settings['gemini_key'], type="password")
            key_weather = st.text_input("OpenWeatherMap Key", value=st.session_state.settings['weather_key'], type="password")
            key_news = st.text_input("NewsAPI Key", value=st.session_state.settings['news_key'], type="password")
            st.caption("Get keys from Google AI Studio, OpenWeatherMap, and NewsAPI.org")
            st.markdown("</div>", unsafe_allow_html=True)

        if st.form_submit_button(t('save')):
            st.session_state.settings['country'] = sel_country
            st.session_state.settings['state'] = sel_state
            st.session_state.settings['soil_type'] = sel_soil
            st.session_state.settings['water_condition'] = sel_water
            st.session_state.settings['language'] = sel_lang
            st.session_state.settings['dark_mode'] = sel_dark_mode
            st.session_state.settings['gemini_key'] = key_gemini
            st.session_state.settings['weather_key'] = key_weather
            st.session_state.settings['news_key'] = key_news
            st.success("Settings Saved!")
            st.rerun()
