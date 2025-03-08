import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv
from urllib.parse import urlencode

# Load environment variables
load_dotenv()

# Retrieve API credentials from both GitHub Model and OpenRouter
API_KEY = os.getenv("GITHUB_API_KEY") or os.getenv("OPENROUTER_API_KEY")
API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT") or os.getenv("OPENROUTER_API_ENDPOINT")
MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME") or os.getenv("OPENROUTER_API_MODEL_NAME")

# Validate API keys and endpoints
if not API_KEY or not API_ENDPOINT:
    st.error("❌ API Key or API Endpoint is missing! Please check your .env file.")
    st.stop()

# Streamlit UI
st.title("🎥 YouTube Video Summarizer")

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:")

# Language selection
language_options = {
    "English": "en",
    "Traditional Chinese": "zh-TW",
    "Simplified Chinese": "zh-CN"
}
summary_language = st.selectbox("Select summary language:", list(language_options.keys()))

# Summary detail level
summary_type = st.radio("Choose summary detail level:", ["Basic", "Detailed", "Fun"])

# Function to extract video ID from URL
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# Function to fetch transcript using proxy API
def fetch_transcript(video_id, lang_code="en"):
    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}&language_code={lang_code}"
    response = requests.get(proxy_api_url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to generate summary using AI
def generate_summary(transcript_text, detail_level, language):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": f"Summarize the transcript in {language} with {detail_level} detail."},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 1000
    }
    response = requests.post(API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return None

# Function to format timestamp
def format_timestamp(seconds):
    return f"{int(seconds // 3600):02}:{int((seconds % 3600) // 60):02}:{int(seconds % 60):02}"

# Generate Summary Button
if st.button("Generate Summary"):
    video_id = extract_video_id(video_url)
    
    if not video_id:
        st.error("Invalid YouTube URL. Please enter a valid video URL.")
    else:
        transcript_data = fetch_transcript(video_id, language_options[summary_language])

        if not transcript_data:
            st.warning("⚠️ Failed to fetch transcript in selected language. Trying English transcript instead.")
            transcript_data = fetch_transcript(video_id, "en")  # Fallback to English

        if transcript_data:
            transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
            st.subheader("📜 Transcript")
            st.write(transcript_text)

            # Generate the summary
            summary_text = generate_summary(transcript_text, summary_type.lower(), summary_language)

            if summary_text:
                st.subheader("📌 Summary")
                st.write(summary_text)

                # Generate section-based summary with timestamps
                st.subheader("⏳ Sections")
                section_summaries = []
                
                for segment in transcript_data['transcript']:
                    start_time = segment['start']
                    formatted_time = format_timestamp(start_time)
                    youtube_link = f"{video_url}&t={int(start_time)}"
                    
                    section_summary = f"**[{formatted_time}]({youtube_link})**: {segment['text']}"
                    section_summaries.append(section_summary)
                
                st.markdown("\n\n".join(section_summaries))

                # Editable summary
                edited_summary = st.text_area("✏️ Edit Summary:", summary_text)
                if st.button("Save Summary"):
                    st.success("✅ Summary updated successfully!")

                # Download summary as HTML
                if st.button("⬇️ Download Summary as HTML"):
                    html_content = f"<html><body><h1>Video Summary</h1><p>{edited_summary}</p></body></html>"
                    st.download_button(label="Download", data=html_content, file_name="summary.html", mime="text/html")

            else:
                st.error("❌ Error generating summary.")