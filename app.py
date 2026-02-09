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

# --- CSS STYLING (High Contrast & Interactive) ---
st.markdown("""
<style>
    /* 1. GLOBAL THEME */
    .stApp {
        background-color: #FFFFFF !important;
        color: #111111 !important;
    }
    
    /* 2. TYPOGRAPHY */
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-size: 48px !important;
        font-weight: 800;
        text-align: center;
        color: #1B5E20 !important;
        margin-top: -40px;
        margin-bottom: 20px;
    }

    /* 3. INTERACTIVE SEARCH BAR (The Glow Effect) */
    .stTextArea textarea {
        background-color: #F8F9FA !important;
        color: #000000 !important; /* Force Black Text */
        border: 2px solid #E0E0E0 !important;
        border-radius: 25px !important;
        font-size: 18px !important;
        padding: 20px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        transition: all 0.3s ease-in-out;
    }
    /* Focus State: Green Glow */
    .stTextArea textarea:focus {
        border-color: #4CAF50 !important;
        box-shadow: 0 0 15px rgba(76, 175, 80, 0.3) !important;
        transform: scale(1.01);
    }
    .stTextArea textarea::placeholder {
        color: #666666 !important;
    }

    /* 4. CHAT BUBBLES (History Above) */
    .chat-user {
        background-color: #F1F8E9;
        padding: 15px 20px;
        border-radius: 20px 20px 0 20px;
        margin: 10px 0;
        color: #1B5E20;
        text-align: right;
        font-weight: 500;
        border: 1px solid #C8E6C9;
        display: inline-block;
        float: right;
        clear: both;
        max-width: 80%;
    }
    .chat-ai {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 0 20px 20px 20px;
        margin: 10px 0;
        color: #333333;
        border: 1px solid #E0E0E0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        display: inline-block;
        float: left;
        clear: both;
        max-width: 90%;
    }
    
    /* 5. PROMPT TAGS (Pills below search) */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 1px solid #DDDDDD !important;
        border-radius: 50px !important;
        padding: 8px 16px !important;
        font-size: 13px !important;
        margin: 5px !important;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #E8F5E9 !important;
        border-color: #4CAF50 !important;
        color: #1B5E20 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Hide standard elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 API Key", type="password")
    
    if api_key:
        genai.configure(api_key=api_key)
    
    language = st.selectbox("Language / भाषा", ["English", "Marathi (मराठी)", "Hindi (हिंदी)"])
    st.info("📍 Region: Maharashtra")

# --- APP LOGIC ---

# 1. Initialize History
if "history" not in st.session_state:
    st.session_state.history = []

# 2. Hero Title
st.markdown('<div class="hero-title">AgroNova</div>', unsafe_allow_html=True)

# 3. DISPLAY CHAT HISTORY (Above Search Bar)
chat_container = st.container()
with chat_container:
    for chat in st.session_state.history:
        if chat["role"] == "user":
            st.markdown(f'<div class="chat-user">{chat["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-ai"><b>🌱 AgroNova:</b><br>{chat["content"]}</div>', unsafe_allow_html=True)
    
    # Add a spacer so the history doesn't hide behind the input immediately
    st.markdown("<div style='clear: both; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 4. SEARCH BAR (Center Stage)
st.write("---") # Visual separator
with st.form(key='search_form'):
    col_input, col_btn = st.columns([6, 1])
    
    with col_input:
        user_input = st.text_area(
            label="Query", 
            label_visibility="collapsed",
            placeholder="Ask anything... (e.g., 'Soybean rust treatment')",
            height=80
        )
    
    with col_btn:
        st.write("") # Spacer to align button
        st.write("") 
        submit_btn = st.form_submit_button("Ask ➔")

# 5. MAHARASHTRA PROMPTS (10 Common Questions)
st.markdown("### ⚡ Quick Prompts for Maharashtra:")

# Define prompts relevant to MH agriculture
mh_prompts = {
    "🥭 Alphonso Care": "Care tips for Alphonso Mango flowering stage?",
    "🧅 Onion Storage": "How to store onions to prevent rotting in Nashik climate?",
    "🍂 Soybean Rust": "Best fungicide for Soybean Rust disease?",
    "🦠 Cotton Bollworm": "Organic control for Pink Bollworm in Cotton?",
    "🌾 Sugarcane Yield": "Fertilizer schedule for high Sugarcane yield?",
    "🌧️ Monsoon Tips": "Farming tips for delayed monsoon in Maharashtra?",
    "🍅 Tomato Blight": "Treating early blight in Tomato plants?",
    "💰 PM Kisan": "How to check PM Kisan Samman Nidhi status?",
    "🍇 Grape Pruning": "Right time for October pruning in Grapes?",
    "🐄 Dairy Diet": "Balanced diet for buffaloes to increase milk fat?"
}

# Grid Layout for Buttons (2 Rows of 5)
row1 = st.columns(5)
row2 = st.columns(5)

prompt_selected = None

# Create buttons
idx = 0
for label, query in mh_prompts.items():
    # Place first 5 in row1, next 5 in row2
    target_row = row1 if idx < 5 else row2
    if target_row[idx % 5].button(label):
        prompt_selected = query
    idx += 1

# 6. HANDLE SUBMISSION
final_query = None

if submit_btn and user_input:
    final_query = user_input
elif prompt_selected:
    final_query = prompt_selected

if final_query:
    if not api_key:
        st.error("⚠️ Please enter API Key in sidebar")
    else:
        # 1. Add User Query to History
        st.session_state.history.append({"role": "user", "content": final_query})
        
        # 2. Get AI Response
        with st.spinner("👩‍🌾 AgroNova is thinking..."):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                full_prompt = f"""
                Act as an expert agronomist for Maharashtra, India.
                Language: {language}.
                Question: {final_query}
                
                Keep answers:
                - Practical and actionable for farmers.
                - Localized (mention Indian fertilizers/medicines if needed).
                - Brief (bullet points).
                """
                response = model.generate_content(full_prompt)
                ai_text = response.text
                
                # 3. Add AI Response to History
                st.session_state.history.append({"role": "assistant", "content": ai_text})
                
                # 4. Rerun to update the chat history above instantly
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
