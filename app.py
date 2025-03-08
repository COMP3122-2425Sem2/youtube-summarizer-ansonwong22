import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME")

# Ensure API credentials exist
if not OPENROUTER_API_KEY or not OPENROUTER_API_ENDPOINT:
    st.error("❌ API Key or API Endpoint is missing! Please check your .env file.")
    st.stop()

# Streamlit UI
st.title("YouTube Summarizer App")
video_url = st.text_input("Enter YouTube Video URL:")

# Language Selection
languages = {
    "English": "en",
    "Simplified Chinese": "zh-CN",
    "Traditional Chinese": "zh-TW",
    "Spanish": "es",
    "French": "fr",
    "German": "de"
}
selected_language = st.selectbox("Choose Summary Language", list(languages.keys()))
summary_type = st.radio("Select Summary Type", ["Basic", "Detailed"])

# Extract YouTube video ID
def extract_video_id(url):
    import re
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

# Fetch transcript from proxy API
def fetch_transcript(url):
    video_id = extract_video_id(url)
    if not video_id:
        st.error("❌ Invalid YouTube URL.")
        return None

    api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}"
    response = requests.get(api_url)

    if response.status_code == 200:
        return response.json()
    else:
        st.warning(f"⚠️ No transcript found. AI will summarize in English. (Error {response.status_code})")
        return None

# Generate AI Summary
def generate_summary(text, level="Basic", lang="English"):
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Summarize in {lang}. Use structured sections. {'Detailed' if level == 'Detailed' else 'Concise'}."

    data = {
        "model": OPENROUTER_API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "max_tokens": 500
    }
    
    response = requests.post(OPENROUTER_API_ENDPOINT, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "❌ Error generating summary")
    else:
        st.error(f"❌ API Error: {response.status_code} - {response.text}")
        return None

# Translate Text (if needed)
def translate_text(text, target_lang):
    if target_lang == "en":
        return text
    params = {"q": text, "langpair": f"en|{target_lang}"}
    response = requests.get("https://api.mymemory.translated.net/get", params=params)
    return response.json().get("responseData", {}).get("translatedText", text)

# Process and Display Summary
if video_url and st.button("Generate Summary"):
    transcript = fetch_transcript(video_url)
    
    if transcript:
        transcript_text = " ".join([t['text'] for t in transcript['transcript']])
    else:
        transcript_text = "No transcript available."

    # Generate summary in English
    summary = generate_summary(transcript_text, summary_type, "English")
    
    if summary:
        # Translate summary if needed
        summary = translate_text(summary, languages[selected_language])
        
        st.subheader("Summary")
        st.write(summary)