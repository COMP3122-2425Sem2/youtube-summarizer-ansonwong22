import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API credentials
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT")
GITHUB_API_MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME")

# Select API Mode
api_mode = st.sidebar.radio("Select API Mode", ("GitHub", "OpenRouter"))

if api_mode == "GitHub":
    API_KEY = GITHUB_API_KEY
    API_ENDPOINT = GITHUB_API_ENDPOINT
    API_MODEL_NAME = GITHUB_API_MODEL_NAME
else:
    API_KEY = OPENROUTER_API_KEY
    API_ENDPOINT = OPENROUTER_API_ENDPOINT
    API_MODEL_NAME = OPENROUTER_API_MODEL_NAME

# Language Selection
st.sidebar.title("Language Settings")
LANGUAGES = {
    "English": "en",
    "Traditional Chinese": "zh-TW",
    "Simplified Chinese": "zh-CN"
}
selected_language = st.sidebar.selectbox("Select Summary Language", list(LANGUAGES.keys()))
lang_code = LANGUAGES[selected_language]

# Function to extract video ID
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# Function to fetch transcript
def fetch_transcript(video_url, lang_code):
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid YouTube URL.")
        return None
    transcript_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?language_code={lang_code}&password=for_demo&video_id={video_id}"
    response = requests.get(transcript_url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch transcript. Error Code: {response.status_code}")
        return None

# Function to generate summary
def generate_summary(transcript_text, detail_level="default"):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompts = {
        "default": "Summarize the transcript in structured sections with timestamps.",
        "detailed": "Provide a more detailed summary for each section while keeping existing sections unchanged.",
        "concise": "Make each section's summary more concise while keeping existing sections unchanged.",
        "fun": "Make the summary of each section more fun by adding emojis while keeping existing sections unchanged."
    }

    data = {
        "model": API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": prompts[detail_level]},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 800
    }
    
    response = requests.post(API_ENDPOINT, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Failed to generate summary. Error Code: {response.status_code}")
        return None

# Extract structured sections from summary
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

# UI Setup
st.title("YouTube Summarizer App")
video_url = st.text_input("Enter YouTube Video URL:")

# Generate Summary Button
if video_url:
    transcript_data = fetch_transcript(video_url, lang_code)
    
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
                        timestamp_link = f"[{section['timestamp']}](https://www.youtube.com/watch?v={extract_video_id(video_url)}&t={section['timestamp']})"
                        st.subheader(f"{section['title']} - {timestamp_link}")
                        edited_summary = st.text_area(f"Edit summary for {section['title']}", section["summary"])
                        if st.button(f"Save {section['title']}"):
                            section["summary"] = edited_summary
                            st.success("Summary updated!")

# Additional Options
st.sidebar.title("Advanced Options")
if st.sidebar.button("Generate Detailed Summary"):
    summary_text = generate_summary(transcript_text, detail_level="detailed")
if st.sidebar.button("Generate Concise Summary"):
    summary_text = generate_summary(transcript_text, detail_level="concise")
if st.sidebar.button("Make Summary Fun"):
    summary_text = generate_summary(transcript_text, detail_level="fun")

# Download Summary as HTML
if st.sidebar.button("Download Summary as HTML"):
    html_content = f"<html><body><h2>YouTube Summary</h2><p>{summary_text}</p></body></html>"
    st.sidebar.download_button("Download HTML", html_content, "summary.html", "text/html")