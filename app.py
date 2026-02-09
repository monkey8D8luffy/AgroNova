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
    }
    
    /* 2. REMOVE PADDING to center things */
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 5rem !important;
        max_width: 900px !important;
    }

    /* 3. HERO TYPOGRAPHY */
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
        color: #666666 !important;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* 4. CENTERED INPUT BOX STYLING (Fixed Visibility) */
    .stTextArea textarea {
        background-color: #F8F9FA !important;
        color: #111111 !important; /* FORCE BLACK TEXT */
        border: 1px solid #E0E0E0 !important;
        border-radius: 20px !important;
        font-size: 18px !important;
        padding: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        height: 150px !important;
    }
    .stTextArea textarea:focus {
        box-shadow: 0 8px 24px rgba(0,0,0,0.1) !important;
        border-color: #1B5E20 !important;
    }
    /* Placeholder Color Fix */
    .stTextArea textarea::placeholder {
        color: #888888 !important;
    }

    /* 5. SUBMIT BUTTON STYLING (The 'Ask AI' Arrow) */
    [data-testid="stFormSubmitButton"] > button {
        background-color: #1B5E20 !important; /* Green Button */
        color: #FFFFFF !important; /* White Text */
        border: none !important;
        border-radius: 50px !important;
        padding: 10px 25px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 10px rgba(27, 94, 32, 0.3) !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #4CAF50 !important;
        transform: translateY(-2px);
    }

    /* 6. PILL BUTTONS (Quick Prompts) */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 30px !important;
        padding: 10px 24px !important;
        font-size: 14px !important;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    div.stButton > button:hover {
        background-color: #F1F8E9 !important;
        border-color: #1B5E20 !important;
        color: #1B5E20 !important;
    }
    
    /* 7. RESPONSE CARD STYLE */
    .response-box {
        background-color: #F1F8E9;
        border-radius: 16px;
        padding: 30px;
        margin-top: 30px;
        border: 1px solid #C8E6C9;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }
    /* Force text inside response box to be dark */
    .response-box, .response-box p, .response-box div {
        color: #111111 !important;
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
st.markdown('<div class="hero-title">Your AI Farming Tool,<br>Now in AgroNova</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Ask about crops, pests, or weather in Maharashtra</div>', unsafe_allow_html=True)

# --- CENTERED INPUT LOGIC ---
with st.form(key='search_form'):
    col_center = st.columns([1, 10, 1])[1] 
    with col_center:
        user_input = st.text_area(
            label="Input", 
            label_visibility="collapsed",
            placeholder="Type your question here... (e.g., 'How to treat white spots on tomato leaves?')",
        )
        
        # Action Row inside the form
        c1, c2, c3 = st.columns([6, 1, 1])
        with c3:
            submit_button = st.form_submit_button(label="Ask AI ➔")

# --- QUICK PROMPT PILLS ---
st.markdown("<br>", unsafe_allow_html=True) 
col1, col2, col3 = st.columns(3)

# Logic to handle Pill Clicks
clicked_prompt = None

if col1.button("🥭 Alphonso Care"):
    clicked_prompt = "Give me a care schedule for Alphonso Mango flowering stage."
if col2.button("🌾 Sugarcane Yield"):
    clicked_prompt = "Best fertilizers to increase Sugarcane tonnage in Maharashtra."
if col3.button("🦠 Cotton Pests"):
    clicked_prompt = "Organic control for Pink Bollworm in Cotton."

# --- GENERATION LOGIC ---
final_query = None
if submit_button and user_input:
    final_query = user_input
elif clicked_prompt:
    final_query = clicked_prompt

# --- DISPLAY RESULT ---
if final_query:
    if not api_key:
        st.error("Please enter your API Key in the sidebar first.")
    else:
        with st.spinner("Analyzing..."):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                full_prompt = f"""
                Act as an expert agronomist. Language: {language}.
                Question: {final_query}
                Keep it practical, bulleted, and regional to Maharashtra.
                """
                response = model.generate_content(full_prompt)
                
                # Render the result
                st.markdown(f"""
                <div class="response-box">
                    <h3 style="color:#1B5E20; margin-top:0;">🌱 AgroNova Advice</h3>
                    <div style="color:#333; font-size:16px; line-height:1.6;">
                        {response.text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error: {e}")

# Footer Spacer
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center; color:#999;'>AgroNova • Built for Sustainable Future</div>", unsafe_allow_html=True)
