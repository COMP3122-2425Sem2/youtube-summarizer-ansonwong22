import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch API Keys from Local Environment or Streamlit Secrets
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", st.secrets.get("OPENROUTER_API_KEY"))
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY", st.secrets.get("GITHUB_API_KEY"))

# Fetch API Endpoints
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT", st.secrets.get("OPENROUTER_API_ENDPOINT"))
GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT", st.secrets.get("GITHUB_API_ENDPOINT"))

# Fetch Model Names
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME", st.secrets.get("OPENROUTER_API_MODEL_NAME"))
GITHUB_API_MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME", st.secrets.get("GITHUB_API_MODEL_NAME"))

# Validate API Keys
if not OPENROUTER_API_KEY and not GITHUB_API_KEY:
    st.error("❌ API keys are missing! Please set them in `.env` (local) or `Secrets` (Streamlit Cloud).")
    st.stop()

# UI - Streamlit Title
st.title("YouTube Video Summarizer")

# Input: YouTube URL
video_url = st.text_input("Enter a YouTube Video URL:")

# Language Selection
language = st.selectbox("Choose Language:", ["English", "Spanish", "French", "German", "Chinese"])

# Summarization Level
detail_level = st.radio("Summary Detail Level:", ["Short", "Detailed"])

# Extract Video ID
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# Fetch Transcript
def fetch_transcript(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid YouTube URL. Please enter a valid video link.")
        return None

    # Proxy API URL for fetching transcripts
    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}"
    response = requests.get(proxy_api_url)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch transcript. Error Code: {response.status_code}")
        return None

# Generate Summary
def generate_summary(transcript_text, detail_level):
    api_key = OPENROUTER_API_KEY if OPENROUTER_API_KEY else GITHUB_API_KEY
    api_endpoint = OPENROUTER_API_ENDPOINT if OPENROUTER_API_KEY else GITHUB_API_ENDPOINT
    model_name = OPENROUTER_API_MODEL_NAME if OPENROUTER_API_KEY else GITHUB_API_MODEL_NAME

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = "Summarize this transcript into structured sections with timestamps."
    if detail_level == "Short":
        prompt += " Keep it concise."
    else:
        prompt += " Provide more details."

    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 500
    }

    response = requests.post(api_endpoint, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Error generating summary. Status Code: {response.status_code}")
        return None

# Process Summary Sections
def extract_sections(summary_text):
    sections = []
    paragraphs = summary_text.split("\n\n")

    for para in paragraphs:
        if ":" in para:
            parts = para.split(":")
            title = parts[0].strip()
            content = ":".join(parts[1:]).strip()
            sections.append({"title": title, "timestamp": "00:00", "summary": content})

    return sections

# Main Logic
if video_url:
    transcript_data = fetch_transcript(video_url)

    if transcript_data:
        st.subheader("Video Transcript")
        transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
        st.write(transcript_text)

        if st.button("Generate Summary"):
            summary_text = generate_summary(transcript_text, detail_level)

            if summary_text:
                st.subheader("Structured Summary")
                sections = extract_sections(summary_text)

                for section in sections:
                    st.subheader(f"{section['title']} - {section['timestamp']}")
                    st.write(section["summary"])