import streamlit as st
import requests
import json

# Load API keys from Streamlit secrets
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
OPENROUTER_API_ENDPOINT = st.secrets["OPENROUTER_API_ENDPOINT"]
OPENROUTER_API_MODEL_NAME = st.secrets["OPENROUTER_API_MODEL_NAME"]

GITHUB_API_KEY = st.secrets["GITHUB_API_KEY"]
GITHUB_API_ENDPOINT = st.secrets["GITHUB_API_ENDPOINT"]
GITHUB_API_MODEL_NAME = st.secrets["GITHUB_API_MODEL_NAME"]

# Validate API keys and endpoints
if not OPENROUTER_API_KEY or not OPENROUTER_API_ENDPOINT:
    st.error("❌ API Key or API Endpoint is missing! Please check your Streamlit secrets.")
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

# Function to extract video ID
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

# Function to generate summary
def generate_summary(transcript_text, detail_level, language):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": f"Summarize the transcript in {language} with {detail_level} detail."},
            {"role": "user", "content": transcript_text}
        ],
        "max_tokens": 1000
    }
    response = requests.post(OPENROUTER_API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return None

# Function to translate text
def translate_text(text, target_lang):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": f"Translate the following text to {target_lang}."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 500
    }
    response = requests.post(OPENROUTER_API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return text  # Return original text if translation fails

# Generate Summary Button
if st.button("Generate Summary"):
    video_id = extract_video_id(video_url)
    
    if not video_id:
        st.error("Invalid YouTube URL. Please enter a valid video URL.")
    else:
        transcript_data = fetch_transcript(video_id, language_options[summary_language])

        if not transcript_data:
            st.error("Failed to fetch transcript. Trying default English transcript.")
            transcript_data = fetch_transcript(video_id, "en")  # Fallback to English

        if transcript_data:
            transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
            st.subheader("📜 Transcript")
            st.write(transcript_text)

            summary_text = generate_summary(transcript_text, summary_type.lower(), summary_language)

            if summary_text:
                st.subheader("📌 Summary")
                
                if summary_language != "English":
                    summary_text = translate_text(summary_text, summary_language)

                st.write(summary_text)

                # Generate section-based summary with timestamps
                st.subheader("⏳ Sections")
                for segment in transcript_data['transcript']:
                    start_time = segment['start']
                    formatted_time = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02}"
                    youtube_link = f"{video_url}&t={int(start_time)}"
                    
                    st.markdown(f"**[{formatted_time}]({youtube_link})**: {segment['text']}")

                # Allow editing summary
                edited_summary = st.text_area("Edit Summary:", summary_text)
                if st.button("Save Summary"):
                    st.success("Summary updated successfully!")

                # Download summary
                if st.button("Download Summary as HTML"):
                    html_content = f"<html><body><h1>Video Summary</h1><p>{edited_summary}</p></body></html>"
                    st.download_button(label="Download", data=html_content, file_name="summary.html", mime="text/html")

            else:
                st.error("Error generating summary.")