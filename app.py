import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv  # Import this to read .env

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AgroNova | Smart Farming AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ... [Keep your CSS Styles here unchanged] ...

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.title("🌾 AgroNova")
    st.markdown("### *Empowering Farmers Globally*")
    st.markdown("---")
    
    # NEW: Logic to check for .env key first
    api_key = os.getenv("GOOGLE_API_KEY")

    # If no key in .env, ask for it in the sidebar
    if not api_key:
        api_key = st.text_input("Enter Gemini API Key", type="password", help="Get your key from Google AI Studio")
    
    # Configure the model
    if api_key:
        genai.configure(api_key=api_key)
        st.success("API Key Loaded! ✅")
    else:
        st.warning("⚠️ Please enter an API Key to continue")
    
    st.markdown("### 🌍 Settings")
    # ... [Rest of your sidebar code] ...

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.title("🌾 AgroNova")
    st.markdown("### *Empowering Farmers Globally*")
    st.markdown("---")
    
    # API Key Handling
    api_key = st.text_input("Enter Gemini API Key", type="password", help="Get your key from Google AI Studio")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        genai.configure(api_key=api_key)
    
    st.markdown("### 🌍 Settings")
    language = st.selectbox("Select Language / भाषा / idioma", 
                            ["English", "Hindi (हिंदी)", "Spanish (Español)", "French (Français)", "Swahili", "Punjabi"])
    
    st.markdown("---")
    st.markdown("### 🎯 Goals (SDGs)")
    st.info("✅ SDG 2: Zero Hunger")
    st.info("✅ SDG 13: Climate Action")

# --- GEMINI MODEL SETUP ---
def get_gemini_response(prompt, context_instruction):
    if not api_key:
        return "⚠️ Please enter your API Key in the sidebar to start."
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        # Combined system instruction + user prompt
        full_prompt = f"""
        You are AgroNova, an expert agricultural AI assistant designed to support farmers globally. 
        Your goals are aligned with UN SDG 2 (Zero Hunger) and SDG 13 (Climate Action).
        
        **Your Persona:**
        - Friendly, empathetic, and practical.
        - Uses simple, jargon-free language suitable for farmers.
        - Knowledgeable about organic farming, pest control, crop cycles, and sustainable practices.
        - Adaptable to the region mentioned (e.g., India, Africa, Americas).
        
        **Current Context:**
        - User Language Preference: {language}
        - Specific Task: Provide advice on: {prompt}
        
        **Instructions:**
        1. Respond strictly in {language}.
        2. Keep the answer structured (bullet points are good) and actionable.
        3. If the query is about pests, prioritize organic/natural solutions first.
        4. Mention climate-smart practices where relevant.
        """
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- MAIN UI LAYOUT ---

# Hero Section
st.markdown("<h1 style='text-align: center; color: #2e7d32;'>🌱 AgroNova Smart Assistant</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #555;'>Sustainable Farming Solutions • {language}</p>", unsafe_allow_html=True)

# Feature Quick-Select (Visual decoration mainly)
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="feature-card">🌿<br><b>Crop Doctor</b><br>Identify diseases</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="feature-card">🌦️<br><b>Climate Smart</b><br>Weather adaptation</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="feature-card">🐛<br><b>Pest Control</b><br>Organic solutions</div>', unsafe_allow_html=True)

st.write("") # Spacer

# --- CHAT INTERFACE ---

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Quick Prompt Buttons (Dynamic based on logic or language could be added here)
st.markdown("### Quick Questions / जल्दी पूछें:")
qp_cols = st.columns(4)
prompts = [
    "Best organic pesticide for tomatoes?",
    "How to save water in rice farming?", 
    "Suggest crops for sandy soil.",
    "Signs of nitrogen deficiency?"
]

def set_prompt(text):
    st.session_state.prompt_input = text

# Logic to handle button clicks effectively
if qp_cols[0].button("🍅 Organic Pesticides"):
    st.session_state.prompt_input = prompts[0]
if qp_cols[1].button("💧 Water Saving"):
    st.session_state.prompt_input = prompts[1]
if qp_cols[2].button("🏖️ Sandy Soil Crops"):
    st.session_state.prompt_input = prompts[2]
if qp_cols[3].button("🍂 Plant Health"):
    st.session_state.prompt_input = prompts[3]

# Chat Input
if prompt := st.chat_input("Ask AgroNova anything about farming...", key="prompt_input"):
    # 1. Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing agricultural data..."):
            response = get_gemini_response(prompt, language)
            st.markdown(response)
    
    # 3. Add assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 12px;'>AgroNova © 2025 | Built for UN SDG 2 & 13 | Powered by Google Gemini</div>", unsafe_allow_html=True)
