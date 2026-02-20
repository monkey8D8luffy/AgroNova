from dotenv import load_dotenv
import os
import streamlit as st
import google.generativeai as genai
import requests
import datetime
from PIL import Image

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
        'crop': 'Wheat', 'sowing_date': datetime.date.today() - datetime.timedelta(days=45),
        'gemini_key': os.getenv('GOOGLE_API_KEY', ''),
    }
    
    # Bulletproof initialization: Fill in ANY missing keys
    if 'settings' not in st.session_state: 
        st.session_state.settings = default_settings.copy()
    else:
        for key, value in default_settings.items():
            if key not in st.session_state.settings:
                st.session_state.settings[key] = value

    if 'page' not in st.session_state: st.session_state.page = 'Home'
    if 'searching' not in st.session_state: st.session_state.searching = False
    if 'chat_history' not in st.session_state: st.session_state.chat_history = []
    if 'show_history' not in st.session_state: st.session_state.show_history = False
    if 'show_news' not in st.session_state: st.session_state.show_news = False
    if 'uploaded_image' not in st.session_state: st.session_state.uploaded_image = None
    if 'settings_hash' not in st.session_state: st.session_state.settings_hash = str(default_settings)

init_session_state()

# --- HELPER: TRANSLATIONS & CONSTANTS ---
LANGUAGES = [
    "English", "Hindi", "Marathi", "Gujarati", "Tamil", "Telugu", "Kannada", "Malayalam", 
    "Bengali", "Punjabi", "Spanish", "French", "German", "Mandarin", "Arabic", "Russian", "Portuguese"
]

CROP_DURATIONS = {
    'Wheat': 120, 'Rice (Paddy)': 150, 'Maize (Corn)': 100, 'Sugarcane': 365,
    'Cotton': 160, 'Soybean': 95, 'Tomato': 70, 'Potato': 90
}

def t(key):
    translations = {
        'English': {'home': 'Home', 'profile': 'Profile', 'setting': 'Setting', 'search_placeholder': 'Ask anything about farming...', 'personalized_prompts': 'Personalized Prompts', 'weather': 'Weather', 'tips': 'Harvesting Tips', 'harvest': 'Harvest Countdown', 'seeds': 'Recommended Seeds', 'save': 'Save Settings', 'history': 'History', 'news': 'Local Ag News'},
    }
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
    return {"India": ["Maharashtra", "Punjab", "Gujarat"], "United States": ["California", "Texas"]}

@st.cache_data(ttl=1800)
def get_weather_warning(location):
    try:
        sanitized_loc = location.replace(" ", "+")
        url = f"https://wttr.in/{sanitized_loc}?format=j1"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            current_condition = data['current_condition'][0]['weatherDesc'][0]['value'].lower()
            temp_c = float(data['current_condition'][0]['temp_C'])
            
            SEVERE_CONDITIONS = ['thunder', 'torrential', 'heavy rain', 'snow', 'blizzard', 'flood', 'storm']
            
            if any(cond in current_condition for cond in SEVERE_CONDITIONS):
                return f"⚠️ SEVERE WEATHER ALERT: {current_condition.title()} detected in your area."
            elif temp_c > 40:
                return f"⚠️ HEATWAVE ALERT: Extreme temperatures ({temp_c}°C) detected."
    except Exception: pass
    return None

def configure_gemini():
    # 1. Check if user typed it in the Settings page
    key = st.session_state.settings.get('gemini_key')
    # 2. If not, check Streamlit Cloud Secrets
    if not key:
        try:
            key = st.secrets["GOOGLE_API_KEY"]
        except:
            pass
    # 3. If still not found, check local .env file
    if not key:
        key = os.getenv('GOOGLE_API_KEY')
        
    if key: 
        genai.configure(api_key=key)
        return True
    return False

def get_gemini_response(prompt, image=None):
    if not configure_gemini(): 
        return "⚠️ No API Key found. Please paste it in the Settings tab."
    try:
        # --- FIX: Changed from 2.0-flash to 1.5-flash for Free Tier compatibility ---
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        settings = st.session_state.settings
        crop = settings.get('crop', 'Wheat')
        settings_context = f"Context: User is a farmer in {settings.get('state', 'Maharashtra')}, {settings.get('country', 'India')}. Crop: {crop}. Soil: {settings.get('soil_type', 'Red Soil')}. Water: {settings.get('water_condition', 'Good')}. Respond EXCLUSIVELY in {settings.get('language', 'English')}."
        full_prompt = f"{settings_context}\nQuestion: {prompt}"
        response = model.generate_content([full_prompt, image]) if image else model.generate_content(full_prompt)
        return response.text
    except Exception as e: 
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg:
            return "⏳ AI is taking a quick break to prevent quota limits. Please wait 60 seconds and try your question again!"
        elif "400" in error_msg or "invalid" in error_msg:
            return "❌ API Key is invalid or expired. Please update it in the Settings tab."
        else:
            return f"❌ AI Connection Error: {str(e)}"
def get_dynamic_prompts():
    """STATIC, ZERO-QUOTA PROMPTS"""
    crop = st.session_state.settings.get('crop', 'Wheat')
    soil = st.session_state.settings.get('soil_type', 'Red Soil')
    
    return [
        f"Best fertilizer for {crop}?",
        f"How to improve {soil} health?",
        f"Water saving tips for {crop}?",
        f"Common pest control for {crop}?"
    ]

def get_harvesting_tips():
    """STATIC, ZERO-QUOTA HARVESTING TIPS"""
    crop = st.session_state.settings.get('crop', 'Wheat')
    
    tips_db = {
        'Wheat': "Monitor grain moisture to reach 14% before harvest. Ensure combine harvester blades are sharp to prevent shattering.",
        'Rice (Paddy)': "Drain the field 7-10 days before harvesting. Harvest when 80% of the panicles are straw-colored.",
        'Maize (Corn)': "Harvest when the black layer forms at the base of the kernels. Check for stalk rot before bringing machinery in.",
        'Sugarcane': "Stop irrigation 10-15 days before harvest to improve sugar recovery. Cut as close to the ground as possible.",
        'Cotton': "Pick cotton when bolls are fully open and dry. Avoid picking wet cotton to prevent discoloration and fungal growth.",
        'Soybean': "Harvest when pods are brown and beans rattle inside. Ideal moisture is around 13% to prevent splitting.",
        'Tomato': "Pick at the breaker stage (showing slight color) for long transport, or fully red for immediate local market sale.",
        'Potato': "Destroy vines 10-15 days before digging to allow the skin to set securely and reduce tuber damage during harvest."
    }
    return tips_db.get(crop, f"Monitor {crop} moisture levels closely before harvest. Ensure equipment is serviced to prevent field losses.")

def get_weather_data(): return {"temp": "28°C", "condition": "Partly Cloudy", "humidity": "65%"}

def get_agri_news(): 
    return [
        {"title": "New agricultural subsidies announced for drip irrigation", "source": "Ministry of Agriculture"},
        {"title": "Monsoon forecast upgraded to 'Above Normal'", "source": "Meteorological Dept"},
        {"title": "Global fertilizer prices see a 5% drop this month", "source": "Agri-Market Watch"},
        {"title": "New pest resistant cotton variety approved for trials", "source": "Research Council"}
    ]

# --- PROFESSIONAL UI/UX CSS ---
leaf_bg_url = "https://images.unsplash.com/photo-1533460004989-cef01064af7e?q=80&w=1920&auto=format&fit=crop" 

st.markdown(f"""
<style>
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .stApp {{ background-image: url('{leaf_bg_url}'); background-size: cover; background-attachment: fixed; background-position: center; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    h1, h2, h3, h4, h5, h6, p, span, label, div {{ color: #FFFFFF !important; font-family: 'Inter', sans-serif; }}
    .stMarkdown p, .stCaption p, small {{ color: #E2E8E0 !important; }}

    [data-testid="stVerticalBlockBorderWrapper"], .custom-card, [data-testid="stExpander"] {{
        background: rgba(20, 35, 25, 0.65) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
        padding: 15px; animation: fadeIn 0.5s ease-out;
    }}
    .custom-card {{ padding: 24px; margin-bottom: 20px; }}
    [data-testid="stAlert"] {{ background: rgba(220, 38, 38, 0.8) !important; color: white !important; border: none; }}

    .stButton > button {{
        background: rgba(255, 255, 255, 0.1) !important; backdrop-filter: blur(5px) !important;
        color: #FFFFFF !important; border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 25px !important; transition: all 0.3s ease !important;
    }}
    .stButton > button:hover {{ background: rgba(163, 230, 53, 0.3) !important; border-color: #A3E635 !important; transform: translateY(-2px); }}
    .icon-btn > button {{ border-radius: 50% !important; height: 50px; width: 50px; padding: 0 !important; display: flex; justify-content: center; align-items: center; font-size: 1.2rem; }}

    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input {{
        background: rgba(10, 20, 10, 0.7) !important; color: #FFFFFF !important;
        border-radius: 25px !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; padding: 10px 20px !important;
    }}
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus {{ border-color: #A3E635 !important; }}
    ::placeholder {{ color: rgba(255, 255, 255, 0.5) !important; }}

    [data-testid="stChatMessage"] {{
        background: rgba(0, 0, 0, 0.3); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.05); border-radius: 15px;
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
st.markdown("<br><br>", unsafe_allow_html=True)

# ================= PAGE: HOME =================
if st.session_state.page == 'Home':
    
    loc_string = f"{st.session_state.settings.get('state', 'Maharashtra')},{st.session_state.settings.get('country', 'India')}"
    warning = get_weather_warning(loc_string)
    if warning:
        st.error(warning, icon="⛈️")

    if not st.session_state.searching:
        st.markdown(f"<h1 style='text-align: center; font-size: 5.5rem; font-family: serif; letter-spacing: 5px; text-shadow: 2px 4px 15px rgba(0,0,0,0.6);'>AGRO NOVA</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.2rem; margin-bottom: 50px; opacity: 0.9;'>Your AI Farming Tool for {st.session_state.settings.get('state', 'Maharashtra')}</p>", unsafe_allow_html=True)

        with st.container():
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
                if st.button("🌍", help="News"): st.session_state.update(searching=True, show_news=True, show_history=False); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        if search_query:
            st.session_state.update(searching=True, show_history=False, show_news=False)
            with st.spinner("Analyzing..."):
                response = get_gemini_response(search_query, st.session_state.uploaded_image)
                st.session_state.chat_history.append([search_query, response])
                st.session_state.uploaded_image = None
            st.rerun()

        st.markdown(f"<br><h4 style='text-align:center; color: #A3E635 !important; font-weight:400;'>{t('personalized_prompts')}</h4>", unsafe_allow_html=True)
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
        show_h = st.session_state.show_history
        show_n = st.session_state.show_news
        
        if show_h and show_n:
            cols = st.columns([2.5, 7, 2.5]) 
        elif show_h:
            cols = st.columns([3, 8.5, 0.5])
        elif show_n:
            cols = st.columns([0.5, 8.5, 3])
        else:
            cols = st.columns([0.1, 11.8, 0.1])

        with cols[0]:
            if show_h:
                if st.button("✖ Close", key="cl_h", use_container_width=True): st.session_state.show_history=False; st.rerun()
                with st.container(height=550, border=True):
                    st.markdown(f"### {t('history')}")
                    for i, (user_msg, _) in enumerate(reversed(st.session_state.chat_history)):
                        st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:10px; margin-bottom:10px;'><small>**Q:** {user_msg[:35]}...</small></div>", unsafe_allow_html=True)
            else:
                 st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
                 if st.button("⏱️", key="op_h"): st.session_state.update(show_history=True, show_news=False); st.rerun()
                 st.markdown("</div>", unsafe_allow_html=True)

        with cols[1]:
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

        with cols[2]:
            if show_n:
                if st.button("✖ Close", key="cl_n", use_container_width=True): st.session_state.show_news=False; st.rerun()
                with st.container(height=550, border=True):
                    st.markdown(f"### {t('news')}")
                    for item in get_agri_news():
                        st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:10px; margin-bottom:10px;'><small>**{item['title']}**<br><span style='opacity:0.6;'>{item['source']}</span></small></div>", unsafe_allow_html=True)
            else:
                 st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
                 if st.button("🌍", key="op_n"): st.session_state.update(show_news=True, show_history=False); st.rerun()
                 st.markdown("</div>", unsafe_allow_html=True)

# ================= PAGE: PROFILE =================
elif st.session_state.page == 'Profile':
    col_p_left, col_p_right = st.columns([1, 2])
    
    current_crop = st.session_state.settings.get('crop', 'Wheat')

    with col_p_left:
        st.markdown(f"<div class='custom-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        st.markdown(f"<h3 style='margin-top:10px;'>{st.session_state.settings.get('name', 'Saurav')}</h3>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: left; margin-top: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"**📍 Location:** {st.session_state.settings.get('state', 'Maharashtra')}, {st.session_state.settings.get('country', 'India')}")
        st.markdown(f"**🌱 Soil:** {st.session_state.settings.get('soil_type', 'Red Soil')}")
        st.markdown(f"**🌾 Crop:** {current_crop}")
        st.markdown("</div></div>", unsafe_allow_html=True)

        with st.expander("✏️ Edit Name"):
             new_name = st.text_input("Name", st.session_state.settings.get('name', 'Saurav'))
             if st.button("Update"): st.session_state.settings['name'] = new_name; st.rerun()

    with col_p_right:
        st.markdown(f"<div class='custom-card'>", unsafe_allow_html=True)
        w_data = get_weather_data()
        c_w1, c_w2 = st.columns([1,3])
        with c_w1: st.markdown(f"<h1 style='color:#A3E635 !important; font-size:3rem;'>{w_data['temp']}</h1>", unsafe_allow_html=True)
        with c_w2: st.markdown(f"<h3>{t('weather')}</h3><p>{w_data['condition']}, Humidity: {w_data['humidity']}</p>", unsafe_allow_html=True)
        st.markdown("---")

        sowing_date = st.session_state.settings.get('sowing_date', datetime.date.today() - datetime.timedelta(days=45))
        total_days = CROP_DURATIONS.get(current_crop, 120)
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
             st.info(get_harvesting_tips()) # Instant load, no API call
        st.markdown("</div>", unsafe_allow_html=True)

# ================= PAGE: SETTING =================
elif st.session_state.page == 'Setting':
    st.markdown(f"<div class='custom-card'><h2 style='text-align:center;'>⚙️ {t('setting')}</h2></div>", unsafe_allow_html=True)
    
    country_dict = get_countries_and_states()
    country_list = list(country_dict.keys())
    
    c_s1, c_s2 = st.columns(2)

    with c_s1:
        st.markdown("<div class='custom-card'><h3>🌍 Location & Soil</h3>", unsafe_allow_html=True)
        
        current_country = st.session_state.settings.get('country', 'India')
        c_idx = country_list.index(current_country) if current_country in country_list else 0
        sel_country = st.selectbox("Country", country_list, index=c_idx)
        
        state_list = country_dict.get(sel_country, ["Select State"])
        current_state = st.session_state.settings.get('state', 'Maharashtra')
        s_idx = state_list.index(current_state) if current_state in state_list else 0
        sel_state = st.selectbox("State/Region", state_list, index=s_idx)
        
        soil_types = ['Red Soil', 'Black Cotton Soil', 'Alluvial Soil', 'Sandy Loam', 'Clayey', 'Laterite']
        current_soil = st.session_state.settings.get('soil_type', 'Red Soil')
        sel_soil = st.selectbox("Soil Type", soil_types, index=soil_types.index(current_soil) if current_soil in soil_types else 0)
        
        water_conds = ['Excellent (Irrigated)', 'Good (Seasonal)', 'Average', 'Poor (Rainfed)', 'Very Bad']
        current_water = st.session_state.settings.get('water_condition', 'Good')
        sel_water = st.selectbox("Water Condition", water_conds, index=water_conds.index(current_water) if current_water in water_conds else 1)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_s2:
        st.markdown("<div class='custom-card'><h3>🌾 Crop & Preferences</h3>", unsafe_allow_html=True)
        
        crop_list = list(CROP_DURATIONS.keys())
        current_crop = st.session_state.settings.get('crop', 'Wheat')
        crop_idx = crop_list.index(current_crop) if current_crop in crop_list else 0
        sel_crop = st.selectbox("Current Crop", crop_list, index=crop_idx)
        
        default_date = datetime.date.today() - datetime.timedelta(days=45)
        current_date = st.session_state.settings.get('sowing_date', default_date)
        sel_date = st.date_input("Sowing Date", value=current_date, max_value=datetime.date.today())

        st.markdown("---")
        
        current_lang = st.session_state.settings.get('language', 'English')
        l_idx = LANGUAGES.index(current_lang) if current_lang in LANGUAGES else 0
        sel_lang = st.selectbox("Language", LANGUAGES, index=l_idx)
        st.caption("AI responses will automatically translate to your selected language.")
        
        st.markdown("<h4 style='margin-top:20px;'>🔑 API Configuration</h4>", unsafe_allow_html=True)
        new_key = st.text_input("Gemini API Key", type="password", value=st.session_state.settings.get('gemini_key', ''))
        st.caption("Your API key is required to use AI features.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 " + t('save'), use_container_width=True):
        st.session_state.settings.update({
            'country': sel_country, 'state': sel_state, 
            'soil_type': sel_soil, 'water_condition': sel_water, 
            'language': sel_lang, 'crop': sel_crop, 'sowing_date': sel_date,
            'gemini_key': new_key
        })
        st.success("Settings Saved Successfully!")
        get_weather_warning.clear() 
        st.rerun()
