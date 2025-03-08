import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve GitHub API credentials
API_KEY = os.getenv("GITHUB_API_KEY")
API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT")  # Ensure this is correctly set
MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME")  # Ensure this is correctly set

# Validate API keys and endpoints
if not API_KEY or not API_ENDPOINT or not MODEL_NAME:
    st.error("❌ Missing API Key, Endpoint, or Model Name. Please check your .env file.")
    st.stop()

# Streamlit UI
st.title("🎥 YouTube Video Summarizer (Powered by GPT-4o-mini)")

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

# Function to call GitHub API (GPT-4o-mini) for transcript extraction
def fetch_transcript(video_url):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Extract the transcript from the following YouTube video and return it as plain text."},
            {"role": "user", "content": f"Video URL: {video_url}"}
        ],
        "max_tokens": 4000
    }
    response = requests.post(API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return None

# Function to generate summary using GitHub API (GPT-4o-mini)
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

# Function to translate text using GitHub API (GPT-4o-mini)
def translate_text(text, target_lang):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": f"Translate the following text to {target_lang}."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 1000
    }
    response = requests.post(API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return text  # If translation fails, return the original text

# Generate Summary Button
if st.button("Generate Summary"):
    video_id = extract_video_id(video_url)
    
    if not video_id:
        st.error("❌ Invalid YouTube URL. Please enter a valid video URL.")
    else:
        # Fetch transcript using GPT-4o-mini
        st.info("⏳ Fetching transcript using GPT-4o-mini...")
        transcript_text = fetch_transcript(video_url)

        if not transcript_text:
            st.error("❌ Failed to extract transcript using GPT. Try a different video.")
        else:
            st.subheader("📜 Transcript")
            st.write(transcript_text)

            # Generate the summary using GPT-4o-mini
            st.info("⏳ Generating summary using GPT-4o-mini...")
            summary_text = generate_summary(transcript_text, summary_type.lower(), "English")

            if summary_text:
                st.subheader("📌 Summary (Original)")
                st.write(summary_text)

                # Translate summary if selected language is not English
                if summary_language in ["Traditional Chinese", "Simplified Chinese"]:
                    st.info(f"⏳ Translating summary to {summary_language} using GPT-4o-mini...")
                    translated_summary = translate_text(summary_text, language_options[summary_language])
                    st.subheader(f"📌 Summary ({summary_language})")
                    st.write(translated_summary)
                else:
                    translated_summary = summary_text  # Keep original if English is selected

                # Editable summary
                edited_summary = st.text_area("✏️ Edit Summary:", translated_summary)
                if st.button("Save Summary"):
                    st.success("✅ Summary updated successfully!")

                # Download summary as HTML
                if st.button("⬇️ Download Summary as HTML"):
                    html_content = f"<html><body><h1>Video Summary</h1><p>{edited_summary}</p></body></html>"
                    st.download_button(label="Download", data=html_content, file_name="summary.html", mime="text/html")

            else:
                st.error("❌ Error generating summary.")