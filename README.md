
```markdown
# 🌿 AgroNova AI: The Smart Farming Assistant

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/AI-Google%20Gemini-orange.svg" alt="Google Gemini API">
  <img src="https://img.shields.io/badge/Status-Deployed-success.svg" alt="Status">
</div>

<br>

**AgroNova AI** is a highly localized, context-aware digital agronomist. Built with Python, Streamlit, and Google's Gemini Generative AI, it translates complex agricultural data into real-time, actionable insights for farmers globally. 

By analyzing user-specific variables like soil type, water availability, crop type, and location, AgroNova AI provides instant, region-specific advice in over 15 native languages.

---

## 🚀 Live Demo
**[Click here to try AgroNova AI on Streamlit Cloud](#)** *(Replace '#' with your actual deployed URL)*

---

## ✨ Features

* **🧠 Context-Aware AI Chatbot:** Powered by `gemini-1.5-flash` with dynamic fallback to `gemini-pro`. The AI tailors every response to your specific geographic and environmental settings.
* **🌍 Multilingual Support:** Natively translates complex farming advice into languages including English, Hindi, Marathi, Spanish, French, and more.
* **⚡ Zero-Quota Smart Prompts:** Generates location- and crop-specific questions (e.g., "Best fertilizer for Wheat in Red Soil?") instantly, saving typing time without consuming API limits.
* **⛈️ Real-Time Severe Weather Alerts:** Integrates with the `wttr.in` API to actively monitor your state and trigger dashboard warnings for heatwaves, severe storms, or heavy rainfall.
* **⏳ Harvest Countdown Tracker:** Automatically calculates your crop's maturation cycle based on the sowing date and displays a dynamic progress bar to harvest.
* **📸 Multimodal Image Analysis:** Allows farmers to upload pictures of their crops or soil for the AI to analyze diseases or nutrient deficiencies.
* **🛡️ Quota-Safe Architecture:** Engineered with advanced `try/except` fallbacks. If API rate limits are hit or cloud servers are regionally blocked, the app gracefully degrades to built-in agricultural databases, remaining 100% functional.

---

## 🛠️ Technology Stack

* **Frontend:** Streamlit, Custom Glassmorphism CSS
* **Backend:** Python 3.x
* **Generative AI:** Google Generative AI SDK (`google-generativeai`)
* **External APIs:** * `wttr.in` (Weather Data)
  * `CountriesNow API` (Dynamic Location Selection)
* **Libraries:** `requests`, `python-dotenv`, `Pillow` (Image Processing)

---

## 💻 Local Installation & Setup

Want to run AgroNova AI on your own machine? Follow these steps:

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/AgroNova-AI.git](https://github.com/yourusername/AgroNova-AI.git)
cd AgroNova-AI

```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Configure Environment Variables

Create a file named `.env` in the root directory and add your Google AI Studio API key:

```env
GOOGLE_API_KEY="your_api_key_goes_here"

```

*(You can obtain a free API key from [Google AI Studio](https://aistudio.google.com/))*

### 5. Run the Application

```bash
streamlit run app.py

```

---

## ☁️ Cloud Deployment (Streamlit Community Cloud)

If you are deploying this repository to the web using Streamlit Cloud, the server cannot read your local `.env` file. You must securely provide your API key via Streamlit Secrets.

1. Go to your app's dashboard on [Streamlit Cloud](https://share.streamlit.io/).
2. Click **Manage App** in the bottom right corner.
3. Click the **⋮ (Settings)** icon in the top right menu and select **Settings**.
4. Navigate to the **Secrets** tab.
5. Add your key using standard TOML formatting:
```toml
GOOGLE_API_KEY="your_api_key_goes_here"

```


6. Click **Save** and reboot your app.

---

## 📂 Project Structure

```text
AgroNova-AI/
├── app.py               # Main Streamlit application and UI logic
├── requirements.txt     # Python package dependencies
├── .env                 # Local API keys (Ensure this is in .gitignore!)
├── .gitignore           # Specifies files ignored by version control
└── README.md            # Project documentation

```





http://googleusercontent.com/youtube_content/0

```
