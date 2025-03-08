import os
import streamlit as st
import json
import toml
from llm import answer  # Import the function from llm.py

# Load API key from credentials.toml
file_path = 'credentials.toml'
if os.path.exists(file_path):
    with open(file_path, 'r') as f:
        secrets = toml.load(f)
else:
    st.error("❌ Credentials file not found. Please create 'credentials.toml'.")
    st.stop()

# Validate API key for GitHub API
if 'GITHUB' not in secrets or 'GITHUB_API_KEY' not in secrets['GITHUB']:
    st.error("❌ GitHub API key not found in credentials.toml.")
    st.stop()
    
# Streamlit UI
st.title("🎥 YouTube Video Summarizer (GPT-4o-mini via GitHub API)")

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

# Function to fetch transcript using GPT-4o-mini (via llm.py)
def fetch_transcript(video_url):
    system_prompt = "Extract the transcript from the following YouTube video and return it as plain text."
    return answer(system_prompt, f"Video URL: {video_url}", model_type="github")

# Function to generate summary using GPT-4o-mini
def generate_summary(transcript_text, detail_level, language):
    system_prompt = f"Summarize the transcript in {language} with {detail_level} detail."
    return answer(system_prompt, transcript_text, model_type="github")

# Function to translate text using GPT-4o-mini
def translate_text(text, target_lang):
    system_prompt = f"Translate the following text to {target_lang}."
    return answer(system_prompt, text, model_type="github")

# Function to format timestamps (for future enhancement if timestamps are extracted)
def format_timestamp(seconds):
    return f"{int(seconds // 3600):02}:{int((seconds % 3600) // 60):02}:{int(seconds % 60):02}"

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