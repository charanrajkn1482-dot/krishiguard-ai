import re
import time
from io import BytesIO
import requests
import streamlit as st
from PIL import Image
from gtts import gTTS
from google import genai
from google.genai import types

st.set_page_config(
    page_title="KrishiGuard AI — Autonomous Agritech Agent",
    page_icon="🌾",
    layout="wide",
)

# --- 1. AUTONOMOUS AGENT TOOLS ---
def get_live_weather(city: str) -> dict:
    """Fetches real-time temperature, humidity, rainfall, and 3-day forecast for a city."""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=10).json()
        if not geo_res.get("results"):
            return {"error": f"Location '{city}' not found.", "temp_c": 28.0, "humidity": 70, "rain_3day_mm": 0.0}

        loc = geo_res["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
            "&timezone=auto&forecast_days=3"
        )
        w_res = requests.get(weather_url, timeout=10).json()
        current = w_res.get("current", {})
        daily = w_res.get("daily", {})
        rain_3day = round(sum(daily.get("precipitation_sum", [0])), 1)

        data = {
            "location": f"{loc.get('name')}, {loc.get('admin1', '')}",
            "temp_c": current.get("temperature_2m", 28.0),
            "humidity_percent": current.get("relative_humidity_2m", 70),
            "wind_kmh": current.get("wind_speed_10m", 10.0),
            "rain_3day_mm": rain_3day,
            "daily_max_c": daily.get("temperature_2m_max", []),
        }
        st.session_state["last_weather"] = data
        return data
    except Exception as e:
        return {"error": str(e), "temp_c": 28.0, "humidity_percent": 70, "rain_3day_mm": 0.0}


def calculate_resource_plan(crop: str, acres: float, soil_type: str, rain_3day_mm: float) -> dict:
    """Calculates precision irrigation water savings and NPK fertilizer dosage."""
    base_water_per_acre = 18000 if "paddy" in crop.lower() or "rice" in crop.lower() else 9500
    total_standard_liters = base_water_per_acre * acres

    rain_factor = 0.55 if rain_3day_mm > 15 else (0.30 if rain_3day_mm > 3 else 0.15)
    soil_factor = 0.10 if "black" in soil_type.lower() or "clay" in soil_type.lower() else 0.0
    savings_pct = min(0.65, rain_factor + soil_factor)

    liters_saved = int(total_standard_liters * savings_pct)
    recommended_liters = int(total_standard_liters - liters_saved)
    fertilizer_saved_inr = int(acres * 1450)

    plan = {
        "crop": crop,
        "acres": acres,
        "soil_type": soil_type,
        "recommended_water_liters": recommended_liters,
        "water_saved_liters": liters_saved,
        "water_savings_percent": int(savings_pct * 100),
        "fertilizer_cost_saved_inr": fertilizer_saved_inr,
        "npk_ratio": "10:26:26 + Zinc Micronutrient" if "paddy" in crop.lower() else "19:19:19 Foliar + Neem Cake",
    }
    st.session_state["last_plan"] = plan
    return plan


LANG_MAP = {
    "English": "en",
    "Kannada (ಕನ್ನಡ)": "kn",
    "Hindi (हिन्दी)": "hi",
    "Tamil (தமிழ்)": "ta",
    "Telugu (తెలుగు)": "te",
    "Marathi (मराठी)": "mr",
    "Malayalam (മലയാളം)": "ml",
    "Bengali (বাংলা)": "bn",
    "Gujarati (ગુજરાતી)": "gu",
}

def generate_voice_audio(text: str, lang_label: str) -> bytes:
    """Cleans markdown and synthesizes fast native speech audio."""
    clean_text = re.sub(r"[#*`_>\-\[\]\(\)]", " ", text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()[:900]
    lang_code = LANG_MAP.get(lang_label, "en")
    tts = gTTS(text=clean_text, lang=lang_code, slow=False)
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()

# --- 2. SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.header("⚙️ Agent Control Panel")
    try:
        default_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        default_key = ""

    api_key = st.text_input(
        "Gemini API Key",
        value=default_key,
        type="password",
        placeholder="Auto-loaded or paste AIza... key",
    )
    language = st.selectbox(
        "Farmer Language (Text + Voice)",
    list(LANG_MAP.keys())
    )
    enable_voice = st.checkbox("🔊 Generate Voice Audio Advisory", value=True)
    st.divider()
    st.markdown("**Autonomous Agent Tools:**")
    st.markdown("1. 🌦️ Open-Meteo Live Weather API\n2. 💧 Precision Resource Optimizer\n3. 🌿 Multimodal Leaf Vision\n4. 🗣️ Native Voice Synthesizer")

# --- 3. MAIN DASHBOARD ---
st.title("🌾 KrishiGuard AI — Autonomous Multilingual Agritech & Resource Agent")
st.caption("Track 02: Climate, Resource Infrastructure & Global Supply Resilience | IDEA//FORGE")

col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("1. Farm & Resource Inputs")
    city = st.text_input("Village / Town / City", value="Shivamogga")
    c_a, c_b = st.columns(2)
    with c_a:
        crop = st.text_input("Crop Name", value="Paddy (Rice)")
    with c_b:
        acres = st.number_input("Farm Size (Acres)", min_value=0.5, max_value=500.0, value=2.0, step=0.5)
    soil_type = st.selectbox("Soil Type", ["Red Soil", "Black Cotton Soil", "Alluvial Soil", "Laterite Soil", "Sandy Loam"])
    symptoms = st.text_area(
        "Describe Crop Symptoms or Question",
        value="Leaves are turning yellow at the tips and weather has been humid. How much water and fertilizer should I use?",
        height=90,
    )

with col2:
    st.subheader("2. Leaf / Crop Disease Scanner")
    uploaded_file = st.file_uploader("Upload a leaf or crop photo for instant AI diagnosis", type=["jpg", "jpeg", "png"])
    image = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Crop Sample", use_container_width=True)

run_btn = st.button("🚀 Run Autonomous KrishiGuard Agent", type="primary", use_container_width=True)

# --- 4. AGENT EXECUTION PIPELINE ---
if run_btn:
    if not api_key:
        st.warning("⚠️ Please open the left sidebar (>>) and paste your Gemini API Key first.")
        st.stop()

    st.session_state["last_weather"] = None
    st.session_state["last_plan"] = None

    with st.status("🤖 KrishiGuard Agent is executing autonomous workflow...", expanded=True) as status:
        try:
            client = genai.Client(api_key=api_key.strip())

            st.write("🌦️ Step 1: Fetching live micro-climate & 3-day rainfall telemetry...")
            weather_snapshot = get_live_weather(city)

            st.write("💧 Step 2: Computing precision irrigation & fertilizer savings...")
            resource_snapshot = calculate_resource_plan(
                crop=crop,
                acres=acres,
                soil_type=soil_type,
                rain_3day_mm=weather_snapshot.get("rain_3day_mm", 0.0),
            )

            st.write(f"🧠 Step 3: Synthesizing multimodal diagnosis & {language} advisory...")
            prompt = f"""
You are KrishiGuard AI, an expert autonomous agritech & climate-resilience advisor for Indian farmers.
Analyze the farm telemetry below (and the attached leaf photo if present) and respond in **{language}**.

FARMER DATA:
- Location: {city}
- Crop: {crop} ({acres} acres) | Soil: {soil_type}
- Farmer Question/Symptoms: {symptoms}
- Live Weather Data: {weather_snapshot}
- Precision Resource Calculation: {resource_snapshot}

Provide a clear, practical response with these exact 4 sections:
1. **Crop Health & Disease Diagnosis** (analyze symptoms & uploaded leaf photo if provided)
2. **3-Day Climate & Irrigation Action Plan** (reference exact temperature, humidity, and water savings)
3. **Soil & Fertilizer Dosage** (exact NPK & organic remedy)
4. **Preventive Supply-Chain & Yield Tip**
"""
            contents = [prompt]
            if image:
                contents.append(image)

            response = None
            last_error = None
            available = [
                m.name.replace("models/", "")
                for m in client.models.list()
                if "gemini" in m.name.lower() and "flash" in m.name.lower()
            ]
            models_to_try = list(dict.fromkeys(["gemini-3.9-flash"] + available))

            for model_name in models_to_try:
                for attempt in range(3):
                    try:
                        res = client.models.generate_content(
                            model=model_name,
                            contents=contents,
                            config=types.GenerateContentConfig(temperature=0.3),
                        )
                        if res and res.text:
                            response = res
                            break
                    except Exception as err:
                        last_error = err
                        if "503" in str(err) or "429" in str(err):
                            st.write(f"⏳ High server demand on {model_name}, retrying ({attempt + 2}/3)...")
                            time.sleep(2)
                        else:
                            break
                if response:
                    break

            if not response:
                raise last_error or RuntimeError("Model returned an empty response.")

            status.update(label="✅ Autonomous Agent Workflow Complete!", state="complete", expanded=False)

            # --- KPI IMPACT METRICS ---
            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🌡️ Live Temp", f"{weather_snapshot.get('temp_c', 'N/A')} °C", f"{weather_snapshot.get('humidity_percent', 0)}% Humidity")
            m2.metric("🌧️ 3-Day Rain Forecast", f"{weather_snapshot.get('rain_3day_mm', 0)} mm")
            m3.metric("💧 Water Saved", f"{resource_snapshot['water_saved_liters']:,} L", f"-{resource_snapshot['water_savings_percent']}% vs Flood")
            m4.metric("💰 Input Cost Saved", f"₹{resource_snapshot['fertilizer_cost_saved_inr']:,}", "Precision NPK")

            # --- ADVISORY OUTPUT ---
            st.markdown(f"### 📋 Personalized Farmer Advisory ({language})")
            st.markdown(response.text)

            # --- AUDIO & EXPORT ---
            c_audio, c_dl = st.columns([2, 1])
            with c_audio:
                if enable_voice:
                    st.markdown("### 🔊 Listen in Native Language")
                    audio_bytes = generate_voice_audio(response.text, language)
                    st.audio(audio_bytes, format="audio/mp3")
            with c_dl:
                st.markdown("### 📄 Farmer Action Card")
                st.download_button(
                    label="⬇️ Download Advisory Report",
                    data=response.text,
                    file_name=f"KrishiGuard_{city}_{crop}.txt",
                    mime="text/plain",
                )

            with st.expander("🔍 View Autonomous Tool Telemetry (Judge Proof)"):
                st.json({"weather_tool_output": weather_snapshot, "resource_tool_output": resource_snapshot})

        except Exception as e:
            status.update(label="❌ Agent Execution Failed", state="error")
            st.error(f"Error details: {repr(e)}")