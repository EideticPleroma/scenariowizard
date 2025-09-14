#!/usr/bin/env python3
"""
Standalone Streamlit application for ScenarioWizard Frontend
Phase 3: Frontend & Export Implementation
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import and run the Streamlit app
from app.main_streamlit import main

if __name__ == "__main__":
    main()
