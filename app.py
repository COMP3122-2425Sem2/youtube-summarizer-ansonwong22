import streamlit as st
import requests
import os
import json
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API credentials from .env file or Streamlit Secrets
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", st.secrets.get("OPENROUTER_API_KEY"))
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY", st.secrets.get("GITHUB_API_KEY"))

OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT", st.secrets.get("OPENROUTER_API_ENDPOINT"))
GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT", st.secrets.get("GITHUB_API_ENDPOINT"))

OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME", st.secrets.get("OPENROUTER_API_MODEL_NAME"))
GITHUB_API_MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME", st.secrets.get("GITHUB_API_MODEL_NAME"))

# Language options for summary
LANGUAGE_OPTIONS = {
    "English": "en",
    "Traditional Chinese": "zh-Hant",
    "Simplified Chinese": "zh-CN"
}

# Streamlit UI
st.title("YouTube Summarizer")
video_url = st.text_input("Enter YouTube Video URL:")
selected_language = st.selectbox("Select Summary Language:", list(LANGUAGE_OPTIONS.keys()))

# Function to extract video ID
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# Fetch transcript
def fetch_transcript(video_id, lang_code):
    api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?language_code={lang_code}&password=for_demo&video_id={video_id}"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        return response.json()["transcript"]
    else:
        st.error(f"Failed to fetch transcript. Error Code: {response.status_code}")
        return None

# Generate summary
def generate_summary(text, detail_level="basic"):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": f"Summarize the following text in {selected_language}. Make it {detail_level}."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 500
    }
    response = requests.post(OPENROUTER_API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Error generating summary. API Response: {response.status_code}")
        return None

# Generate structured summary with timestamps
def generate_detailed_summary(text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": f"Provide a detailed, structured summary with timestamps for this transcript in {selected_language}."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 1000
    }
    response = requests.post(OPENROUTER_API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Error generating detailed summary. API Response: {response.status_code}")
        return None

# Process transcript
if video_url:
    video_id = extract_video_id(video_url)
    if video_id:
        transcript_data = fetch_transcript(video_id, LANGUAGE_OPTIONS[selected_language])
        if transcript_data:
            transcript_text = " ".join([segment["text"] for segment in transcript_data])
            st.subheader("Transcript")
            st.text_area("Full Transcript", transcript_text, height=200)

            if st.button("Generate Basic Summary"):
                summary_text = generate_summary(transcript_text, "basic")
                if summary_text:
                    st.subheader("Summary")
                    st.write(summary_text)

            if st.button("Generate Detailed Summary"):
                detailed_summary_text = generate_detailed_summary(transcript_text)
                if detailed_summary_text:
                    st.subheader("Detailed Summary")
                    st.write(detailed_summary_text)

            if st.button("Download Summary"):
                summary_file = f"summary_{video_id}.html"
                with open(summary_file, "w", encoding="utf-8") as f:
                    f.write(summary_text)
                st.download_button("Download as HTML", data=summary_text, file_name=summary_file)