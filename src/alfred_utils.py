"""
Alfred-specific utilities for handling snippet file format, folder operations, and compatibility.
"""

import json
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

from .exceptions import AlfredFolderError, ValidationError, SnippetError


class AlfredUtils:
    """Utilities for Alfred snippet management and file operations."""
    
    def __init__(self, snippets_path: str):
        """
        Initialize Alfred utilities with the path to Alfred snippets folder.
        
        Args:
            snippets_path: Path to Alfred snippets directory
            
        Raises:
            AlfredFolderError: If the snippets path is invalid or inaccessible
        """
        self.snippets_path = Path(snippets_path).expanduser().resolve()
        self._validate_snippets_folder()
    
    def _validate_snippets_folder(self) -> None:
        """
        Validate that the Alfred snippets folder exists and is writable.
        
        Raises:
            AlfredFolderError: If folder validation fails
        """
        if not self.snippets_path.exists():
            raise AlfredFolderError(f"Alfred snippets folder does not exist: {self.snippets_path}")
        
        if not self.snippets_path.is_dir():
            raise AlfredFolderError(f"Alfred snippets path is not a directory: {self.snippets_path}")
        
        if not os.access(self.snippets_path, os.W_OK):
            raise AlfredFolderError(f"Alfred snippets folder is not writable: {self.snippets_path}")
    
    def get_existing_collections(self) -> List[str]:
        """
        Get list of existing collection (folder) names.
        
        Returns:
            List of collection names
        """
        collections = []
        try:
            for item in self.snippets_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    collections.append(item.name)
        except PermissionError as e:
            raise AlfredFolderError(f"Permission denied accessing collections: {e}")
        
        return sorted(collections)
    
    def create_collection(self, collection_name: str) -> Path:
        """
        Create a new collection folder if it doesn't exist.
        
        Args:
            collection_name: Name of the collection to create
            
        Returns:
            Path to the collection folder
            
        Raises:
            ValidationError: If collection name is invalid
            AlfredFolderError: If folder creation fails
        """
        if not collection_name or not collection_name.strip():
            raise ValidationError("Collection name cannot be empty")
        
        # Sanitize collection name
        sanitized_name = self._sanitize_folder_name(collection_name.strip())
        collection_path = self.snippets_path / sanitized_name
        
        try:
            collection_path.mkdir(exist_ok=True)
            return collection_path
        except PermissionError as e:
            raise AlfredFolderError(f"Permission denied creating collection '{sanitized_name}': {e}")
        except OSError as e:
            raise AlfredFolderError(f"Failed to create collection '{sanitized_name}': {e}")
    
    def _sanitize_folder_name(self, name: str) -> str:
        """
        Sanitize folder name for filesystem compatibility.
        
        Args:
            name: Original folder name
            
        Returns:
            Sanitized folder name
        """
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
        sanitized = sanitized.strip('. ')  # Remove leading/trailing dots and spaces
        
        if not sanitized:
            sanitized = "Snippets"
        
        return sanitized
    
    def get_existing_snippets(self, collection_name: Optional[str] = None) -> Dict[str, Dict]:
        """
        Get existing snippets, optionally filtered by collection.
        
        Args:
            collection_name: Optional collection name to filter by
            
        Returns:
            Dictionary mapping snippet keywords to snippet data
        """
        snippets = {}
        
        if collection_name:
            collections = [collection_name]
        else:
            collections = self.get_existing_collections()
        
        for collection in collections:
            collection_path = self.snippets_path / collection
            if not collection_path.exists():
                continue
                
            try:
                for snippet_file in collection_path.glob("*.json"):
                    try:
                        snippet_data = self._load_snippet_file(snippet_file)
                        if snippet_data and 'keyword' in snippet_data:
                            snippets[snippet_data['keyword']] = {
                                'collection': collection,
                                'file_path': snippet_file,
                                **snippet_data
                            }
                    except (json.JSONDecodeError, KeyError, ValidationError):
                        # Skip invalid snippet files
                        continue
            except PermissionError:
                # Skip collections we can't read
                continue
        
        return snippets
    
    def _load_snippet_file(self, file_path: Path) -> Optional[Dict]:
        """
        Load and validate a snippet file.
        
        Args:
            file_path: Path to snippet file
            
        Returns:
            Snippet data dictionary or None if invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate Alfred snippet format
            if 'alfredsnippet' not in data:
                return None
            
            snippet = data['alfredsnippet']
            required_fields = ['snippet', 'name', 'keyword', 'uid']
            
            if not all(field in snippet for field in required_fields):
                return None
            
            return snippet
            
        except (json.JSONDecodeError, FileNotFoundError, PermissionError):
            return None
    
    def generate_snippet_filename(self, keyword: str, uid: Optional[str] = None) -> str:
        """
        Generate a filename for a snippet.
        
        Args:
            keyword: Snippet keyword
            uid: Optional UID (will generate if not provided)
            
        Returns:
            Snippet filename
        """
        if not uid:
            uid = str(uuid.uuid4()).upper()
        
        # Sanitize keyword for filename
        safe_keyword = re.sub(r'[^a-zA-Z0-9_-]', '_', keyword.lower())
        return f"{safe_keyword}_{uid}.json"
    
    def create_snippet_file(self, collection_name: str, snippet_data: Dict) -> Path:
        """
        Create a snippet file in the specified collection.
        
        Args:
            collection_name: Name of the collection
            snippet_data: Snippet data with content, name, keyword, etc.
            
        Returns:
            Path to the created snippet file
            
        Raises:
            ValidationError: If snippet data is invalid
            AlfredFolderError: If file creation fails
        """
        self._validate_snippet_data(snippet_data)
        
        # Ensure collection exists
        collection_path = self.create_collection(collection_name)
        
        # Generate UID if not provided
        uid = snippet_data.get('uid', str(uuid.uuid4()).upper())
        
        # Create Alfred snippet format
        alfred_snippet = {
            "alfredsnippet": {
                "snippet": snippet_data['content'],
                "name": snippet_data['name'],
                "keyword": snippet_data['keyword'],
                "uid": uid
            }
        }
        
        # Generate filename
        filename = self.generate_snippet_filename(snippet_data['keyword'], uid)
        file_path = collection_path / filename
        
        # Check for duplicates
        if file_path.exists():
            raise AlfredFolderError(f"Snippet file already exists: {file_path}")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(alfred_snippet, f, indent=2, ensure_ascii=False)
            
            return file_path
            
        except PermissionError as e:
            raise AlfredFolderError(f"Permission denied creating snippet file: {e}")
        except OSError as e:
            raise AlfredFolderError(f"Failed to create snippet file: {e}")
    
    def _validate_snippet_data(self, snippet_data: Dict) -> None:
        """
        Validate snippet data for required fields and format.
        
        Args:
            snippet_data: Snippet data to validate
            
        Raises:
            ValidationError: If validation fails
        """
        required_fields = ['content', 'name', 'keyword']
        
        for field in required_fields:
            if field not in snippet_data:
                raise ValidationError(f"Missing required field: {field}")
            
            if not snippet_data[field] or not str(snippet_data[field]).strip():
                raise ValidationError(f"Field '{field}' cannot be empty")
        
        # Validate keyword format
        keyword = snippet_data['keyword'].strip()
        if not re.match(r'^[a-zA-Z0-9_-]+$', keyword):
            raise ValidationError(f"Invalid keyword format: {keyword}")
    
    def check_duplicate_keyword(self, keyword: str, collection_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if a keyword already exists.
        
        Args:
            keyword: Keyword to check
            collection_name: Optional collection to limit search to
            
        Returns:
            Tuple of (is_duplicate, existing_collection_name)
        """
        existing_snippets = self.get_existing_snippets(collection_name)
        
        if keyword in existing_snippets:
            return True, existing_snippets[keyword]['collection']
        
        return False, None
    
    def delete_snippet(self, collection_name: str, keyword: str) -> bool:
        """
        Delete a snippet by keyword from a collection.
        
        Args:
            collection_name: Name of the collection
            keyword: Keyword of snippet to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            AlfredFolderError: If deletion fails
        """
        existing_snippets = self.get_existing_snippets(collection_name)
        
        if keyword not in existing_snippets:
            return False
        
        snippet_info = existing_snippets[keyword]
        file_path = snippet_info['file_path']
        
        try:
            file_path.unlink()
            return True
        except PermissionError as e:
            raise AlfredFolderError(f"Permission denied deleting snippet: {e}")
        except OSError as e:
            raise AlfredFolderError(f"Failed to delete snippet: {e}")