import markdown
from markdown.extensions import codehilite, fenced_code
from typing import List, Dict, Any
import re

class MarkdownParser:
    def __init__(self):
        self.md = markdown.Markdown(
            extensions=['codehilite', 'fenced_code', 'tables']
        )

    def parse_document(self, content: str) -> Dict[str, Any]:
        """Parse markdown content and extract structure"""
        try:
            # Validate content is not empty
            if not content or not content.strip():
                raise ValueError("Failed to parse markdown: Content is empty")
            
            # Extract user stories
            user_stories = self._extract_user_stories(content)

            # Extract acceptance criteria
            acceptance_criteria = self._extract_acceptance_criteria(content)

            # Extract features
            features = self._extract_features(content)

            return {
                "user_stories": user_stories,
                "acceptance_criteria": acceptance_criteria,
                "features": features,
                "raw_content": content
            }
        except Exception as e:
            raise ValueError(f"Failed to parse markdown: {e}")

    def _extract_user_stories(self, content: str) -> List[str]:
        """Extract user stories from markdown content"""
        pattern = r'##\s*User Stories?\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if not match:
            return []

        stories_text = match.group(1)
        stories = []

        # Extract individual stories
        story_pattern = r'-\s*(.+?)(?=\n-|\Z)'
        for match in re.finditer(story_pattern, stories_text, re.DOTALL):
            stories.append(match.group(1).strip())

        return stories

    def _extract_acceptance_criteria(self, content: str) -> List[str]:
        """Extract acceptance criteria from markdown content"""
        pattern = r'##\s*Acceptance Criteria\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if not match:
            return []

        criteria_text = match.group(1)
        criteria = []

        # Extract individual criteria
        criteria_pattern = r'-\s*(.+?)(?=\n-|\Z)'
        for match in re.finditer(criteria_pattern, criteria_text, re.DOTALL):
            criteria.append(match.group(1).strip())

        return criteria

    def _extract_features(self, content: str) -> List[Dict[str, str]]:
        """Extract features from markdown content"""
        features = []

        # Look for main feature title (e.g., "# User Authentication Feature")
        main_feature_match = re.search(r'^#\s*(.+?)\s*$', content, re.MULTILINE)
        if main_feature_match:
            main_feature_title = main_feature_match.group(1).strip()
            
            # Extract user stories section
            user_stories_section = self._extract_user_stories_section(content)
            
            # Extract acceptance criteria section
            acceptance_criteria_section = self._extract_acceptance_criteria_section(content)
            
            features.append({
                "title": main_feature_title,
                "user_stories": user_stories_section,
                "acceptance_criteria": acceptance_criteria_section
            })

        return features

    def _extract_user_stories_section(self, content: str) -> str:
        """Extract the entire user stories section as text"""
        pattern = r'##\s*User Stories?\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_acceptance_criteria_section(self, content: str) -> str:
        """Extract all acceptance criteria from the document"""
        # Look for acceptance criteria under user stories
        criteria_pattern = r'\*\*Acceptance Criteria:\*\*\s*\n(.*?)(?=\n\n|\n###|\Z)'
        matches = re.findall(criteria_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return '\n\n'.join(match.strip() for match in matches)
        
        # Fallback: look for a dedicated acceptance criteria section
        pattern = r'##\s*Acceptance Criteria\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""
