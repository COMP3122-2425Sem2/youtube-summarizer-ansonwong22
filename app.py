import streamlit as st
import requests
import openai
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# API credentials
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME")

# Streamlit App UI
st.title("🎥 YouTube Summarizer App")
st.write("Enter a YouTube video URL to generate a structured summary.")

# Input field for YouTube video URL
video_url = st.text_input("🔗 Enter YouTube Video URL:")

# Function to fetch YouTube transcript from the proxy API
def fetch_transcript(video_url):
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    response = requests.get(f"{OPENROUTER_API_ENDPOINT}/transcript", params={"url": video_url}, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: Unable to fetch transcript. Status code: {response.status_code}")
        return None

# Function to generate a structured summary using GPT-4o-mini
def generate_summary(transcript_text):
    openai.api_key = OPENROUTER_API_KEY
    
    response = openai.ChatCompletion.create(
        model=OPENROUTER_API_MODEL_NAME,
        messages=[
            {"role": "system", "content": "Summarize the transcript into structured sections with timestamps."},
            {"role": "user", "content": transcript_text}
        ],
        max_tokens=500
    )
    
    return response["choices"][0]["message"]["content"]

# Function to format summary into sections with timestamps
def extract_sections(summary_text):
    try:
        summary_json = json.loads(summary_text)  # Convert JSON string to Python dict
        sections = []
        for section in summary_json["sections"]:
            sections.append({
                "title": section["title"],
                "timestamp": section["timestamp"],
                "summary": section["summary"]
            })
        return sections
    except json.JSONDecodeError:
        st.error("Error: Unable to parse summary into sections.")
        return None

# Main logic
if video_url:
    transcript_data = fetch_transcript(video_url)

    if transcript_data:
        st.subheader("📜 Video Transcript")
        transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
        st.write(transcript_text)

        if st.button("📝 Generate Summary"):
            summary_text = generate_summary(transcript_text)

            if summary_text:
                st.subheader("📌 Structured Summary")
                sections = extract_sections(summary_text)

                if sections:
                    for section in sections:
                        st.subheader(f"📌 {section['title']} - ⏳ {section['timestamp']}")
                        st.write(section["summary"])