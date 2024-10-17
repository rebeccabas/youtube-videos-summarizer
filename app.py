import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import os
from youtube_transcript_api import YouTubeTranscriptApi
import re
import time

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Please set your GOOGLE_API_KEY in the .env file")
    st.stop()

genai.configure(api_key=api_key)

st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .stButton > button {
            width: 100%;
            border-radius: 20px;
            height: 3em;
            font-weight: bold;
        }
        .main-header {
            font-family: 'Helvetica Neue', sans-serif;
            text-align: center;
            padding: 20px;
            background-color: #f0f2f6;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .summary-box {
            padding: 20px;
            border-radius: 10px;
            background-color: #ffffff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .video-info {
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

def extract_video_id(youtube_url):
    """Extract video ID from various forms of YouTube URLs"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:be\/)([0-9A-Za-z_-]{11}).*'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    return None

def extract_transcript_details(youtube_video_url):
    """Extract transcript from YouTube video"""
    try:
        video_id = extract_video_id(youtube_video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
            
        transcript_youtube = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join(item["text"] for item in transcript_youtube)
        return transcript
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def generate_gemini_content(transcript_youtube, summary_type="detailed"):
    try:
        if summary_type == "detailed":
            prompt = """You are a YouTube video summarizer specially for lecture videos. 
            Provide a detailed summary of the following transcript within 250 words. 
            Include main topics covered, key takeaways, and important concepts discussed.
            Format the output with proper headings and bullet points where appropriate.
            
            Transcript: """
        else:  # Quick summary
            prompt = """Provide a brief, concise summary of the main points from this video transcript 
            in no more than 100 words. Focus on the core message and key takeaways.
            
            Transcript: """
        
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt + transcript_youtube)
        return response.text
    
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return None

def display_progress_bar():
    progress_bar = st.progress(0)
    for i in range(100):
        time.sleep(0.01)
        progress_bar.progress(i + 1)
    progress_bar.empty()

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    summary_type = st.radio(
        "Choose Summary Type",
        ["Quick Summary", "Detailed Summary"],
        index=1
    )
    
    st.markdown("### 💡 Tips")
    st.info("""
    - Paste any YouTube video URL
    - Works best with educational content
    - Supports multiple URL formats
    - Choose between quick or detailed summary
    """)


def main():
    st.markdown('<div class="main-header">'
                '<h1>🎥 YouTube Video/Lectures Summarizer</h1>'
                '<p>Transform lengthy videos into concise, actionable summaries</p>'
                '</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        youtube_link = st.text_input(
            "Enter YouTube Video Link:",
            placeholder="https://www.youtube.com/watch?v=..."
        )
    
    if youtube_link:
        video_id = extract_video_id(youtube_link)
        if video_id:
            st.markdown("### 📺 Video Preview")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.image(
                    f"http://img.youtube.com/vi/{video_id}/0.jpg",
                    use_column_width=True
                )
            
            with col2:
                st.markdown('<div class="video-info">', unsafe_allow_html=True)
                analyze_button = st.button("🔍 Analyze Video", type="primary", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            if analyze_button:
                with st.spinner("Processing video..."):
                    display_progress_bar()
                    transcript = extract_transcript_details(youtube_link)
                
                if transcript:
                    with st.spinner("Generating summary..."):
                        summary = generate_gemini_content(
                            transcript, 
                            "quick" if summary_type == "Quick Summary" else "detailed"
                        )
                        if summary:
                            st.markdown('<div class="summary-box">', unsafe_allow_html=True)
                            st.markdown(f"### 📝 {summary_type}")
                            st.write(summary)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
        else:
            st.warning("Please enter a valid YouTube URL")

if __name__ == "__main__":
    main()