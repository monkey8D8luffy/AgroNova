from dotenv import load_dotenv
import os

load_dotenv() # This loads the keys from the .env file

# ... later in your session state initialization ...
default_settings = {
    # ... other settings ...
    # Load from .env if available, otherwise leave empty
    'gemini_key': os.getenv('GOOGLE_API_KEY', ''), 
    'weather_key': os.getenv('OPENWEATHER_KEY', ''),
    'news_key': os.getenv('NEWS_API_KEY', '')
}
import streamlit as st
import google.generativeai as genai
import requests
import json
from PIL import Image
import base64
import io
from country_list import countries_for_language

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
        'name': 'Farmer John', 'gemini_key': '', 'weather_key': '', 'news_key': ''
    }
    if 'settings' not in st.session_state: st.session_state.settings = default_settings
    if 'page' not in st.session_state: st.session_state.page = 'Home'
    if 'searching' not in st.session_state: st.session_state.searching = False
    if 'chat_history' not in st.session_state: st.session_state.chat_history = [] # List of [user_msg, ai_msg]
    if 'show_history' not in st.session_state: st.session_state.show_history = False
    if 'show_news' not in st.session_state: st.session_state.show_news = False
    if 'uploaded_image' not in st.session_state: st.session_state.uploaded_image = None

init_session_state()

# --- HELPER: TRANSLATIONS (Simplified Mockup) ---
# In a real app, this would be a comprehensive JSON or separate file.
translations = {
    'English': {'home': 'Home', 'profile': 'Profile', 'setting': 'Setting', 'search_placeholder': 'Ask anything about farming...', 'personalized_prompts': 'Personalized Prompts for your Area', 'weather': 'Weather', 'tips': 'Farming Tips', 'harvest': 'Harvest Countdown', 'seeds': 'Recommended High-Yield Seeds', 'save': 'Save Settings', 'dark_mode': 'Dark Mode', 'history': 'History', 'news': 'Local Ag News', 'send': 'Send'},
    'Hindi': {'home': 'होम', 'profile': 'प्रोफाइल', 'setting': 'सेटिंग', 'search_placeholder': 'खेती के बारे में कुछ भी पूछें...', 'personalized_prompts': 'आपके क्षेत्र के लिए व्यक्तिगत सुझाव', 'weather': 'मौसम', 'tips': 'खेती के टिप्स', 'harvest': 'फसल की उल्टी गिनती', 'seeds': 'अनुशंसित उच्च उपज वाले बीज', 'save': 'सेटिंग्स सहेजें', 'dark_mode': 'डार्क मोड', 'history': 'इतिहास', 'news': 'स्थानीय कृषि समाचार', 'send': 'भेजें'},
    # Add more languages here...
}
def t(key):
    lang = st.session_state.settings.get('language', 'English')
    return translations.get(lang, translations['English']).get(key, key)

# --- HELPER: CSS & ASSETS ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    img_base64 = get_base64_of_bin_file("image_22.png") # Ensure image_22.png is in the same folder
    bg_image_css = f'url("data:image/png;base64,{img_base64}")'
except FileNotFoundError:
    st.error("image_22.png not found. Please ensure it is in the app directory.")
    bg_image_css = ""

dark_mode_css = """
    --bg-overlay: rgba(0, 0, 0, 0.6);
    --glass-bg: rgba(0, 0, 0, 0.3);
    --text-color: #e0e0e0;
    --input-bg: rgba(255, 255, 255, 0.1);
""" if st.session_state.settings['dark_mode'] else """
    --bg-overlay: rgba(255, 255, 255, 0.1);
    --glass-bg: rgba(255, 255, 255, 0.25);
    --text-color: #ffffff;
    --input-bg: rgba(255, 255, 255, 0.3);
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
        color: var(--text-color);
    }}
    /*Glassmorphism Containers*/
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
    /*Nav Pills*/
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
    
    /*Inputs*/
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {{
        background-color: var(--input-bg) !important;
        color: var(--text-color) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }}
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {{ color: rgba(255,255,255,0.7) !important; }}
    
    /*Prompt Buttons*/
    .prompt-btn {{
        background: var(--glass-bg);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 12px; padding: 10px; margin: 5px;
        text-align: left; font-size: 0.9rem; cursor: pointer; transition: 0.2s;
    }}
    .prompt-btn:hover {{ transform: scale(1.02); background: rgba(255,255,255,0.3); color: #1a4a1c; }}

    /*Headings*/
    h1, h2, h3, h4, p, label {{ color: var(--text-color) !important; }}
    
    /*Hide default Elements*/
    #MainMenu, footer, header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# --- HELPER: API INTEGRATIONS (MOCK & REAL) ---
def configure_gemini():
    key = st.session_state.settings.get('gemini_key')
    if key: genai.configure(api_key=key)
    return key is not None and key != ''

def get_gemini_response(prompt, image=None):
    if not configure_gemini(): return "⚠️ Please set your Google Gemini API Key in Settings."
    try:
        model_name = 'gemini-pro-vision' if image else 'gemini-pro'
        model = genai.GenerativeModel(model_name)
        
        settings_context = f"Context: User is a farmer in {st.session_state.settings['state']}, {st.session_state.settings['country']}. Soil: {st.session_state.settings['soil_type']}. Water: {st.session_state.settings['water_condition']}. Respond in {st.session_state.settings['language']}."
        full_prompt = f"{settings_context}\nQuestion: {prompt}"

        if image:
            response = model.generate_content([full_prompt, image])
        else:
            response = model.generate_content(full_prompt)
        return response.text
    except Exception as e: return f"Error: {e}"

def get_personalized_prompts():
    # In a real app, call Gemini here. Returning mock for stability without keys.
    loc = f"{st.session_state.settings['state']}, {st.session_state.settings['country']}"
    return [
        f"Best crop rotation plan for {loc}?",
        f"How to improve {st.session_state.settings['soil_type']} health organically?",
        f"Water saving techniques for {st.session_state.settings['water_condition']} water availability.",
        "Current market prices for major crops in my mandi.",
        "Pest control measures for Fall Armyworm.",
        "Government subsidies available for drip irrigation.",
        "Weather forecast impact on sowing this week.",
        "Identify this plant disease (upload image).",
        "Optimal fertilizer schedule for sugarcane.",
        "Storage tips to prevent post-harvest losses."
    ]

def get_weather_data():
    # Needs OpenWeatherMap Key. Mock data below.
    return {"temp": "28°C", "condition": "Partly Cloudy", "humidity": "65%"}

def get_agri_news():
    # Needs NewsAPI Key. Mock data below.
    return [
        {"title": "New MSP announced for Kharif crops", "source": "AgriNews"},
        {"title": "Monsoon expected to be normal this year", "source": "WeatherDept"},
        {"title": "New organic farming scheme launched in state", "source": "Govt press"},
    ]

def get_seed_recommendations():
    # Mock data based on settings
    return ["Hybrid Wheat DBW 187 (High Yield)", "Drought Tolerant Maize PMH 1"]

# --- NAVIGATION LOGIC ---
def nav_button(label, page_name):
    active_class = "nav-active" if st.session_state.page == page_name and not st.session_state.searching else ""
    # Using HTML buttons within Markdown for custom styling, handling click via session state check next rerun
    st.markdown(f'<button class="nav-pill-btn {active_class}" id="btn_{page_name}">{label}</button>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
with c2:
    if st.button(t('home'), key='nav_home', use_container_width=True):
        # Double tap logic implementation for reset
        if st.session_state.page == 'Home' and st.session_state.searching:
             st.session_state.searching = False
        st.session_state.page = 'Home'
        st.rerun()
with c3:
    if st.button(t('profile'), key='nav_profile', use_container_width=True):
        st.session_state.page = 'Profile'
        st.session_state.searching = False # Ensure we exit search view
        st.rerun()
with c4:
    if st.button(t('setting'), key='nav_setting', use_container_width=True):
        st.session_state.page = 'Setting'
        st.session_state.searching = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True) # Spacer

# ================= PAGE: HOME =================
if st.session_state.page == 'Home':

    # --- PRE-SEARCH VIEW ---
    if not st.session_state.searching:
        st.markdown(f"<h1 style='text-align: center; font-size: 3.5rem; font-weight: 700; color: #aed581 !important;'>AGRO NOVA</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.2rem;'>Your AI Farming Tool for {st.session_state.settings['state']}</p><br>", unsafe_allow_html=True)

        # Search Bar Container
        with st.container():
            col_hist, col_search, col_news = st.columns([1, 6, 1])
            with col_hist:
                # Using buttons to simulate icons due to streamlit limitations inside inputs
                if st.button("📜", help="History"): 
                    st.session_state.searching = True
                    st.session_state.show_history = True
                    st.session_state.show_news = False
                    st.rerun()
            with col_search:
                search_query = st.chat_input(t('search_placeholder'))
                
                # Image Uploader (placed below search bar as "plus" icon inside is hard in pure streamlit)
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
            st.session_state.show_history = False # Default to chat view
            st.session_state.show_news = False
            
            # Process request
            with st.spinner("Analyzing..."):
                response = get_gemini_response(search_query, st.session_state.uploaded_image)
                st.session_state.chat_history.append([search_query, response])
                st.session_state.uploaded_image = None # Reset image after send
            st.rerun()

        # Personalized Prompts
        st.markdown(f"### {t('personalized_prompts')}")
        prompts = get_personalized_prompts()
        
        # Grid layout for prompts
        p_cols = st.columns(2)
        for i, prompt in enumerate(prompts):
            col_idx = i % 2
            with p_cols[col_idx]:
                 if st.button(prompt, key=f"prompt_{i}", use_container_width=True):
                     st.session_state.searching = True
                     # Simulate prompt submission
                     with st.spinner("Thinking..."):
                        response = get_gemini_response(prompt)
                        st.session_state.chat_history.append([prompt, response])
                     st.rerun()

    # --- POST-SEARCH / CHAT VIEW ---
    else:
        # Layout: History Panel | Main Chat | News Panel
        # We use columns and session state variables to toggle visibility, simulating "slide-in"
        
        hist_col_width = 2 if st.session_state.show_history else 0.1
        news_col_width = 2 if st.session_state.show_news else 0.1
        chat_col_width = 8
        
        c_hist, c_chat, c_news = st.columns([hist_col_width, chat_col_width, news_col_width])

        # --- HISTORY SIDEBAR ---
        with c_hist:
            if st.session_state.show_history:
                st.markdown(f"<div class='glass-container' style='height: 70vh; overflow-y: auto;'><h3>{t('history')}</h3>", unsafe_allow_html=True)
                if st.button("← Close", key="close_hist"): 
                    st.session_state.show_history=False
                    st.rerun()
                    
                for i, (user_msg, ai_msg) in enumerate(reversed(st.session_state.chat_history)):
                    with st.container():
                        st.markdown(f"**Q:** {user_msg[:30]}...")
                        if st.button("🗑️", key=f"del_{i}", help="Delete Chat"):
                            # Calculate actual index due to reversed loop
                            actual_idx = len(st.session_state.chat_history) - 1 - i
                            st.session_state.chat_history.pop(actual_idx)
                            st.rerun()
                        st.markdown("---")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                 # Collapsed state button
                 if st.button("📜 History", key="open_hist", use_container_width=True):
                     st.session_state.show_history = True
                     st.session_state.show_news = False
                     st.rerun()

        # --- MAIN CHAT AREA ---
        with c_chat:
             st.markdown(f"<div class='glass-container' style='height: 75vh; display: flex; flex-direction: column;'>", unsafe_allow_html=True)
             
             # Chat messages container (scrollable)
             chat_container = st.container(height=500, border=False)
             with chat_container:
                 for user_msg, ai_msg in st.session_state.chat_history:
                     with st.chat_message("user"): st.write(user_msg)
                     with st.chat_message("assistant", avatar="🌿"): st.write(ai_msg)

             # Chat Input
             new_query = st.chat_input("Ask follow-up...", key="chat_followup")
             if new_query:
                 with st.spinner("Thinking..."):
                    response = get_gemini_response(new_query)
                    st.session_state.chat_history.append([new_query, response])
                 st.rerun()
             st.markdown("</div>", unsafe_allow_html=True)

        # --- NEWS SIDEBAR ---
        with c_news:
            if st.session_state.show_news:
                st.markdown(f"<div class='glass-container' style='height: 70vh; overflow-y: auto;'><h3>{t('news')}</h3>", unsafe_allow_html=True)
                if st.button("Close →", key="close_news"):
                     st.session_state.show_news=False
                     st.rerun()
                
                news_items = get_agri_news()
                for item in news_items:
                    st.markdown(f"**{item['title']}**")
                    st.markdown(f"*{item['source']}*")
                    st.markdown("---")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                 if st.button("📰 News", key="open_news", use_container_width=True):
                     st.session_state.show_news = True
                     st.session_state.show_history = False
                     st.rerun()

# ================= PAGE: PROFILE =================
elif st.session_state.page == 'Profile':
    
    col_p_left, col_p_right = st.columns([1, 2])

    # Left Sidebar: Bio info
    with col_p_left:
        st.markdown(f"<div class='glass-container' style='text-align: center;'>", unsafe_allow_html=True)
        # Placeholder profile pic (replace with actual user image if implemented)
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=120)
        st.markdown(f"### {st.session_state.settings['name']}")
        
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

    # Right Side: Insights
    with col_p_right:
        st.markdown(f"<div class='glass-container'>", unsafe_allow_html=True)
        
        # Weather
        w_data = get_weather_data()
        c_w1, c_w2 = st.columns([1,3])
        with c_w1: st.markdown(f"# {w_data['temp']}")
        with c_w2: st.markdown(f"### {t('weather')}\n{w_data['condition']}, Humidity: {w_data['humidity']}")
        st.markdown("---")
        
        # Harvest Countdown & Seeds (Mock data)
        c_h1, c_h2 = st.columns(2)
        with c_h1:
             st.markdown(f"### ⏳ {t('harvest')}")
             st.markdown("## 45 Days")
             st.markdown("*(Wheat)*")
        with c_h2:
             st.markdown(f"### 🌾 {t('seeds')}")
             for seed in get_seed_recommendations():
                 st.write(f"- {seed}")
        st.markdown("---")

        # AI Tips based on location
        st.markdown(f"### 💡 {t('tips')}")
        tip_prompt = f"Give 3 short, critical farming tips for {st.session_state.settings['state']} right now considering {st.session_state.settings['water_condition']} water."
        # In real app, cache this response
        if 'profile_tips' not in st.session_state:
             with st.spinner("Loading personalized tips..."):
                 st.session_state.profile_tips = get_gemini_response(tip_prompt)
        
        st.write(st.session_state.profile_tips)
        st.markdown("</div>", unsafe_allow_html=True)


# ================= PAGE: SETTING =================
elif st.session_state.page == 'Setting':
    st.markdown(f"<div class='glass-container'><h2>{t('setting')}</h2></div>", unsafe_allow_html=True)

    with st.form("settings_form"):
        c_s1, c_s2 = st.columns(2)
        
        with c_s1:
            st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
            st.markdown("### Location & Soil")
            
            # Dynamic Country/State loading
            all_countries = dict(countries_for_language('en'))
            country_names = list(all_countries.values())
            current_country_idx = country_names.index(st.session_state.settings['country']) if st.session_state.settings['country'] in country_names else 0
            
            sel_country = st.selectbox("Country", country_names, index=current_country_idx)
            
            # Mock States - In real app use a library or API based on selected country
            states = ["Maharashtra", "Punjab", "Karnataka", "California", "Texel"] if sel_country in ['India', 'United States', 'Netherlands'] else ["Region 1", "Region 2"]
            current_state_idx = states.index(st.session_state.settings['state']) if st.session_state.settings['state'] in states else 0
            sel_state = st.selectbox("State/Region", states, index=current_state_idx)

            soil_types = ['Red Soil', 'Black Cotton Soil', 'Alluvial Soil', 'Sandy Loam', 'Clayey']
            sel_soil = st.selectbox("Soil Type", soil_types, index=soil_types.index(st.session_state.settings['soil_type']))
            
            water_conditions = ['Excellent (Irrigated)', 'Good (Seasonal)', 'Average', 'Poor (Rainfed)', 'Very Bad (Drought Prone)']
            # Simple index matching for mock data
            water_idx = 1
            if 'Good' in st.session_state.settings['water_condition']: water_idx = 1
            elif 'Excellent' in st.session_state.settings['water_condition']: water_idx = 0
            
            sel_water = st.selectbox("Water Condition", water_conditions, index=water_idx)
            st.markdown("</div>", unsafe_allow_html=True)

        with c_s2:
            st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
            st.markdown("### App Preferences")
            
            langs = ['English', 'Hindi', 'Marathi', 'Spanish', 'French']
            sel_lang = st.selectbox("Language", langs, index=langs.index(st.session_state.settings['language']))
            
            sel_dark_mode = st.toggle(t('dark_mode'), value=st.session_state.settings['dark_mode'])
            
            st.markdown("---")
            st.markdown("### 🔑 API Keys (Required for AI features)")
            # Using text_input with type='password' for keys
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
