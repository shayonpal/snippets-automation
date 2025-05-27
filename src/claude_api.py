"""
Anthropic Claude API integration for analyzing snippet content and generating metadata.
"""

import json
import os
import time
from typing import Dict, List, Optional, Any
import requests
from dataclasses import dataclass

from exceptions import APIError, NetworkError, RateLimitError, ValidationError


@dataclass
class SnippetSuggestion:
    """Data class for AI-generated snippet suggestions."""
    collection: str
    name: str
    keyword: str
    description: str
    confidence: str  # 'high', 'medium', 'low'


class ClaudeAPI:
    """
    Client for interacting with Anthropic's Claude API for snippet analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude API client.
        
        Args:
            api_key: Anthropic API key (will read from env if not provided)
            
        Raises:
            APIError: If API key is not available
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise APIError("ANTHROPIC_API_KEY environment variable is required")
        
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-3-5-haiku-latest"
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': self.api_key,
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01'
        })
    
    def analyze_snippet(self, content: str, existing_collections: List[str]) -> SnippetSuggestion:
        """
        Analyze snippet content and generate metadata suggestions.
        
        Args:
            content: The snippet content to analyze
            existing_collections: List of existing collection names
            
        Returns:
            SnippetSuggestion with AI-generated metadata
            
        Raises:
            APIError: If API call fails
            ValidationError: If response format is invalid
        """
        if not content or not content.strip():
            raise ValidationError("Snippet content cannot be empty")
        
        prompt = self._build_analysis_prompt(content, existing_collections)
        
        try:
            response = self._make_api_call(prompt)
            return self._parse_suggestion_response(response)
        except Exception as e:
            if isinstance(e, (APIError, ValidationError)):
                raise
            raise APIError(f"Unexpected error during snippet analysis: {e}")
    
    def _build_analysis_prompt(self, content: str, existing_collections: List[str]) -> str:
        """
        Build the prompt for snippet analysis.
        
        Args:
            content: Snippet content
            existing_collections: List of existing collections
            
        Returns:
            Formatted prompt string
        """
        collections_text = ", ".join(existing_collections) if existing_collections else "None"
        
        prompt = f"""Analyze this snippet content and suggest appropriate metadata for an Alfred snippet:

Content:
{content}

Existing collections: {collections_text}

Please provide a JSON response with the following structure:
{{
  "collection": "suggested collection name (Title Case)",
  "name": "descriptive snippet name (Title Case, start with topic if applicable)",
  "keyword": "trigger keyword (lowercase, topic_function format with underscores or dashes)",
  "description": "brief description (1-2 sentences)",
  "confidence": "high|medium|low"
}}

Rules:
1. If the content matches an existing collection topic, use that collection
2. For new collections, use Title Case (e.g., "Git", "Dataview", "Terminal")
3. Names should be descriptive and start with the topic when possible (e.g., "Git: Pretty Log")
4. Keywords should be lowercase with topic prefix (e.g., "git_log5", "dv_projects")
5. Set confidence to:
   - "high" if you're very confident about the categorization
   - "medium" if reasonably confident but could fit multiple categories
   - "low" if the content is ambiguous or you're unsure

Examples:
- Git command → collection: "Git", keyword: "git_something"
- Dataview query → collection: "Dataview", keyword: "dv_something"
- Shell command → collection: "Terminal", keyword: "term_something"
- Code snippet → collection based on language/framework

Respond only with valid JSON."""
        
        return prompt
    
    def _make_api_call(self, prompt: str) -> Dict[str, Any]:
        """
        Make API call to Claude with retry logic.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            API response data
            
        Raises:
            APIError: If API call fails after retries
            RateLimitError: If rate limited
            NetworkError: If network issues
        """
        payload = {
            "model": self.model,
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('retry-after', 60))
                    if attempt < self.max_retries - 1:
                        time.sleep(min(retry_after, 300))  # Max 5 minutes
                        continue
                    else:
                        raise RateLimitError("Rate limit exceeded, please try again later")
                elif response.status_code in [500, 502, 503, 504]:
                    # Server errors - retry
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        raise APIError(f"Server error: {response.status_code}")
                else:
                    # Client errors - don't retry
                    error_msg = f"API error {response.status_code}: {response.text}"
                    raise APIError(error_msg)
                    
            except requests.exceptions.Timeout as e:
                last_exception = NetworkError(f"Request timeout: {e}")
            except requests.exceptions.ConnectionError as e:
                last_exception = NetworkError(f"Connection error: {e}")
            except requests.exceptions.RequestException as e:
                last_exception = APIError(f"Request error: {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (2 ** attempt))
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        else:
            raise APIError("API call failed after all retries")
    
    def _parse_suggestion_response(self, response: Dict[str, Any]) -> SnippetSuggestion:
        """
        Parse API response and extract suggestion data.
        
        Args:
            response: Raw API response
            
        Returns:
            Parsed SnippetSuggestion
            
        Raises:
            ValidationError: If response format is invalid
        """
        try:
            # Extract content from Claude response
            if 'content' not in response or not response['content']:
                raise ValidationError("Empty response from API")
            
            content = response['content'][0]
            if content['type'] != 'text':
                raise ValidationError("Invalid response type from API")
            
            text_content = content['text'].strip()
            
            # Parse JSON from the response
            try:
                suggestion_data = json.loads(text_content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text_content, re.DOTALL)
                if json_match:
                    suggestion_data = json.loads(json_match.group(1))
                else:
                    # Try to find JSON-like content
                    json_match = re.search(r'\{[^}]*\}', text_content, re.DOTALL)
                    if json_match:
                        suggestion_data = json.loads(json_match.group(0))
                    else:
                        raise ValidationError(f"Could not parse JSON from response: {text_content}")
            
            # Validate required fields
            required_fields = ['collection', 'name', 'keyword', 'description', 'confidence']
            for field in required_fields:
                if field not in suggestion_data:
                    raise ValidationError(f"Missing required field in API response: {field}")
            
            # Validate confidence level
            if suggestion_data['confidence'] not in ['high', 'medium', 'low']:
                suggestion_data['confidence'] = 'low'  # Default to low if invalid
            
            return SnippetSuggestion(
                collection=str(suggestion_data['collection']).strip(),
                name=str(suggestion_data['name']).strip(),
                keyword=str(suggestion_data['keyword']).strip().lower(),
                description=str(suggestion_data['description']).strip(),
                confidence=suggestion_data['confidence']
            )
            
        except (KeyError, IndexError, TypeError) as e:
            raise ValidationError(f"Invalid API response format: {e}")
    
    def test_connection(self) -> bool:
        """
        Test the API connection and authentication.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/messages",
                headers={'x-api-key': self.api_key},
                timeout=10
            )
            # We expect a 405 (Method Not Allowed) for GET on messages endpoint
            # but this confirms the API key is valid
            return response.status_code in [200, 405]
        except:
            return False