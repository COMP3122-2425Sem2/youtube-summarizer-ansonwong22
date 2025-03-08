import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API credentials from environment variables or Streamlit Secrets
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", st.secrets.get("OPENROUTER_API_KEY"))
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY", st.secrets.get("GITHUB_API_KEY"))
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT", st.secrets.get("OPENROUTER_API_ENDPOINT"))
GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT", st.secrets.get("GITHUB_API_ENDPOINT"))
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME", st.secrets.get("OPENROUTER_API_MODEL_NAME"))
GITHUB_API_MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME", st.secrets.get("GITHUB_API_MODEL_NAME"))

# Validate API keys
if not OPENROUTER_API_KEY and not GITHUB_API_KEY:
    st.error("Missing API Key. Please set up the API keys in your environment variables or Streamlit Secrets.")
    st.stop()

# Streamlit App UI
st.title("YouTube Summarizer App")
st.write("Enter a YouTube video URL to generate a structured summary.")

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")

# Language selection
LANGUAGES = {
    "English": "en",
    "Simplified Chinese": "zh-CN",
    "Traditional Chinese": "zh-TW",
    "Spanish": "es",
    "French": "fr",
    "German": "de"
}
selected_language = st.selectbox("Choose Summary Language", list(LANGUAGES.keys()))

# Summary Detail Level
summary_type = st.radio("Select Summary Type", ["Basic", "Detailed"])

# Extract video ID
def extract_video_id(video_url):
    import re
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", video_url)
    return match.group(1) if match else None

# Fetch YouTube transcript
def fetch_transcript(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid YouTube URL. Please enter a valid video URL.")
        return None

    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}"

    try:
        response = requests.get(proxy_api_url)
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Transcript not found. Using English summary for translation. (Error: {response.status_code})")
            return None
    except requests.exceptions.RequestException as e:
        st.error("Failed to fetch transcript. Check your network connection.")
        return None

# Generate Summary using AI
def generate_summary(transcript_text, detail_level="Basic", language="English"):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"Summarize this transcript in {language}. Format it with structured sections."
    if detail_level == "Detailed":
        prompt += " Provide an in-depth summary."
    else:
        prompt += " Keep it short and concise."

    data = {
        "model": OPENROUTER_API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post(OPENROUTER_API_ENDPOINT, json=data, headers=headers)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            st.error(f"Error generating summary. API Response: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error("Error connecting to AI model API. Check your API key and internet connection.")
        return None

# Translate Summary if Needed
def translate_text(text, target_language_code):
    translation_api_url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text,
        "langpair": f"en|{target_language_code}"
    }

    try:
        response = requests.get(translation_api_url, params=params)
        if response.status_code == 200:
            return response.json()["responseData"]["translatedText"]
        else:
            st.warning(f"Translation API error. Returning English summary. (Error: {response.status_code})")
            return text
    except requests.exceptions.RequestException as e:
        st.warning("Translation failed. Returning English summary.")
        return text

# Process Summary
if video_url:
    transcript_data = fetch_transcript(video_url)

    if transcript_data:
        transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
    else:
        transcript_text = "No transcript available. AI will summarize in English."

    if st.button("Generate Summary"):
        summary_text = generate_summary(transcript_text, summary_type, "English")

        if summary_text:
            # Translate if the selected language is NOT English
            if LANGUAGES[selected_language] != "en":
                summary_text = translate_text(summary_text, LANGUAGES[selected_language])

            st.subheader("Generated Summary")
            st.write(summary_text)