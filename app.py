import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.getcwd(), ".env")  # Ensure .env file is loaded
load_dotenv(dotenv_path=dotenv_path)

# Retrieve API credentials from .env file
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME")

# Check if API credentials are loaded
if not OPENROUTER_API_KEY or not OPENROUTER_API_ENDPOINT:
    st.error("Error: Missing API Key or Endpoint. Please check your .env file.")
    st.stop()

# Streamlit App UI
st.title("YouTube Summarizer App")
st.write("Enter a YouTube video URL to generate a structured summary.")

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")

# Function to extract video ID from YouTube URL
def extract_video_id(video_url):
    if "v=" in video_url:
        return video_url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in video_url:
        return video_url.split("youtu.be/")[-1].split("?")[0]
    else:
        return None

# Function to fetch YouTube transcript from proxy API
def fetch_transcript(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid YouTube URL. Please enter a valid video URL.")
        return None

    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}"
    response = requests.get(proxy_api_url)

    if response.status_code == 200:
        transcript_data = response.json()
        if "transcript" in transcript_data:
            return transcript_data
        else:
            st.error("Error: Transcript data is missing in the response.")
            return None
    else:
        st.error(f"Error: Unable to fetch transcript. Status code: {response.status_code}")
        return None

# Function to generate a structured summary using OpenRouter API
def generate_summary(transcript_text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": OPENROUTER_API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Summarize the transcript into structured sections with timestamps."},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 500
    }

    response = requests.post(OPENROUTER_API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        if "choices" in response_json and len(response_json["choices"]) > 0:
            return response_json["choices"][0]["message"]["content"]
        else:
            st.error("Error: API response format is incorrect.")
            return None
    else:
        st.error(f"Error: Unable to generate summary. Status code: {response.status_code}")
        return None

# Function to process the summary into sections with timestamps
def extract_sections(summary_text):
    try:
        sections = []
        paragraphs = summary_text.split("\n\n")  

        for para in paragraphs:
            if ":" in para:
                parts = para.split(":")
                title = parts[0].strip()
                content = ":".join(parts[1:]).strip()
                sections.append({
                    "title": title,
                    "timestamp": "00:00",
                    "summary": content
                })
        return sections
    except Exception as e:
        st.error(f"Error: Unable to process summary: {e}")
        return None

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
