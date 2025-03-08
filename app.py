import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API credentials from .env or Streamlit Secrets
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY", st.secrets.get("GITHUB_API_KEY", ""))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", st.secrets.get("OPENROUTER_API_KEY", ""))

# Retrieve API endpoint and model name
GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT", st.secrets.get("GITHUB_API_ENDPOINT", ""))
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT", st.secrets.get("OPENROUTER_API_ENDPOINT", ""))
GITHUB_API_MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME", st.secrets.get("GITHUB_API_MODEL_NAME", ""))
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME", st.secrets.get("OPENROUTER_API_MODEL_NAME", ""))

# Determine which API to use
USE_GITHUB = bool(GITHUB_API_KEY and GITHUB_API_ENDPOINT)
API_KEY = GITHUB_API_KEY if USE_GITHUB else OPENROUTER_API_KEY
API_ENDPOINT = GITHUB_API_ENDPOINT if USE_GITHUB else OPENROUTER_API_ENDPOINT
API_MODEL_NAME = GITHUB_API_MODEL_NAME if USE_GITHUB else OPENROUTER_API_MODEL_NAME

# Validate API credentials
if not API_KEY or not API_ENDPOINT:
    st.error("API Key or Endpoint is missing. Please check your environment variables or Streamlit secrets.")
    st.stop()

# Streamlit App UI
st.title("YouTube Video Summarizer")
st.write("Enter a YouTube video URL to generate a structured summary in your chosen language.")

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")

# Language selection
language_map = {"English": "en", "Simplified Chinese": "zh-CN", "Traditional Chinese": "zh-TW"}
selected_language = st.selectbox("Select Summary Language:", list(language_map.keys()))

# Function to extract video ID from YouTube URL
def extract_video_id(video_url):
    if "v=" in video_url:
        return video_url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in video_url:
        return video_url.split("youtu.be/")[-1].split("?")[0]
    else:
        return None

# Function to fetch YouTube transcript
def fetch_transcript(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid YouTube URL. Please enter a valid video URL.")
        return None

    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}"
    
    response = requests.get(proxy_api_url)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        st.error("Transcript not found. The video may not have subtitles.")
        return None
    else:
        st.error(f"Failed to fetch transcript. Error Code: {response.status_code}")
        return None

# Function to generate summary using OpenRouter or GitHub API
def generate_summary(transcript_text, detail_level="standard", lang_code="en"):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"Summarize the transcript in {lang_code}. Provide a structured summary with timestamps."
    if detail_level == "detailed":
        prompt += " Make it as detailed as possible."

    data = {
        "model": API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 800
    }

    response = requests.post(API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            st.error("Unexpected API response format.")
            return None
    else:
        st.error(f"Error generating summary. API Response: {response.status_code} - {response.text}")
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
        st.error(f"Error processing summary: {e}")
        return None

# Main logic
if video_url:
    transcript_data = fetch_transcript(video_url)

    if transcript_data:
        st.subheader("Video Transcript")
        transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
        st.write(transcript_text)

        # Choose summary level
        detail_level = st.radio("Select Detail Level:", ["Standard", "Detailed"]).lower()

        if st.button("Generate Summary"):
            summary_text = generate_summary(transcript_text, detail_level=detail_level, lang_code=language_map[selected_language])

            if summary_text:
                st.subheader("Generated Summary")
                sections = extract_sections(summary_text)

                if sections:
                    for section in sections:
                        st.subheader(f"{section['title']} - {section['timestamp']}")
                        st.write(section["summary"])