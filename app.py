import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. Load environment variables first
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AgroNova | Smart Farming AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM MODERN CSS STYLING ---
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background-color: #f8fcf8; 
    }
    h1, h2, h3 {
        font-family: 'Sans-serif';
        color: #2e7d32;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stChatMessage {
        animation: fadeIn 0.5s ease-out;
        border-radius: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .feature-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.15);
    }
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #4CAF50;
        color: #4CAF50;
        background-color: transparent;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #4CAF50;
        color: white;
    }
    [data-testid="stSidebar"] {
        background-color: #1b5e20;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.title("🌾 AgroNova")
    st.markdown("### *Empowering Farmers Globally*")
    st.markdown("---")
    
    # 2. Logic to check for .env key or Sidebar Input
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        # If no .env key found, ask in sidebar
        api_key = st.text_input(
            "Enter Gemini API Key", 
            type="password", 
            help="Get your key from Google AI Studio"
        )
    
    # 3. Configure the model if key is present
    if api_key:
        try:
            genai.configure(api_key=api_key)
            st.success("API Key Loaded! ✅")
        except Exception as e:
            st.error("Invalid API Key")
    else:
        st.warning("⚠️ Enter API Key to start")
    
    st.markdown("### 🌍 Settings")
    language = st.selectbox("Select Language / भाषा / idioma", 
                            ["English", "Hindi (हिंदी)", "Spanish (Español)", "French (Français)", "Swahili", "Punjabi"])
    
    st.markdown("---")
    st.markdown("### 🎯 Goals (SDGs)")
    st.info("✅ SDG 2: Zero Hunger")
    st.info("✅ SDG 13: Climate Action")
# ... inside the sidebar, after api_key is loaded ...
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            st.success("API Key Loaded! ✅")
            
            # --- DEBUGGING: PRINT AVAILABLE MODELS ---
            st.write("🔍 **Available Models for your Key:**")
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        st.code(m.name)
            except Exception as e:
                st.error(f"Could not list models: {e}")
            # -----------------------------------------

        except Exception as e:
            st.error("Invalid API Key")
# --- GEMINI MODEL FUNCTION ---
def get_gemini_response(prompt, lang_pref):
    if not api_key:
        return "⚠️ Please enter your API Key in the sidebar or .env file to start."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        full_prompt = f"""
        You are AgroNova, an expert agricultural AI assistant designed to support farmers globally. 
        Your goals are aligned with UN SDG 2 (Zero Hunger) and SDG 13 (Climate Action).
        
        **Your Persona:**
        - Friendly, empathetic, and practical.
        - Uses simple, jargon-free language suitable for farmers.
        - Knowledgeable about organic farming, pest control, crop cycles, and sustainable practices.
        
        **Current Context:**
        - User Language Preference: {lang_pref}
        - Specific Task: Provide advice on: {prompt}
        
        **Instructions:**
        1. Respond strictly in {lang_pref}.
        2. Keep the answer structured and actionable.
        3. If the query is about pests, prioritize organic/natural solutions first.
        """
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- MAIN UI LAYOUT ---
st.markdown("<h1 style='text-align: center; color: #2e7d32;'>🌱 AgroNova Smart Assistant</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #555;'>Sustainable Farming Solutions • {language}</p>", unsafe_allow_html=True)

# Feature Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="feature-card">🌿<br><b>Crop Doctor</b><br>Identify diseases</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="feature-card">🌦️<br><b>Climate Smart</b><br>Weather adaptation</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="feature-card">🐛<br><b>Pest Control</b><br>Organic solutions</div>', unsafe_allow_html=True)

st.write("") 

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Quick Questions
st.markdown("### Quick Questions / जल्दी पूछें:")
qp_cols = st.columns(4)
prompts = [
    "Best organic pesticide for tomatoes?",
    "How to save water in rice farming?", 
    "Suggest crops for sandy soil.",
    "Signs of nitrogen deficiency?"
]

if qp_cols[0].button("🍅 Organic Pesticides"):
    st.session_state.prompt_input = prompts[0]
if qp_cols[1].button("💧 Water Saving"):
    st.session_state.prompt_input = prompts[1]
if qp_cols[2].button("🏖️ Sandy Soil Crops"):
    st.session_state.prompt_input = prompts[2]
if qp_cols[3].button("🍂 Plant Health"):
    st.session_state.prompt_input = prompts[3]

# Handle Input
prompt = st.chat_input("Ask AgroNova anything about farming...", key="prompt_input_main")
# Check if a button was clicked (override prompt)
if "prompt_input" in st.session_state and st.session_state.prompt_input:
    prompt = st.session_state.prompt_input
    st.session_state.prompt_input = None # Reset after use

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            response = get_gemini_response(prompt, language)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 12px;'>AgroNova © 2025 | Built for UN SDG 2 & 13</div>", unsafe_allow_html=True)
