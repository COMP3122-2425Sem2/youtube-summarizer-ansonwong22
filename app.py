import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Credentials
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
GITHUB_API_MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME", "gpt-4o-mini")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME", "gpt-4o-mini")

# Select API Key
API_KEY = GITHUB_API_KEY if GITHUB_API_KEY else OPENROUTER_API_KEY
API_ENDPOINT = GITHUB_API_ENDPOINT if GITHUB_API_KEY else OPENROUTER_API_ENDPOINT
API_MODEL_NAME = GITHUB_API_MODEL_NAME if GITHUB_API_KEY else OPENROUTER_API_MODEL_NAME

if not API_KEY or not API_ENDPOINT:
    st.error("Missing API Key or Endpoint. Please set up your API credentials.")
    st.stop()

# Streamlit UI
st.title("YouTube Video Summarizer")

# Video URL Input
video_url = st.text_input("Enter YouTube Video URL:")

# Language Selection
language_options = {
    "English": "en",
    "Traditional Chinese": "zh-TW",
    "Simplified Chinese": "zh-CN"
}
language = st.selectbox("Select Summary Language:", list(language_options.keys()))

# Extract Video ID
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# Fetch Transcript from Proxy API
def fetch_transcript(video_id, lang_code):
    url = f"https://yt.vl.comp.polyu.edu.hk/transcript?language_code={lang_code}&password=for_demo&video_id={video_id}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch transcript. Error Code: {response.status_code}")
        return None

# Generate Summary via API
def generate_summary(transcript_text, detail_level="standard", lang_code="en"):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompt = f"Summarize the transcript into structured sections with timestamps in {language_options[language]}."
    
    if detail_level == "detailed":
        prompt += " Include detailed explanations for each section."
    elif detail_level == "concise":
        prompt += " Make it short and precise."
    elif detail_level == "fun":
        prompt += " Add emojis and a fun tone."

    data = {
        "model": API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 500
    }
    response = requests.post(API_ENDPOINT, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Error: Unable to generate summary. Status code: {response.status_code}")
        return None

# Process Summary into Sections
def extract_sections(summary_text, video_id):
    sections = []
    paragraphs = summary_text.split("\n\n")

    for para in paragraphs:
        if ":" in para:
            parts = para.split(":")
            title = parts[0].strip()
            content = ":".join(parts[1:]).strip()
            timestamp = "00:00"
            link = f"https://www.youtube.com/watch?v={video_id}&t={timestamp}"

            sections.append({
                "title": title,
                "timestamp": timestamp,
                "summary": content,
                "link": link
            })
    return sections

# Main Execution
if video_url:
    video_id = extract_video_id(video_url)

    if video_id:
        transcript_data = fetch_transcript(video_id, language_options[language])

        if transcript_data:
            st.subheader("Video Transcript")
            transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
            st.text_area("Full Transcript", transcript_text, height=200)

            # Summary Buttons
            col1, col2, col3, col4 = st.columns(4)
            if col1.button("Generate Summary"):
                summary_text = generate_summary(transcript_text, "standard", language_options[language])
            if col2.button("Detailed Summary"):
                summary_text = generate_summary(transcript_text, "detailed", language_options[language])
            if col3.button("Concise Summary"):
                summary_text = generate_summary(transcript_text, "concise", language_options[language])
            if col4.button("Fun Summary 🎉"):
                summary_text = generate_summary(transcript_text, "fun", language_options[language])

            if summary_text:
                st.subheader("Summary")
                sections = extract_sections(summary_text, video_id)

                for section in sections:
                    st.subheader(f"{section['title']} - ⏳ {section['timestamp']}")
                    st.write(section["summary"])
                    st.markdown(f"[Watch this part on YouTube]({section['link']})")

                # Editable Summaries
                st.subheader("Edit Summaries")
                for section in sections:
                    new_summary = st.text_area(f"Edit: {section['title']}", section["summary"])
                    if st.button(f"Save {section['title']}"):
                        section["summary"] = new_summary
                        st.success(f"Updated summary for {section['title']}.")

                # Download as HTML
                st.download_button("Download Summary as HTML", data=summary_text, file_name="summary.html", mime="text/html")
    else:
        st.error("Invalid YouTube URL. Please enter a valid video URL.")