#!/usr/bin/env python3
"""
Standalone Streamlit application for ScenarioWizard Frontend
Phase 3: Frontend & Export Implementation
"""

import streamlit as st
import sys
import os
import asyncio
from typing import Optional

# Add the app directory to Python path
# This allows running the script from the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app modules
from app.core.config import get_settings
from app.services.database import DatabaseService
from app.services.parser import MarkdownParser
from app.services.llm_service import LLMServiceManager

def main():
    """Main Streamlit application entry point"""
    st.set_page_config(
        page_title="ScenarioWizard",
        page_icon="🧙‍♂️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🧙‍♂️ ScenarioWizard")
    st.markdown("**BDD Scenario Generation Tool**")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # API Configuration
        st.subheader("API Settings")
        api_base_url = st.text_input(
            "API Base URL",
            value="http://localhost:8000/api/v1",
            help="Base URL for the ScenarioWizard API"
        )
        
        # LLM Configuration
        st.subheader("LLM Settings")
        llm_provider = st.selectbox(
            "LLM Provider",
            ["grok", "claude"],
            help="Choose the LLM provider for scenario generation"
        )
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📄 Upload Document", "🔍 View Documents", "⚙️ Settings"])
    
    with tab1:
        st.header("Upload Document")
        st.markdown("Upload a markdown file containing user stories and acceptance criteria.")
        
        uploaded_file = st.file_uploader(
            "Choose a markdown file",
            type=['md'],
            help="Upload a .md file with user stories and acceptance criteria"
        )
        
        if uploaded_file is not None:
            st.success(f"File uploaded: {uploaded_file.name}")
            
            # Display file content
            content = uploaded_file.read().decode("utf-8")
            st.text_area("File Content", content, height=300)
            
            if st.button("Process Document"):
                with st.spinner("Processing document..."):
                    try:
                        # Here you would call your API to process the document
                        st.success("Document processed successfully!")
                    except Exception as e:
                        st.error(f"Error processing document: {str(e)}")
    
    with tab2:
        st.header("View Documents")
        st.markdown("View and manage uploaded documents.")
        
        # Placeholder for document list
        st.info("Document management features will be implemented here.")
    
    with tab3:
        st.header("Settings")
        st.markdown("Configure application settings.")
        
        # Settings form
        with st.form("settings_form"):
            st.subheader("API Configuration")
            api_url = st.text_input("API URL", value="http://localhost:8000")
            
            st.subheader("LLM Configuration")
            grok_key = st.text_input("Grok API Key", type="password")
            claude_key = st.text_input("Claude API Key", type="password")
            
            submitted = st.form_submit_button("Save Settings")
            if submitted:
                st.success("Settings saved!")

if __name__ == "__main__":
    main()
