#!/usr/bin/env python3
"""Test the markdown parser directly"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.services.parser import MarkdownParser

# Read the sample feature file
with open('sample_feature.md', 'r') as f:
    content = f.read()

print("=== Testing Markdown Parser ===")
print(f"Content length: {len(content)}")
print(f"First 200 chars: {content[:200]}...")
print()

# Test the parser
parser = MarkdownParser()
try:
    result = parser.parse_document(content)
    print("=== Parser Result ===")
    print(f"User stories: {len(result.get('user_stories', []))}")
    print(f"Acceptance criteria: {len(result.get('acceptance_criteria', []))}")
    print(f"Features: {len(result.get('features', []))}")
    print()
    
    if result.get('features'):
        for i, feature in enumerate(result['features']):
            print(f"Feature {i+1}:")
            print(f"  Title: {feature.get('title', 'N/A')}")
            print(f"  User stories length: {len(feature.get('user_stories', ''))}")
            print(f"  Acceptance criteria length: {len(feature.get('acceptance_criteria', ''))}")
            print()
    else:
        print("No features found!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
