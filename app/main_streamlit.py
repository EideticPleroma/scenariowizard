import streamlit as st
import requests
import json
from typing import List, Dict, Any
import io
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="QA Scenario Writer",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def main():
    st.title("🧪 QA Scenario Writer")
    st.markdown("Generate BDD scenarios from Markdown documents")

    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Choose a page",
            ["Upload Document", "View Documents", "Generate Scenarios", "Export Results"]
        )

    # Main content
    if page == "Upload Document":
        upload_document_page()
    elif page == "View Documents":
        view_documents_page()
    elif page == "Generate Scenarios":
        generate_scenarios_page()
    elif page == "Export Results":
        export_results_page()

def upload_document_page():
    st.header("📄 Upload Document")
    st.markdown("Upload a Markdown document containing user stories and acceptance criteria")

    # File upload
    uploaded_file = st.file_uploader(
        "Choose a Markdown file",
        type=['md'],
        help="Only .md files are supported"
    )

    if uploaded_file is not None:
        # Display file content
        content = uploaded_file.read().decode('utf-8')
        st.subheader("Document Preview")
        st.text_area("Content", content, height=300)

        # Upload button
        if st.button("Upload Document", type="primary"):
            with st.spinner("Uploading document..."):
                try:
                    # Upload to API
                    files = {"file": (uploaded_file.name, content, "text/markdown")}
                    response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)

                    if response.status_code == 200:
                        document = response.json()
                        st.success(f"Document uploaded successfully! ID: {document['id']}")
                        st.session_state['last_document_id'] = document['id']
                    else:
                        st.error(f"Upload failed: {response.text}")

                except Exception as e:
                    st.error(f"Error uploading document: {str(e)}")

def view_documents_page():
    st.header("📋 View Documents")

    try:
        # Get documents from API
        response = requests.get(f"{API_BASE_URL}/documents/")
        if response.status_code == 200:
            documents = response.json()

            if not documents:
                st.info("No documents found. Upload a document to get started.")
                return

            # Display documents
            for doc in documents:
                with st.expander(f"📄 {doc['filename']} - {doc['status']}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**ID:** {doc['id']}")
                        st.write(f"**Status:** {doc['status']}")

                    with col2:
                        st.write(f"**Created:** {doc['created_at']}")
                        if doc['processed_at']:
                            st.write(f"**Processed:** {doc['processed_at']}")

                    with col3:
                        if doc['error_message']:
                            st.error(f"**Error:** {doc['error_message']}")
                        else:
                            st.success("✅ Ready")

                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"View Details", key=f"view_{doc['id']}"):
                            st.session_state['selected_document'] = doc['id']

                    with col2:
                        if doc['status'] == 'completed':
                            if st.button(f"Generate Scenarios", key=f"gen_{doc['id']}"):
                                st.session_state['selected_document'] = doc['id']
                                st.rerun()

                    with col3:
                        if doc['status'] == 'completed':
                            if st.button(f"Export", key=f"exp_{doc['id']}"):
                                st.session_state['selected_document'] = doc['id']
                                st.rerun()
        else:
            st.error(f"Failed to load documents: {response.text}")

    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")

def generate_scenarios_page():
    st.header("🚀 Generate Scenarios")

    # Document selection
    if 'selected_document' in st.session_state:
        document_id = st.session_state['selected_document']
    else:
        st.info("Please select a document from the 'View Documents' page first.")
        return

    st.write(f"**Selected Document ID:** {document_id}")

    # Test type selection
    st.subheader("Test Types")
    test_types = st.multiselect(
        "Select test types to generate",
        ["unit", "integration", "e2e", "api", "ui"],
        default=["unit", "integration", "e2e"],
        help="Choose which types of tests to generate"
    )

    # LLM provider selection
    st.subheader("LLM Provider")
    provider = st.selectbox(
        "Select LLM provider",
        ["grok", "anthropic"],
        help="Grok is faster, Anthropic is more reliable"
    )

    # Generation options
    st.subheader("Generation Options")
    col1, col2 = st.columns(2)

    with col1:
        max_scenarios = st.number_input(
            "Max scenarios per test type",
            min_value=1,
            max_value=10,
            value=3,
            help="Maximum number of scenarios to generate per test type"
        )

    with col2:
        include_examples = st.checkbox(
            "Include examples tables",
            value=True,
            help="Generate examples tables for data-driven tests"
        )

    # Generate button
    if st.button("Generate Scenarios", type="primary"):
        if not test_types:
            st.error("Please select at least one test type.")
            return

        with st.spinner("Generating scenarios..."):
            try:
                # Call API to generate scenarios
                payload = {
                    "test_types": test_types,
                    "provider": provider,
                    "max_scenarios": max_scenarios,
                    "include_examples": include_examples
                }

                response = requests.post(
                    f"{API_BASE_URL}/scenarios/generate",
                    params={"document_id": document_id},
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    st.success("Scenarios generated successfully!")

                    # Display results
                    st.subheader("Generation Results")
                    st.write(f"**Total scenarios:** {result['total_scenarios']}")
                    st.write(f"**Features processed:** {result['features_processed']}")

                    # Display feature results
                    for feature_id, feature_result in result['feature_results'].items():
                        with st.expander(f"Feature: {feature_result['feature_title']}"):
                            st.write(f"**Scenarios generated:** {feature_result['scenarios_count']}")

                            if 'error' in feature_result:
                                st.error(f"Error: {feature_result['error']}")
                            else:
                                for scenario in feature_result['scenarios']:
                                    st.write(f"**{scenario['test_type'].upper()} Test:**")
                                    st.code(scenario['content'], language='gherkin')

                    st.session_state['last_generation_result'] = result

                else:
                    st.error(f"Generation failed: {response.text}")

            except Exception as e:
                st.error(f"Error generating scenarios: {str(e)}")

def export_results_page():
    st.header("📤 Export Results")

    if 'last_generation_result' not in st.session_state:
        st.info("No generation results to export. Generate scenarios first.")
        return

    result = st.session_state['last_generation_result']

    st.subheader("Export Options")

    # Export format selection
    export_format = st.selectbox(
        "Select export format",
        ["gherkin", "cucumber", "playwright", "pytest"],
        help="Choose the format for exported test files"
    )

    # Export scope
    export_scope = st.radio(
        "Export scope",
        ["All scenarios", "By test type", "By feature"],
        help="Choose which scenarios to export"
    )

    if export_scope == "By test type":
        available_types = set()
        for feature_result in result['feature_results'].values():
            if 'scenarios' in feature_result:
                for scenario in feature_result['scenarios']:
                    available_types.add(scenario['test_type'])

        selected_types = st.multiselect(
            "Select test types",
            list(available_types),
            default=list(available_types)
        )
    elif export_scope == "By feature":
        available_features = list(result['feature_results'].keys())
        selected_features = st.multiselect(
            "Select features",
            available_features,
            default=available_features
        )

    # Export button
    if st.button("Export Scenarios", type="primary"):
        with st.spinner("Preparing export..."):
            try:
                # Call API to export scenarios
                export_payload = {
                    "format": export_format,
                    "scope": export_scope,
                    "test_types": selected_types if export_scope == "By test type" else None,
                    "feature_ids": selected_features if export_scope == "By feature" else None
                }

                response = requests.post(
                    f"{API_BASE_URL}/scenarios/export",
                    json=export_payload
                )

                if response.status_code == 200:
                    # Handle ZIP file download
                    if export_format == "zip":
                        st.download_button(
                            label="Download ZIP Archive",
                            data=response.content,
                            file_name=f"scenarios_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip"
                        )
                    else:
                        export_result = response.json()
                        st.success("Export completed successfully!")

                        # Display download links for individual files
                        st.subheader("Download Files")
                        for filename, content in export_result['files'].items():
                            st.download_button(
                                label=f"Download {filename}",
                                data=content,
                                file_name=filename,
                                mime="text/plain"
                            )
                else:
                    st.error(f"Export failed: {response.text}")

            except Exception as e:
                st.error(f"Error exporting scenarios: {str(e)}")

if __name__ == "__main__":
    main()
