import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables (for local running)
load_dotenv()

# Read API keys & endpoints (GitHub API or OpenRouter API)
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT")
GITHUB_API_MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME")

# Use Streamlit secrets if deployed on Streamlit Cloud
if not GITHUB_API_KEY or not OPENROUTER_API_KEY:
    GITHUB_API_KEY = st.secrets.get("GITHUB_API_KEY")
    GITHUB_API_ENDPOINT = st.secrets.get("GITHUB_API_ENDPOINT")
    GITHUB_API_MODEL_NAME = st.secrets.get("GITHUB_API_MODEL_NAME")

    OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")
    OPENROUTER_API_ENDPOINT = st.secrets.get("OPENROUTER_API_ENDPOINT")
    OPENROUTER_API_MODEL_NAME = st.secrets.get("OPENROUTER_API_MODEL_NAME")

st.title("YouTube Video Summarizer")

# Language selection for transcript
language_options = {
    "English": "en",
    "Traditional Chinese": "zh-TW",
    "Simplified Chinese": "zh-CN",
}
selected_language = st.selectbox("Select Transcript Language:", list(language_options.keys()))

# Input YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")

# Extract video ID from YouTube URL
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# Fetch YouTube transcript
def fetch_transcript(video_id, language_code):
    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}&language_code={language_code}"
    response = requests.get(proxy_api_url)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch transcript. Error Code: {response.status_code}")
        return None

# Generate Summary using API
def generate_summary(transcript_text, detail_level="short"):
    api_key = OPENROUTER_API_KEY if OPENROUTER_API_KEY else GITHUB_API_KEY
    api_endpoint = OPENROUTER_API_ENDPOINT if OPENROUTER_API_KEY else GITHUB_API_ENDPOINT
    model_name = OPENROUTER_API_MODEL_NAME if OPENROUTER_API_KEY else GITHUB_API_MODEL_NAME

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": f"Summarize this YouTube transcript in a {detail_level} format."},
            {"role": "user", "content": transcript_text},
        ],
        "max_tokens": 500
    }
    response = requests.post(api_endpoint, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Failed to generate summary. Error Code: {response.status_code}")
        return None

# Generate Detailed Summary with timestamps
def generate_detailed_summary(transcript_data):
    summary = []
    for segment in transcript_data["transcript"]:
        start_time = int(segment["start"])
        minutes, seconds = divmod(start_time, 60)
        timestamp = f"{minutes:02}:{seconds:02}"
        summary.append(f"[{timestamp}](https://www.youtube.com/watch?v={video_id}&t={start_time}) - {segment['text']}")
    return "\n".join(summary)

# Process and Display Results
if video_url:
    video_id = extract_video_id(video_url)
    
    if video_id:
        transcript_data = fetch_transcript(video_id, language_options[selected_language])
        
        if transcript_data:
            st.subheader("📜 Video Transcript")
            transcript_text = " ".join([segment['text'] for segment in transcript_data["transcript"]])
            st.write(transcript_text)

            if st.button("Generate Short Summary"):
                short_summary = generate_summary(transcript_text, detail_level="short")
                if short_summary:
                    st.subheader("Short Summary")
                    st.write(short_summary)

            if st.button("Generate Detailed Summary"):
                detailed_summary = generate_detailed_summary(transcript_data)
                st.subheader("Detailed Summary with Timestamps")
                st.markdown(detailed_summary, unsafe_allow_html=True)

            # Show transcript per section
            with st.expander("Show Transcript with Timestamps"):
                st.write(generate_detailed_summary(transcript_data))

            # Editable Summary Sections
            st.subheader("Edit Section Summaries")
            for section in transcript_data["transcript"]:
                section_text = st.text_area(f"Edit Summary for [{section['start']:.2f} sec]", section['text'])
                if st.button(f"Save Section [{section['start']:.2f} sec]"):
                    st.success("Section summary updated!")

            # Download Summary as HTML
            if st.button("Download Summary as HTML"):
                with open("summary.html", "w", encoding="utf-8") as f:
                    f.write(f"<h1>Summary for {video_url}</h1>")
                    f.write(f"<p>{transcript_text}</p>")
                st.download_button("Download Summary", "summary.html", "text/html")

else:
    st.warning("Please enter a YouTube URL to proceed.")