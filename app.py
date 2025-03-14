import os
import streamlit as st
import pandas as pd
import PyPDF2
import google.generativeai as genai
from io import StringIO
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# Page configuration with custom theme
st.set_page_config(
    page_title="Enterprise Content Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    .stTextArea>div>div>textarea {
        border-radius: 5px;
    }
    .upload-prompt {
        border: 2px dashed #cccccc;
        border-radius: 5px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
    }
    .success-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        color: #155724;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        color: #721c24;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def initialize_agent():
    return Agent(
        name="Enterprise Content Analyzer",
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

def fetch_webpage_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = ' '.join(chunk.strip() for line in soup.get_text().splitlines() for chunk in line.split("  ") if chunk)
        return text, None
    except Exception as e:
        return None, f"Error fetching content: {str(e)}"

def extract_text_from_pdf(uploaded_file):
    try:
        text = ""
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text, None
    except Exception as e:
        return None, f"Error processing PDF: {str(e)}"

def extract_text_from_txt(uploaded_file):
    try:
        return str(uploaded_file.read(), "utf-8"), None
    except Exception as e:
        return None, f"Error processing text file: {str(e)}"

def extract_text_from_csv(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        return df.to_string(), None
    except Exception as e:
        return None, f"Error processing CSV file: {str(e)}"

def extract_text_from_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        return df.to_string(), None
    except Exception as e:
        return None, f"Error processing Excel file: {str(e)}"

# Initialize the agent
multimodal_Agent = initialize_agent()

# Sidebar for configuration and information
with st.sidebar:
    st.image("https://i.pinimg.com/736x/41/59/d5/4159d5618a90e96c7807be2438cf9515.jpg", use_container_width=True)
    st.title("Settings & Info")
    st.markdown("---")
    st.markdown("""
    ### About
    Enterprise Content Analyzer helps you extract insights from various data sources using advanced AI.
    
    ### Supported Formats
    - Website URLs
    - PDF Documents
    - Text Files
    - CSV Files
    - Excel Spreadsheets
    """)
    st.markdown("---")
    st.markdown("Version 1.0.0")

# Main content area
st.title("🔍 Enterprise Content Analyzer")
st.markdown("Extract insights from multiple data sources using AI-powered analysis")

# Create two columns for input options
col1, col2 = st.columns(2)

with col1:
    input_type = st.radio(
        "Select Input Source:",
        ["Website URL", "Upload File"],
        format_func=lambda x: "🌐 " + x if x == "Website URL" else "📁 " + x
    )

data_content = None
error_message = None

# Handle different input types
if input_type == "Website URL":
    url = st.text_input("Enter Website URL", placeholder="https://example.com")
    if url:
        with st.spinner("Fetching webpage content..."):
            data_content, error_message = fetch_webpage_content(url)
            
else:
    st.markdown('<div class="upload-prompt">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drag and drop or click to upload",
        type=["pdf", "txt", "csv", "xlsx"],
        help="Supported formats: PDF, TXT, CSV, XLSX"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file:
        with st.spinner("Processing uploaded file..."):
            if uploaded_file.type == "application/pdf":
                data_content, error_message = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.type == "text/plain":
                data_content, error_message = extract_text_from_txt(uploaded_file)
            elif uploaded_file.type == "text/csv":
                data_content, error_message = extract_text_from_csv(uploaded_file)
            elif uploaded_file.type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
                data_content, error_message = extract_text_from_excel(uploaded_file)

# Display any error messages
if error_message:
    st.markdown(f'<div class="error-message">❌ {error_message}</div>', unsafe_allow_html=True)

# Query input and analysis
if data_content:
    st.markdown('<div class="success-message">✅ Content loaded successfully!</div>', unsafe_allow_html=True)
    
    user_query = st.text_area(
        "What would you like to know about the content?",
        placeholder="Enter your question here...",
        height=100
    )

    if st.button("🔍 Analyze Content", use_container_width=True):
        if not user_query:
            st.warning("⚠️ Please enter a question about the content.")
        else:
            with st.spinner("🤖 AI is analyzing your content..."):
                analysis_prompt = f"""
                Analyze the following content and answer the user's question:
                
                User Query: {user_query}
                
                Content:
                {data_content[:8000]}
                
                Provide a structured and detailed response.
                """
                response = multimodal_Agent.run(analysis_prompt)
                
                st.markdown("### 📊 Analysis Results")
                st.markdown("---")
                st.markdown(response.content)
