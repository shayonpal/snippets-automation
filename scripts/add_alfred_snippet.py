#!/usr/bin/env python3
"""
Ad hoc snippet creation script for single snippet creation with Raycast integration.

Usage:
    python add_alfred_snippet.py [content] [--no-ai] [--overwrite]
    
If content is not provided, will attempt to read from clipboard.
"""

import argparse
import subprocess
import sys
from pathlib import Path
import logging

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from snippet_manager import SnippetManager
from exceptions import SnippetError, ConfigurationError, DuplicateSnippetError, ValidationError


def get_clipboard_content() -> str:
    """
    Get content from macOS clipboard.
    
    Returns:
        Clipboard content as string
        
    Raises:
        RuntimeError: If clipboard access fails
    """
    try:
        result = subprocess.run(
            ['pbpaste'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to access clipboard: {e}")
    except FileNotFoundError:
        raise RuntimeError("pbpaste command not found (not running on macOS?)")


def show_notification(title: str, message: str, sound: bool = True) -> None:
    """
    Show macOS notification.
    
    Args:
        title: Notification title
        message: Notification message
        sound: Whether to play notification sound
    """
    try:
        sound_arg = "default" if sound else ""
        subprocess.run([
            'osascript', '-e',
            f'display notification "{message}" with title "{title}" sound name "{sound_arg}"'
        ], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to print if notification fails
        print(f"📢 {title}: {message}")


def prompt_user_choice(prompt: str, choices: list, allow_new: bool = False) -> str:
    """
    Prompt user to select from a list of choices.
    
    Args:
        prompt: Prompt message
        choices: List of available choices
        allow_new: Whether to allow entering a new value
        
    Returns:
        Selected choice or new value
    """
    print(f"\n{prompt}")
    
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    
    if allow_new:
        print(f"  {len(choices) + 1}. Enter new value")
    
    while True:
        try:
            user_input = input("\nEnter choice number: ").strip()
            
            if not user_input:
                continue
            
            choice_num = int(user_input)
            
            if 1 <= choice_num <= len(choices):
                return choices[choice_num - 1]
            elif allow_new and choice_num == len(choices) + 1:
                try:
                    new_value = input("Enter new value: ").strip()
                    if new_value:
                        return new_value
                    else:
                        print("Value cannot be empty. Please try again.")
                except (KeyboardInterrupt, EOFError):
                    print("\n\nOperation cancelled by user.")
                    sys.exit(1)
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(choices) + (1 if allow_new else 0)}")
                
        except ValueError:
            print("Please enter a valid number.")
        except (KeyboardInterrupt, EOFError):
            print("\n\nOperation cancelled by user.")
            sys.exit(1)


def prompt_manual_metadata(content: str, collections: list) -> dict:
    """
    Prompt user for manual metadata input.
    
    Args:
        content: Snippet content
        collections: Available collections
        
    Returns:
        Dictionary with metadata
    """
    print(f"\n{'='*60}")
    print("MANUAL METADATA INPUT")
    print(f"{'='*60}")
    print("Content preview:")
    print(content[:200] + ("..." if len(content) > 200 else ""))
    print(f"{'='*60}")
    
    # Collection
    if collections:
        collection = prompt_user_choice(
            "Select collection:",
            collections,
            allow_new=True
        )
    else:
        try:
            collection = input("\nEnter collection name: ").strip()
            while not collection:
                print("Collection name cannot be empty.")
                collection = input("Enter collection name: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nOperation cancelled by user.")
            sys.exit(1)
    
    # Name
    try:
        name = input(f"\nEnter snippet name (e.g., '{collection}: Description'): ").strip()
        while not name:
            print("Snippet name cannot be empty.")
            name = input("Enter snippet name: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    
    # Keyword
    try:
        keyword = input(f"\nEnter keyword (e.g., '{collection.lower()}_function'): ").strip()
        while not keyword:
            print("Keyword cannot be empty.")
            keyword = input("Enter keyword: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    
    # Description (optional)
    try:
        description = input("\nEnter description (optional): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    
    return {
        'collection': collection,
        'name': name,
        'keyword': keyword,
        'description': description
    }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Create a single Alfred snippet with AI categorization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use clipboard content
  python add_alfred_snippet.py
  
  # Provide content directly
  python add_alfred_snippet.py "echo 'Hello World'"
  
  # Disable AI and provide manual metadata
  python add_alfred_snippet.py "git status" --no-ai
  
  # Overwrite existing snippet
  python add_alfred_snippet.py "new content" --overwrite

Raycast Quicklink:
  file:///path/to/add_alfred_snippet.py?arguments={Query}
        """
    )
    
    parser.add_argument(
        'content',
        nargs='?',
        help='Snippet content (uses clipboard if not provided)'
    )
    
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Disable AI categorization (will prompt for manual input)'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing snippet with same keyword'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        # Get snippet content
        if args.content:
            content = args.content
            print(f"Using provided content ({len(content)} characters)")
        else:
            print("No content provided, reading from clipboard...")
            content = get_clipboard_content()
            if not content.strip():
                print("❌ Clipboard is empty")
                return 1
            print(f"Read {len(content)} characters from clipboard")
        
        content = content.strip()
        
        # Initialize snippet manager
        print("Initializing snippet manager...")
        manager = SnippetManager()
        
        # Validate setup
        validation = manager.validate_setup()
        if not validation['alfred_folder']:
            show_notification("Snippet Creation Failed", "Alfred folder not accessible", sound=False)
            print("❌ Alfred snippets folder is not accessible")
            return 1
        
        collections = manager.list_collections()
        print(f"Found {len(collections)} existing collections")
        
        # Use AI categorization unless disabled
        use_ai = not args.no_ai
        if use_ai and not validation['api_connection']:
            print("⚠️  AI connection failed, falling back to manual input")
            use_ai = False
        
        metadata = {}
        suggestion = None
        
        if use_ai:
            print("🤖 Analyzing content with AI...")
            suggestion = manager.get_snippet_suggestions(content)
            
            if suggestion:
                print(f"AI suggestion (confidence: {suggestion.confidence}):")
                print(f"  Collection: {suggestion.collection}")
                print(f"  Name: {suggestion.name}")
                print(f"  Keyword: {suggestion.keyword}")
                print(f"  Description: {suggestion.description}")
                
                # Use AI suggestion if confidence is high, otherwise prompt
                if suggestion.confidence == 'high':
                    metadata = {
                        'collection': suggestion.collection,
                        'name': suggestion.name,
                        'keyword': suggestion.keyword,
                        'description': suggestion.description
                    }
                    print("✅ Using AI suggestion (high confidence)")
                else:
                    # Ask user if they want to use the suggestion
                    if suggestion.confidence == 'medium':
                        choice = prompt_user_choice(
                            "AI suggestion has medium confidence. What would you like to do?",
                            ["Use AI suggestion", "Enter metadata manually"]
                        )
                        if choice.startswith("Use"):
                            metadata = {
                                'collection': suggestion.collection,
                                'name': suggestion.name,
                                'keyword': suggestion.keyword,
                                'description': suggestion.description
                            }
                        else:
                            metadata = prompt_manual_metadata(content, collections)
                    else:
                        print("⚠️  AI suggestion has low confidence, prompting for manual input")
                        metadata = prompt_manual_metadata(content, collections)
            else:
                print("⚠️  AI analysis failed, prompting for manual input")
                metadata = prompt_manual_metadata(content, collections)
        else:
            # Manual metadata input
            metadata = prompt_manual_metadata(content, collections)
        
        # Create the snippet
        print(f"\n🚀 Creating snippet '{metadata['keyword']}'...")
        
        try:
            result = manager.create_snippet(
                content=content,
                name=metadata['name'],
                keyword=metadata['keyword'],
                collection=metadata['collection'],
                description=metadata['description'],
                use_ai=False,  # We already have metadata
                overwrite=args.overwrite
            )
            
            # Success notification
            success_msg = f"Snippet '{result['keyword']}' added to {result['collection']}"
            show_notification("Snippet Created", success_msg)
            
            print("✅ Success!")
            print(f"   Name: {result['name']}")
            print(f"   Keyword: {result['keyword']}")
            print(f"   Collection: {result['collection']}")
            print(f"   File: {result['file_path']}")
            
            if result['overwritten']:
                print("   ⚠️  Overwrote existing snippet")
            
            return 0
            
        except DuplicateSnippetError as e:
            error_msg = f"Duplicate keyword: {metadata['keyword']}"
            show_notification("Snippet Creation Failed", error_msg, sound=False)
            print(f"❌ {e}")
            print("   Use --overwrite to replace existing snippet")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        return 1
        
    except RuntimeError as e:
        show_notification("Snippet Creation Failed", str(e), sound=False)
        print(f"❌ {e}")
        return 1
        
    except ConfigurationError as e:
        show_notification("Configuration Error", str(e), sound=False)
        print(f"❌ Configuration error: {e}")
        print("   Make sure ALFRED_SNIPPETS_PATH and ANTHROPIC_API_KEY are set")
        return 1
        
    except ValidationError as e:
        show_notification("Validation Error", str(e), sound=False)
        print(f"❌ {e}")
        return 1
        
    except SnippetError as e:
        show_notification("Snippet Creation Failed", str(e), sound=False)
        print(f"❌ {e}")
        return 1
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        show_notification("Snippet Creation Failed", error_msg, sound=False)
        print(f"❌ {error_msg}")
        return 1


if __name__ == '__main__':
    sys.exit(main())