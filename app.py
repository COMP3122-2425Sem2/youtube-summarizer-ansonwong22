import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API credentials (supports both GitHub Model and OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME", "gpt-4o-mini")
GITHUB_API_MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME", "gpt-4o-mini")

# Determine which API to use
API_KEY = OPENROUTER_API_KEY if OPENROUTER_API_KEY else GITHUB_API_KEY
API_ENDPOINT = OPENROUTER_API_ENDPOINT if OPENROUTER_API_ENDPOINT else GITHUB_API_ENDPOINT
API_MODEL_NAME = OPENROUTER_API_MODEL_NAME if OPENROUTER_API_KEY else GITHUB_API_MODEL_NAME

# Check API key
if not API_KEY or not API_ENDPOINT:
    st.error("Error: Missing API Key or Endpoint. Check environment variables or Streamlit secrets.")
    st.stop()

# UI - Streamlit App
st.title("YouTube Summarizer App")
st.write("Enter a YouTube video URL to generate a structured summary.")

# Language Selection
LANGUAGES = {"English": "en", "Traditional Chinese": "zh-TW", "Simplified Chinese": "zh-CN"}
language = st.selectbox("Select summary language:", list(LANGUAGES.keys()))

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")

# Function to extract video ID from URL
def extract_video_id(video_url):
    if "v=" in video_url:
        return video_url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in video_url:
        return video_url.split("youtu.be/")[-1].split("?")[0]
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
    else:
        st.error(f"Error: Unable to fetch transcript. Status code: {response.status_code}")
        return None

# Function to generate summary using API
def generate_summary(transcript_text, lang):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": f"Summarize the transcript in {lang}. Provide timestamps and structured sections."},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 1000
    }

    response = requests.post(API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Error: Unable to generate summary. Status code: {response.status_code}")
        return None

# Function to format summary with timestamps
def extract_sections(summary_text, video_id):
    sections = []
    paragraphs = summary_text.split("\n\n")

    for i, para in enumerate(paragraphs):
        if ":" in para:
            parts = para.split(":")
            title = parts[0].strip()
            content = ":".join(parts[1:]).strip()
            timestamp = f"{i*30:02}:00"  # Approximate timestamps every 30s
            yt_link = f"https://www.youtube.com/watch?v={video_id}&t={i*30}s"
            sections.append({"title": title, "timestamp": timestamp, "summary": content, "link": yt_link})
    return sections

# Function to download summary as HTML
def download_summary(sections):
    html_content = "<html><body><h2>YouTube Video Summary</h2>"
    for section in sections:
        html_content += f"<h3>{section['title']} - <a href='{section['link']}' target='_blank'>{section['timestamp']}</a></h3>"
        html_content += f"<p>{section['summary']}</p>"
    html_content += "</body></html>"
    return html_content

# Main logic
if video_url:
    transcript_data = fetch_transcript(video_url)

    if transcript_data:
        st.subheader("Video Transcript")
        transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
        st.write(transcript_text)

        if st.button("Generate Summary"):
            summary_text = generate_summary(transcript_text, LANGUAGES[language])

            if summary_text:
                st.subheader("Structured Summary")
                video_id = extract_video_id(video_url)
                sections = extract_sections(summary_text, video_id)

                for section in sections:
                    with st.expander(f"{section['title']} - {section['timestamp']}"):
                        st.write(section["summary"])
                        st.markdown(f"[Jump to {section['timestamp']} ▶️]({section['link']})", unsafe_allow_html=True)

                # Editable Summary Sections
                st.subheader("Edit Summary")
                updated_sections = []
                for section in sections:
                    new_summary = st.text_area(f"Edit {section['title']}", section["summary"])
                    updated_sections.append({**section, "summary": new_summary})

                # Download Button
                if st.button("Download Summary as HTML"):
                    html_content = download_summary(updated_sections)
                    st.download_button("Download HTML", data=html_content, file_name="summary.html", mime="text/html")