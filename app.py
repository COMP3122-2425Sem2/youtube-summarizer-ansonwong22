import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API credentials
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME")

# Validate API credentials
if not OPENROUTER_API_KEY or not OPENROUTER_API_ENDPOINT:
    st.error("❌ API Key or API Endpoint is missing! Please check your .env file.")
    st.stop()

# Streamlit App UI
st.title("YouTube Summarizer App")
st.write("Enter a YouTube video URL to generate a structured summary.")

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")

# Language selection
language = st.selectbox("Select summary language:", ["English", "Simplified Chinese", "Traditional Chinese"])
summary_type = st.radio("Choose Summary Type:", ["Short", "Detailed"])

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
        st.error("❌ Invalid YouTube URL. Please enter a valid video URL.")
        return None

    # Proxy API URL for fetching transcripts
    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}"
    
    # Make the API request
    response = requests.get(proxy_api_url)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"❌ Error fetching transcript. Status code: {response.status_code}")
        return None

# Function to generate a structured summary using OpenRouter API
def generate_summary(transcript_text, summary_type, language):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Define the prompt based on summary type
    summary_instruction = "Summarize the transcript into key points." if summary_type == "Short" else "Summarize the transcript in detail with timestamps."
    
    # Language translation
    if language == "Simplified Chinese":
        summary_instruction += " Translate the summary into Simplified Chinese."
    elif language == "Traditional Chinese":
        summary_instruction += " Translate the summary into Traditional Chinese."

    data = {
        "model": OPENROUTER_API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": summary_instruction},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 700
    }

    response = requests.post(OPENROUTER_API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"❌ Error generating summary. API Response: {response.status_code} - {response.text}")
        return None

# Main logic
if video_url:
    transcript_data = fetch_transcript(video_url)

    if transcript_data:
        st.subheader("📜 Video Transcript")
        transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
        st.write(transcript_text)

        if st.button("📝 Generate Summary"):
            summary_text = generate_summary(transcript_text, summary_type, language)

            if summary_text:
                st.subheader("📌 Generated Summary")
                st.write(summary_text)