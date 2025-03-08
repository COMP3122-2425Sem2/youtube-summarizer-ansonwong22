import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API credentials (Supports GitHub API & OpenRouter API)
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT")
GITHUB_API_MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME")

# Determine which API to use
if GITHUB_API_KEY:
    API_KEY = GITHUB_API_KEY
    API_ENDPOINT = GITHUB_API_ENDPOINT
    API_MODEL_NAME = GITHUB_API_MODEL_NAME
elif OPENROUTER_API_KEY:
    API_KEY = OPENROUTER_API_KEY
    API_ENDPOINT = OPENROUTER_API_ENDPOINT
    API_MODEL_NAME = OPENROUTER_API_MODEL_NAME
else:
    st.error("❌ Error: No API Key found. Please set GITHUB_API_KEY or OPENROUTER_API_KEY.")
    st.stop()

# Streamlit App UI
st.title("YouTube Summarizer App")
st.write("Enter a YouTube video URL to generate a structured summary.")

# Language selection
language_options = {"English": "en", "Traditional Chinese": "zh-TW", "Simplified Chinese": "zh-CN"}
selected_language = st.selectbox("Select Summary Language:", list(language_options.keys()))

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")

# Extract video ID from URL
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# Fetch transcript from proxy API
def fetch_transcript(video_url, lang_code):
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid YouTube URL. Please enter a valid video URL.")
        return None

    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&language_code={lang_code}&video_id={video_id}"
    response = requests.get(proxy_api_url)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching transcript. Status code: {response.status_code}")
        return None

# Generate summary using OpenRouter or GitHub API
def generate_summary(transcript_text):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Summarize the transcript into structured sections with timestamps."},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 500
    }

    response = requests.post(API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Error generating summary. Status code: {response.status_code}")
        return None

# Extract structured sections from summary
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

# Process and display results
if video_url:
    transcript_data = fetch_transcript(video_url, language_options[selected_language])

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

                # Download Summary as HTML
                st.download_button("Download Summary as HTML", summary_text, file_name="summary.html", mime="text/html")