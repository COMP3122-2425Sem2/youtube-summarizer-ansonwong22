import streamlit as st
import requests
import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT")
OPENROUTER_API_ENDPOINT = os.getenv("OPENROUTER_API_ENDPOINT")
GITHUB_API_MODEL_NAME = os.getenv("GITHUB_API_MODEL_NAME", "gpt-4o-mini")
OPENROUTER_API_MODEL_NAME = os.getenv("OPENROUTER_API_MODEL_NAME", "gpt-4o")

# Language Options
LANGUAGES = {
    "English": "en",
    "Traditional Chinese": "zh-TW",
    "Simplified Chinese": "zh"
}

# UI Texts for Different Languages
UI_TEXTS = {
    "en": {
        "title": "YouTube Summarizer App",
        "description": "Enter a YouTube video URL to generate a structured summary.",
        "input_label": "Enter YouTube Video URL:",
        "language_label": "Select Language:",
        "fetch_transcript": "Fetching transcript...",
        "generate_summary": "Generate Summary",
        "summary": "Summary",
        "fallback": "Transcript not available in {lang}. Falling back to English.",
        "no_transcript": "No transcript available in any language.",
        "error": "Error fetching transcript. Error Code: {code}",
        "translation": "Translating...",
        "translated": "Translated Summary"
    },
    "zh-TW": {
        "title": "YouTube 摘要應用",
        "description": "輸入 YouTube 影片 URL 以生成結構化摘要。",
        "input_label": "輸入 YouTube 影片網址：",
        "language_label": "選擇語言：",
        "fetch_transcript": "正在獲取字幕...",
        "generate_summary": "生成摘要",
        "summary": "摘要",
        "fallback": "未找到 {lang} 的字幕，將改用英文。",
        "no_transcript": "沒有可用的字幕。",
        "error": "獲取字幕錯誤，錯誤代碼：{code}",
        "translation": "正在翻譯...",
        "translated": "翻譯後的摘要"
    },
    "zh": {
        "title": "YouTube 摘要应用",
        "description": "输入 YouTube 视频 URL 以生成结构化摘要。",
        "input_label": "输入 YouTube 视频网址：",
        "language_label": "选择语言：",
        "fetch_transcript": "正在获取字幕...",
        "generate_summary": "生成摘要",
        "summary": "摘要",
        "fallback": "未找到 {lang} 的字幕，将改用英文。",
        "no_transcript": "没有可用的字幕。",
        "error": "获取字幕错误，错误代码：{code}",
        "translation": "正在翻译...",
        "translated": "翻译后的摘要"
    }
}

# Streamlit UI
st.set_page_config(page_title="YouTube Summarizer", layout="wide")

# Select Language
selected_lang = st.selectbox("🌍 " + UI_TEXTS["en"]["language_label"], list(LANGUAGES.keys()))
lang_code = LANGUAGES[selected_lang]
ui_text = UI_TEXTS[lang_code]

st.title(ui_text["title"])
st.write(ui_text["description"])

# YouTube URL Input
video_url = st.text_input(ui_text["input_label"])

# Extract YouTube Video ID
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# Fetch Transcript
def fetch_transcript(video_id, lang_code):
    st.info(ui_text["fetch_transcript"])
    proxy_api_url = f"https://yt.vl.comp.polyu.edu.hk/transcript?password=for_demo&video_id={video_id}&lang={lang_code}"
    
    response = requests.get(proxy_api_url)
    if response.status_code == 200:
        return response.json()
    elif lang_code != "en":
        st.warning(ui_text["fallback"].format(lang=selected_lang))
        return fetch_transcript(video_id, "en")
    else:
        st.error(ui_text["error"].format(code=response.status_code))
        return None

# AI Translation
def translate_text(text, target_lang):
    st.info(ui_text["translation"])
    response = openai.ChatCompletion.create(
        model=OPENROUTER_API_MODEL_NAME,
        messages=[
            {"role": "system", "content": f"Translate the following text into {target_lang}."},
            {"role": "user", "content": text}
        ]
    )
    return response["choices"][0]["message"]["content"]

# Generate Summary
def generate_summary(text, model="gpt-4o-mini"):
    headers = {"Authorization": f"Bearer {GITHUB_API_KEY or OPENROUTER_API_KEY}"}
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Summarize the following transcript into structured sections with timestamps."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 500
    }
    response = requests.post(GITHUB_API_ENDPOINT or OPENROUTER_API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(ui_text["error"].format(code=response.status_code))
        return None

# Process Transcript & Generate Summary
if video_url:
    video_id = extract_video_id(video_url)
    if video_id:
        transcript_data = fetch_transcript(video_id, lang_code)

        if transcript_data:
            transcript_text = " ".join([segment['text'] for segment in transcript_data['transcript']])

            if st.button(ui_text["generate_summary"]):
                summary_text = generate_summary(transcript_text)

                if lang_code != "en":
                    summary_text = translate_text(summary_text, lang_code)
                    st.subheader(ui_text["translated"])
                else:
                    st.subheader(ui_text["summary"])

                st.write(summary_text)
    else:
        st.error(ui_text["error"].format(code="Invalid YouTube URL"))