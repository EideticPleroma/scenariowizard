"""
BDD-Wizard Main Application
Streamlit web interface for BDD scenario generation
"""

import streamlit as st

def main():
    st.set_page_config(
        page_title="BDD-Wizard",
        page_icon="🧙‍♂️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🧙‍♂️ BDD-Wizard")
    st.subtitle("AI-Powered BDD Scenario Generation")
    
    st.markdown("""
    Welcome to BDD-Wizard! This tool helps you transform your business requirements, 
    user stories, and acceptance criteria into executable BDD scenarios automatically.
    
    ## Getting Started
    
    1. **Upload Documents**: Upload your Markdown files with user stories and acceptance criteria
    2. **Generate Scenarios**: Let our AI create BDD scenarios from your requirements
    3. **Export Features**: Download .feature files ready for your BDD framework
    
    ## Features
    
    - 📝 **Markdown Input**: Process user stories and requirements from Markdown documents
    - 🤖 **AI-Powered**: Uses advanced LLMs to create accurate BDD scenarios
    - 🎯 **Gherkin Output**: Exports standard .feature files compatible with Cucumber, SpecFlow, and other BDD frameworks
    - 🔧 **MCP Integration**: Exposes tools via Model Context Protocol for external AI agents
    - ⚡ **Rapid Development**: Built with FastAPI and Streamlit for quick iteration
    - 🐳 **Docker Ready**: Simple deployment with Docker containers
    """)
    
    st.info("🚧 This is a work in progress. The full functionality will be available soon!")

if __name__ == "__main__":
    main()
