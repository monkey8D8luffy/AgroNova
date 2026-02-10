import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AgroNova UI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS: THE GLASSMORPHISM ENGINE ---
st.markdown("""
<style>
    /* 1. BACKGROUND IMAGE (Dark Leaves) */
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?q=80&w=2727&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    /* 2. REMOVE DEFAULT STREAMLIT PADDING */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max_width: 1200px;
    }
    
    /* 3. CUSTOM NAVIGATION BAR (The Top Pill) */
    div.stButton > button {
        background-color: rgba(255, 255, 255, 0.25) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 25px !important;
        font-weight: 500 !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.5) !important;
        transform: scale(1.05);
        color: #1a4a1c !important; /* Dark Green Text on Hover */
    }
    /* Active State styling (simulated) */
    div.stButton > button:focus {
        background-color: #8FBC8F !important;
        color: #000 !important;
        border-color: #8FBC8F !important;
    }

    /* 4. GLASS CONTAINERS (The Box Effect) */
    .glass-box {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 30px;
        margin-bottom: 20px;
        color: white;
    }

    /* 5. SEARCH BAR STYLING (Home Page) */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-radius: 30px !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        padding: 15px 20px !important;
        font-size: 16px !important;
    }
    .stTextInput input::placeholder {
        color: #e0e0e0 !important;
    }
    /* Focus state */
    .stTextInput input:focus {
        background-color: rgba(255, 255, 255, 0.3) !important;
        border-color: white !important;
        box-shadow: 0 0 15px rgba(255,255,255,0.3) !important;
    }

    /* 6. LIST ITEMS (The Horizontal Bars) */
    .glass-list-item {
        background: rgba(255, 255, 255, 0.1);
        margin: 10px 0;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        text-align: center;
        transition: transform 0.2s;
        cursor: pointer;
    }
    .glass-list-item:hover {
        background: rgba(255, 255, 255, 0.25);
        transform: scale(1.02);
    }

    /* 7. CHAT MESSAGE STYLES */
    .chat-bubble-user {
        background: rgba(76, 175, 80, 0.6);
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        margin-bottom: 10px;
        text-align: right;
        float: right;
        clear: both;
        color: white;
        border: 1px solid rgba(255,255,255,0.3);
    }
    .chat-bubble-ai {
        background: rgba(255, 255, 255, 0.2);
        padding: 10px 15px;
        border-radius: 0 15px 15px 15px;
        margin-bottom: 10px;
        text-align: left;
        float: left;
        clear: both;
        color: white;
        border: 1px solid rgba(255,255,255,0.3);
    }

    /* Hide standard elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;} /* Hide sidebar for full immersion */
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE & NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- TOP NAVIGATION BAR (Pills) ---
# We use columns to center the buttons at the top
col_spacer1, col_nav1, col_nav2, col_nav3, col_spacer2 = st.columns([4, 1, 1, 1, 4])

with col_nav1:
    if st.button("Home"):
        st.session_state.page = 'Home'
with col_nav2:
    if st.button("Profile"):
        st.session_state.page = 'Profile'
with col_nav3:
    if st.button("Setting"):
        st.session_state.page = 'Setting'

st.markdown("<br><br>", unsafe_allow_html=True) # Spacing after nav

# --- PAGE 1: HOME (Search Bar + Glass Lists) ---
if st.session_state.page == 'Home':
    
    # 1. Centered Search Bar
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        search_query = st.text_input("Search", placeholder="Ask anything about farming... 🔍", label_visibility="collapsed")
        
        if search_query:
            # If user types here, we can redirect to chat or show results
            # For this UI demo, let's just save it and move to profile/chat
            st.session_state.chat_history.append({"role": "user", "content": search_query})
            st.session_state.page = 'Profile'
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Glass List Items (The horizontal bars in your image)
    # These are functional buttons disguised as glass bars
    c_list1, c_list2, c_list3 = st.columns([1, 2, 1])
    with c_list2:
        # Prompt 1
        st.markdown('<div class="glass-list-item">🍅 Best organic fertilizer for tomatoes?</div>', unsafe_allow_html=True)
        # Prompt 2
        st.markdown('<div class="glass-list-item">💧 How to save water in paddy fields?</div>', unsafe_allow_html=True)
        # Prompt 3
        st.markdown('<div class="glass-list-item">🐛 Identification of Cotton pests</div>', unsafe_allow_html=True)
        # Prompt 4
        st.markdown('<div class="glass-list-item">🚜 Subsidy for drip irrigation in MH</div>', unsafe_allow_html=True)

# --- PAGE 2: PROFILE (The Chat Interface) ---
elif st.session_state.page == 'Profile':
    
    # We use a 3-column layout to center the "Glass Modal"
    col_l, col_main, col_r = st.columns([1, 4, 1])
    
    with col_main:
        # OPEN GLASS CONTAINER
        st.markdown('<div class="glass-box" style="min-height: 500px;">', unsafe_allow_html=True)
        
        # 1. Chat History Display
        # We manually render HTML bubbles to match the glass style
        if not st.session_state.chat_history:
             st.markdown("<h3 style='text-align:center; color:rgba(255,255,255,0.7);'>AgroNova Chat</h3>", unsafe_allow_html=True)
        
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.markdown(f'<div class="chat-bubble-user">{chat["content"]}</div><div style="clear:both"></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble-ai">{chat["content"]}</div><div style="clear:both"></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True) # Close glass box
        
        # 2. Input Area (Outside the box or inside, based on pref. Image shows inside bottom)
        # Streamlit inputs are hard to put INSIDE a div, so we put it right below
        with st.form(key='chat_form', clear_on_submit=True):
            cols = st.columns([8, 1])
            with cols[0]:
                user_input = st.text_input("Message", placeholder="Type your message...", label_visibility="collapsed")
            with cols[1]:
                submit = st.form_submit_button("➤")
            
            if submit and user_input:
                # Add User Message
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # AI Logic
                api_key = os.getenv("GOOGLE_API_KEY")
                response_text = "Please set your API Key in Settings."
                
                if api_key:
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content(user_input)
                        response_text = response.text
                    except Exception as e:
                        response_text = "Sorry, I'm having trouble connecting."
                
                st.session_state.chat_history.append({"role": "ai", "content": response_text})
                st.rerun()

# --- PAGE 3: SETTINGS ---
elif st.session_state.page == 'Setting':
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="glass-box">', unsafe_allow_html=True)
        st.markdown("### ⚙️ Settings")
        
        # API Key Input (Styled transparently via CSS above)
        api_key_input = st.text_input("Google API Key", type="password", value=os.getenv("GOOGLE_API_KEY") or "")
        if api_key_input:
            os.environ["GOOGLE_API_KEY"] = api_key_input
            st.success("Key Saved!")
            
        st.markdown("---")
        st.markdown("### 👤 User Info")
        st.text_input("Name", value="Rajesh Kumar")
        st.selectbox("Language", ["English", "Hindi", "Marathi"])
        
        st.markdown('</div>', unsafe_allow_html=True)
