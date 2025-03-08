import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API credentials from .env file
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME")

# Validate API credentials
if not OPENROUTER_API_KEY or not OPENROUTER_API_ENDPOINT or not OPENROUTER_API_MODEL_NAME:
    st.error("Error: Missing API Key or Endpoint. Check your .env file.")
    st.stop()

st.title("YouTube Summarizer App")

video_url = st.text_input("Enter YouTube Video URL:")

def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

def fetch_transcript(url):
    video_id = extract_video_id(url)
    if not video_id:
        st.error("Invalid YouTube URL.")
        return None

    transcript_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}"
    response = requests.get(transcript_url)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching transcript. Status: {response.status_code}")
        return None

def generate_summary(text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": OPENROUTER_API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Summarize the transcript into structured sections."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 500
    }

    response = requests.post(OPENROUTER_API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Error generating summary. Status: {response.status_code}")
        return None

if video_url:
    transcript_data = fetch_transcript(video_url)

    if transcript_data:
        transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
        st.write(transcript_text)

        if st.button("Generate Summary"):
            summary_text = generate_summary(transcript_text)

            if summary_text:
                st.subheader("Summary")
                st.write(summary_text)
