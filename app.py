import streamlit as st
import google.generativeai as genai
import os
import sys

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AgroNova Debugger", page_icon="🔧")

st.title("🔧 AgroNova Diagnostics")
st.write("If you are seeing this, the app is running. Let's find the error.")

# --- 1. CHECK LIBRARY VERSION ---
try:
    import google.generativeai
    st.info(f"📚 Google GenAI Library Version: `{google.generativeai.__version__}`")
    # We need at least version 0.5.0 for Flash.
    if google.generativeai.__version__ < "0.5.0":
        st.error("❌ YOUR LIBRARY IS TOO OLD. Update requirements.txt to: `google-generativeai>=0.8.3`")
except Exception as e:
    st.error(f"Library Error: {e}")

# --- 2. API KEY CHECK ---
api_key = os.getenv("GOOGLE_API_KEY")

# Fallback to sidebar if env var is missing
if not api_key:
    api_key = st.text_input("Enter Gemini API Key", type="password")

if not api_key:
    st.warning("⚠️ Enter API Key to continue debugging.")
    st.stop()

# --- 3. TEST MODELS ---
genai.configure(api_key=api_key)

st.write("---")
st.write("🔍 **Testing Connection to Google...**")

try:
    # Get list of models available to YOUR specific key
    models = list(genai.list_models())
    available_names = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
    
    if available_names:
        st.success(f"✅ Connection Successful! Found {len(available_names)} models.")
        st.write("### 📋 Copy one of these names into your code:")
        st.code(available_names)
        
        # Test the first working model
        test_model = available_names[0]
        st.write(f"🧪 **Attempting generation with: `{test_model}`...**")
        model = genai.GenerativeModel(test_model)
        response = model.generate_content("Say 'Hello Farmer'")
        st.success(f"🎉 It works! Response: {response.text}")
        
    else:
        st.error("❌ Connection worked, but no models are available for this API Key. This might be a region issue.")

except Exception as e:
    st.error(f"❌ CRITICAL ERROR: {str(e)}")
    st.write("This usually means the API Key is invalid or the Library version is incompatible.")
