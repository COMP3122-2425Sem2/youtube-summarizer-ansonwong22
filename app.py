import streamlit as st
import requests
import os
import json
import re
from dotenv import load_dotenv

# Load environment variables (for local development)
load_dotenv()

# Function to get API credentials (supports both local & Streamlit Cloud)
def get_api_credentials():
    API_KEY = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("GITHUB_API_KEY")
    API_ENDPOINT = st.secrets.get("OPENROUTER_API_ENDPOINT") or os.getenv("OPENROUTER_API_ENDPOINT") or os.getenv("GITHUB_API_ENDPOINT")
    MODEL_NAME = st.secrets.get("OPENROUTER_API_MODEL_NAME") or os.getenv("OPENROUTER_API_MODEL_NAME") or os.getenv("GITHUB_API_MODEL_NAME")

    if not API_KEY or not API_ENDPOINT:
        st.error("❌ API credentials are missing. Set them in `.env` (local) or Streamlit Secrets (cloud).")
        return None, None, None

    return API_KEY, API_ENDPOINT, MODEL_NAME

# Function to extract YouTube Video ID from URL
def extract_video_id(video_url):
    regex = r"(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, video_url)
    return match.group(1) if match else None

# Function to fetch transcript from YouTube transcript API
def fetch_transcript(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("❌ Invalid YouTube URL. Please enter a valid video link.")
        return None

    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}"

    try:
        response = requests.get(proxy_api_url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.error("❌ Transcript not found. This video may not have subtitles.")
        else:
            st.error(f"❌ Failed to fetch transcript. Error Code: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"❌ Error fetching transcript: {str(e)}")
        return None

# Function to generate a summary using OpenRouter or GitHub API
def generate_summary(transcript_text):
    if not transcript_text:
        st.error("❌ Cannot generate summary: transcript is missing.")
        return None

    API_KEY, API_ENDPOINT, MODEL_NAME = get_api_credentials()
    if not API_KEY or not API_ENDPOINT:
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Summarize the transcript into structured sections."},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post(API_ENDPOINT, json=data, headers=headers)
        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No summary generated.")
        else:
            st.error(f"❌ Error generating summary: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Failed to generate summary: {str(e)}")
        return None

# Function to process summary into sections
def extract_sections(summary_text):
    try:
        sections = []
        paragraphs = summary_text.split("\n\n")

        for para in paragraphs:
            if ":" in para:
                parts = para.split(":")
                title = parts[0].strip()
                content = ":".join(parts[1:]).strip()
                sections.append({"title": title, "timestamp": "00:00", "summary": content})
        return sections
    except Exception as e:
        st.error(f"❌ Error processing summary: {str(e)}")
        return None

# Streamlit App UI
st.title("YouTube Summarizer App")
st.write("Enter a YouTube video URL to generate a structured summary.")

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")

# Main logic
if video_url:
    transcript_data = fetch_transcript(video_url)

    if transcript_data:
        st.subheader("Video Transcript")
        transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
        st.write(transcript_text)

        if st.button("Generate Summary"):
            summary_text = generate_summary(transcript_text)

            if summary_text:
                st.subheader("Structured Summary")
                sections = extract_sections(summary_text)

                if sections:
                    for section in sections:
                        st.subheader(f"{section['title']} - {section['timestamp']}")
                        st.write(section["summary"])