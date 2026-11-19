# 🌾 KrishiGuard AI — Autonomous Multilingual Agritech & Resource Agent

**Track 02:** Climate, Resource Infrastructure & Global Supply Resilience | **IDEA//FORGE**  
**Live App:** [krishiguard-ai-app.streamlit.app](https://krishiguard-ai-app.streamlit.app)

---

## 🚀 Overview
**KrishiGuard AI** is an autonomous, multimodal AI agent designed to help smallholder farmers optimize water and fertilizer usage, diagnose crop diseases from leaf images, and receive actionable farming advisories in their local language—both as readable text and synthesized voice audio.

## ✨ Key Capabilities
* **Live Micro-Climate & Rainfall Telemetry:** Fetches real-time temperature, humidity, and 3-day precipitation forecasts via the Open-Meteo API based on the farmer's village or town.
* **Precision Resource Optimizer:** Calculates exact water savings (in liters) and fertilizer input cost reductions (in ₹) tailored to crop type, acreage, soil type, and upcoming rain.
* **Multimodal Leaf & Crop Disease Scanner:** Analyzes uploaded leaf or crop photos alongside text symptom descriptions using Google Gemini (`gemini-2.5-flash`) with automatic fallback/retry resilience.
* **Multilingual Text & Native Voice Synthesizer:** Delivers clear, jargon-free advisories in regional languages and generates playable audio via `gTTS` for accessibility in the field.

## 🛠️ Tech Stack
* **Frontend & Hosting:** Streamlit, Streamlit Community Cloud
* **AI & Vision Engine:** Google GenAI SDK (`google-genai`)
* **Weather Telemetry:** Open-Meteo REST API (`requests`)
* **Voice & Image Processing:** `gTTS`, `Pillow`

## ⚙️ Local Setup
1. Clone the repository:
   ```bash
   git clone [https://github.com/charanrajkn1482-dot/krishiguard-ai.git](https://github.com/charanrajkn1482-dot/krishiguard-ai.git)
   cd krishiguard-ai
