import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env (for local) or Streamlit secrets (for deployment)
load_dotenv()

# Retrieve API credentials securely
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY"))
GITHUB_API_KEY = st.secrets.get("GITHUB_API_KEY", os.getenv("GITHUB_API_KEY"))

OPENROUTER_API_ENDPOINT = st.secrets.get("OPENROUTER_API_ENDPOINT", os.getenv("OPENROUTER_API_ENDPOINT"))
GITHUB_API_ENDPOINT = st.secrets.get("GITHUB_API_ENDPOINT", os.getenv("GITHUB_API_ENDPOINT"))

OPENROUTER_API_MODEL_NAME = st.secrets.get("OPENROUTER_API_MODEL_NAME", os.getenv("OPENROUTER_API_MODEL_NAME"))
GITHUB_API_MODEL_NAME = st.secrets.get("GITHUB_API_MODEL_NAME", os.getenv("GITHUB_API_MODEL_NAME"))

# Determine which API to use
if OPENROUTER_API_KEY:
    API_KEY = OPENROUTER_API_KEY
    API_ENDPOINT = OPENROUTER_API_ENDPOINT
    MODEL_NAME = OPENROUTER_API_MODEL_NAME
elif GITHUB_API_KEY:
    API_KEY = GITHUB_API_KEY
    API_ENDPOINT = GITHUB_API_ENDPOINT
    MODEL_NAME = GITHUB_API_MODEL_NAME
else:
    st.error("No API key found. Please set it in Streamlit secrets or an .env file.")
    st.stop()

# Streamlit UI
st.title("YouTube Video Summarizer")
st.write("Enter a YouTube video URL to generate a structured summary.")

# Language selection
language = st.selectbox("Select Language / 选择语言", ["English", "中文"])

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube Video URL:" if language == "English" else "输入YouTube视频链接:")

# Function to extract video ID from YouTube URL
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# Function to fetch YouTube transcript from proxy API
def fetch_transcript(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid YouTube URL. Please enter a valid video link." if language == "English" else "无效的YouTube链接，请输入有效的视频链接。")
        return None

    # Proxy API for transcript retrieval
    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}"
    
    # Make the API request
    response = requests.get(proxy_api_url)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching transcript. Status code: {response.status_code}" if language == "English" else f"获取字幕时出错。状态码：{response.status_code}")
        return None

# Function to generate structured summary using API
def generate_summary(transcript_text):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL_NAME,
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
        st.error(f"Error generating summary. Status code: {response.status_code}" if language == "English" else f"生成摘要时出错。状态码：{response.status_code}")
        return None

# Function to extract sections from summary
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
        st.error(f"Error processing summary: {e}" if language == "English" else f"处理摘要时出错：{e}")
        return None

# Main logic
if video_url:
    transcript_data = fetch_transcript(video_url)

    if transcript_data:
        st.subheader("Video Transcript" if language == "English" else "视频字幕")
        transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])
        st.write(transcript_text)

        if st.button("Generate Summary" if language == "English" else "生成摘要"):
            summary_text = generate_summary(transcript_text)

            if summary_text:
                st.subheader("Structured Summary" if language == "English" else "结构化摘要")
                sections = extract_sections(summary_text)

                if sections:
                    for section in sections:
                        st.subheader(f"{section['title']} - {section['timestamp']}")
                        st.write(section["summary"])