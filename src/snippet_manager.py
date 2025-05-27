"""
Core snippet management functionality for Alfred snippet creation, validation, and operations.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

from .alfred_utils import AlfredUtils
from .claude_api import ClaudeAPI, SnippetSuggestion
from .exceptions import (
    SnippetError, 
    DuplicateSnippetError, 
    ValidationError,
    APIError,
    ConfigurationError
)


class SnippetManager:
    """
    Main class for managing Alfred snippets with AI-powered categorization.
    """
    
    def __init__(self, alfred_snippets_path: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the snippet manager.
        
        Args:
            alfred_snippets_path: Path to Alfred snippets folder (uses env var if not provided)
            api_key: Anthropic API key (uses env var if not provided)
            
        Raises:
            ConfigurationError: If required configuration is missing
        """
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Get Alfred snippets path
        snippets_path = alfred_snippets_path or os.getenv('ALFRED_SNIPPETS_PATH')
        if not snippets_path:
            raise ConfigurationError(
                "Alfred snippets path not provided. Set ALFRED_SNIPPETS_PATH environment variable "
                "or pass alfred_snippets_path parameter."
            )
        
        # Initialize components
        try:
            self.alfred_utils = AlfredUtils(snippets_path)
            self.claude_api = ClaudeAPI(api_key)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize components: {e}")
        
        self.logger.info(f"SnippetManager initialized with path: {snippets_path}")
    
    def create_snippet(
        self,
        content: str,
        name: Optional[str] = None,
        keyword: Optional[str] = None,
        collection: Optional[str] = None,
        description: Optional[str] = None,
        use_ai: bool = True,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new Alfred snippet with optional AI categorization.
        
        Args:
            content: The snippet content
            name: Optional snippet name (AI will suggest if not provided)
            keyword: Optional keyword (AI will suggest if not provided)
            collection: Optional collection name (AI will suggest if not provided)
            description: Optional description (AI will suggest if not provided)
            use_ai: Whether to use AI for missing metadata
            overwrite: Whether to overwrite existing snippets with same keyword
            
        Returns:
            Dictionary with creation results and metadata
            
        Raises:
            ValidationError: If input validation fails
            DuplicateSnippetError: If snippet already exists and overwrite=False
            SnippetError: If creation fails
        """
        if not content or not content.strip():
            raise ValidationError("Snippet content cannot be empty")
        
        content = content.strip()
        
        # Use AI to fill in missing metadata if requested
        suggestion = None
        if use_ai and (not name or not keyword or not collection):
            try:
                existing_collections = self.alfred_utils.get_existing_collections()
                suggestion = self.claude_api.analyze_snippet(content, existing_collections)
                self.logger.info(f"AI suggestion received with confidence: {suggestion.confidence}")
            except APIError as e:
                self.logger.warning(f"AI analysis failed: {e}")
                if not all([name, keyword, collection]):
                    raise SnippetError(f"AI analysis failed and required metadata missing: {e}")
        
        # Use provided values or AI suggestions
        final_name = name or (suggestion.name if suggestion else None)
        final_keyword = keyword or (suggestion.keyword if suggestion else None)
        final_collection = collection or (suggestion.collection if suggestion else None)
        final_description = description or (suggestion.description if suggestion else "")
        
        # Validate that we have all required fields
        if not all([final_name, final_keyword, final_collection]):
            missing = []
            if not final_name: missing.append("name")
            if not final_keyword: missing.append("keyword")
            if not final_collection: missing.append("collection")
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")
        
        # Check for duplicates
        is_duplicate, existing_collection = self.alfred_utils.check_duplicate_keyword(final_keyword)
        if is_duplicate and not overwrite:
            raise DuplicateSnippetError(
                f"Snippet with keyword '{final_keyword}' already exists in collection '{existing_collection}'"
            )
        
        # Delete existing snippet if overwriting
        if is_duplicate and overwrite:
            self.alfred_utils.delete_snippet(existing_collection, final_keyword)
            self.logger.info(f"Overwriting existing snippet: {final_keyword}")
        
        # Create snippet data
        snippet_data = {
            'content': content,
            'name': final_name,
            'keyword': final_keyword,
            'description': final_description
        }
        
        # Create the snippet file
        try:
            file_path = self.alfred_utils.create_snippet_file(final_collection, snippet_data)
            
            result = {
                'success': True,
                'file_path': str(file_path),
                'collection': final_collection,
                'name': final_name,
                'keyword': final_keyword,
                'description': final_description,
                'ai_suggested': suggestion is not None,
                'ai_confidence': suggestion.confidence if suggestion else None,
                'overwritten': is_duplicate and overwrite
            }
            
            self.logger.info(f"Snippet created successfully: {final_keyword} in {final_collection}")
            return result
            
        except Exception as e:
            raise SnippetError(f"Failed to create snippet file: {e}")
    
    def create_snippets_batch(
        self,
        snippets: List[Dict[str, Any]],
        use_ai: bool = True,
        overwrite: bool = False,
        continue_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Create multiple snippets from a batch.
        
        Args:
            snippets: List of snippet dictionaries with 'content' and optional metadata
            use_ai: Whether to use AI for missing metadata
            overwrite: Whether to overwrite existing snippets
            continue_on_error: Whether to continue processing after errors
            
        Returns:
            Dictionary with batch processing results
        """
        results = {
            'total': len(snippets),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'created_snippets': []
        }
        
        for i, snippet_data in enumerate(snippets):
            try:
                # Get content from either 'content' or 'snippet' field for compatibility
                content = snippet_data.get('content') or snippet_data.get('snippet')
                if not content:
                    raise ValidationError(f"Snippet {i+1}: Missing 'content' or 'snippet' field")
                
                result = self.create_snippet(
                    content=content,
                    name=snippet_data.get('name'),
                    keyword=snippet_data.get('keyword'),
                    collection=snippet_data.get('collection'),
                    description=snippet_data.get('description'),
                    use_ai=use_ai,
                    overwrite=overwrite
                )
                
                results['successful'] += 1
                results['created_snippets'].append(result)
                
            except Exception as e:
                results['failed'] += 1
                error_info = {
                    'index': i + 1,
                    'error': str(e),
                    'type': type(e).__name__,
                    'content_preview': snippet_data.get('content', '')[:50] + '...'
                }
                results['errors'].append(error_info)
                
                self.logger.error(f"Failed to create snippet {i+1}: {e}")
                
                if not continue_on_error:
                    break
        
        self.logger.info(f"Batch processing complete: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def get_snippet_suggestions(self, content: str) -> Optional[SnippetSuggestion]:
        """
        Get AI suggestions for snippet metadata without creating the snippet.
        
        Args:
            content: Snippet content to analyze
            
        Returns:
            SnippetSuggestion or None if AI analysis fails
        """
        try:
            existing_collections = self.alfred_utils.get_existing_collections()
            suggestion = self.claude_api.analyze_snippet(content, existing_collections)
            return suggestion
        except APIError as e:
            self.logger.warning(f"AI suggestion failed: {e}")
            return None
    
    def list_collections(self) -> List[str]:
        """
        Get list of existing collections.
        
        Returns:
            List of collection names
        """
        return self.alfred_utils.get_existing_collections()
    
    def list_snippets(self, collection: Optional[str] = None) -> Dict[str, Dict]:
        """
        List existing snippets, optionally filtered by collection.
        
        Args:
            collection: Optional collection name to filter by
            
        Returns:
            Dictionary mapping keywords to snippet data
        """
        return self.alfred_utils.get_existing_snippets(collection)
    
    def delete_snippet(self, keyword: str, collection: Optional[str] = None) -> bool:
        """
        Delete a snippet by keyword.
        
        Args:
            keyword: Snippet keyword
            collection: Optional collection name (searches all if not provided)
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            SnippetError: If multiple snippets found with same keyword in different collections
        """
        if collection:
            return self.alfred_utils.delete_snippet(collection, keyword)
        
        # Search all collections for the keyword
        existing_snippets = self.alfred_utils.get_existing_snippets()
        
        if keyword not in existing_snippets:
            return False
        
        snippet_info = existing_snippets[keyword]
        return self.alfred_utils.delete_snippet(snippet_info['collection'], keyword)
    
    def validate_setup(self) -> Dict[str, Any]:
        """
        Validate the setup and configuration.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'alfred_folder': False,
            'api_connection': False,
            'collections_count': 0,
            'snippets_count': 0,
            'errors': []
        }
        
        # Check Alfred folder
        try:
            collections = self.alfred_utils.get_existing_collections()
            results['alfred_folder'] = True
            results['collections_count'] = len(collections)
            
            snippets = self.alfred_utils.get_existing_snippets()
            results['snippets_count'] = len(snippets)
            
        except Exception as e:
            results['errors'].append(f"Alfred folder error: {e}")
        
        # Check API connection
        try:
            if self.claude_api.test_connection():
                results['api_connection'] = True
            else:
                results['errors'].append("API connection test failed")
        except Exception as e:
            results['errors'].append(f"API error: {e}")
        
        return results