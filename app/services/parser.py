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

        # Look for feature sections
        feature_pattern = r'##\s*Feature:\s*(.+?)\n(.*?)(?=\n##|\Z)'
        for match in re.finditer(feature_pattern, content, re.DOTALL | re.IGNORECASE):
            feature_title = match.group(1).strip()
            feature_content = match.group(2).strip()

            features.append({
                "title": feature_title,
                "content": feature_content
            })

        return features
