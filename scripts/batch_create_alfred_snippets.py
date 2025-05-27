#!/usr/bin/env python3
"""
Batch creation script for Alfred snippets from JSON input files.

Usage:
    python batch_create_alfred_snippets.py input_snippets.json [--no-ai] [--overwrite] [--stop-on-error]
"""

import argparse
import json
import sys
from pathlib import Path
import logging

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from snippet_manager import SnippetManager
from exceptions import SnippetError, ConfigurationError


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_snippets_file(file_path: str) -> dict:
    """
    Load and validate snippets from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If file format is invalid
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Snippets file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e}", e.doc, e.pos)
    
    # Validate file structure
    if not isinstance(data, dict):
        raise ValueError("JSON file must contain an object at root level")
    
    if 'snippets' not in data:
        raise ValueError("JSON file must contain a 'snippets' array")
    
    if not isinstance(data['snippets'], list):
        raise ValueError("'snippets' must be an array")
    
    if not data['snippets']:
        raise ValueError("Snippets array cannot be empty")
    
    return data


def validate_snippet_schema(snippet: dict, index: int) -> None:
    """
    Validate individual snippet schema.
    
    Args:
        snippet: Snippet dictionary
        index: Index in array for error reporting
        
    Raises:
        ValueError: If snippet is invalid
    """
    if not isinstance(snippet, dict):
        raise ValueError(f"Snippet {index + 1}: Must be an object")
    
    if 'content' not in snippet:
        raise ValueError(f"Snippet {index + 1}: Missing required 'content' field")
    
    if not snippet['content'] or not str(snippet['content']).strip():
        raise ValueError(f"Snippet {index + 1}: 'content' cannot be empty")
    
    # Optional fields validation
    optional_fields = ['name', 'keyword', 'collection', 'description']
    for field in optional_fields:
        if field in snippet and not isinstance(snippet[field], str):
            raise ValueError(f"Snippet {index + 1}: '{field}' must be a string")


def print_results_summary(results: dict) -> None:
    """Print a summary of batch processing results."""
    print(f"\n{'='*60}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total snippets: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    
    if results['successful'] > 0:
        print(f"\n✅ Successfully created {results['successful']} snippets:")
        for snippet in results['created_snippets']:
            ai_indicator = " (AI)" if snippet['ai_suggested'] else ""
            overwrite_indicator = " (OVERWRITTEN)" if snippet['overwritten'] else ""
            print(f"  • {snippet['keyword']} → {snippet['collection']}/{snippet['name']}{ai_indicator}{overwrite_indicator}")
    
    if results['failed'] > 0:
        print(f"\n❌ Failed to create {results['failed']} snippets:")
        for error in results['errors']:
            print(f"  • Snippet {error['index']}: {error['error']}")
            print(f"    Content: {error['content_preview']}")
    
    print(f"\n{'='*60}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Create Alfred snippets from JSON file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_create_alfred_snippets.py snippets.json
  python batch_create_alfred_snippets.py snippets.json --no-ai --overwrite
  python batch_create_alfred_snippets.py snippets.json --stop-on-error --verbose

JSON File Format:
{
  "snippets": [
    {
      "content": "git log --oneline --graph --decorate --all -n 10",
      "name": "Git: Pretty Log",
      "keyword": "git_log5",
      "collection": "Git",
      "description": "Display last 10 commits in a pretty format"
    },
    {
      "content": "echo 'Hello World'",
      "suggested_collection": "Terminal"
    }
  ]
}
        """
    )
    
    parser.add_argument(
        'file',
        help='Path to JSON file containing snippets'
    )
    
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Disable AI categorization (requires all metadata in JSON)'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing snippets with same keywords'
    )
    
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Stop processing on first error instead of continuing'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Load and validate input file
        logger.info(f"Loading snippets from: {args.file}")
        data = load_snippets_file(args.file)
        
        snippets = data['snippets']
        logger.info(f"Found {len(snippets)} snippets to process")
        
        # Validate snippet schemas
        for i, snippet in enumerate(snippets):
            validate_snippet_schema(snippet, i)
        
        # Initialize snippet manager
        logger.info("Initializing snippet manager...")
        manager = SnippetManager()
        
        # Validate setup
        validation = manager.validate_setup()
        if not validation['alfred_folder']:
            logger.error("Alfred folder validation failed")
            print("❌ Alfred snippets folder is not accessible")
            return 1
        
        if not args.no_ai and not validation['api_connection']:
            logger.warning("API connection failed, AI features disabled")
            print("⚠️  AI connection failed, proceeding without AI categorization")
            args.no_ai = True
        
        print(f"🚀 Processing {len(snippets)} snippets...")
        print(f"   AI categorization: {'disabled' if args.no_ai else 'enabled'}")
        print(f"   Overwrite existing: {'yes' if args.overwrite else 'no'}")
        print(f"   Stop on error: {'yes' if args.stop_on_error else 'no'}")
        
        # Process snippets
        results = manager.create_snippets_batch(
            snippets=snippets,
            use_ai=not args.no_ai,
            overwrite=args.overwrite,
            continue_on_error=not args.stop_on_error
        )
        
        # Print results
        print_results_summary(results)
        
        # Return appropriate exit code
        if results['failed'] > 0:
            return 1 if args.stop_on_error else 0
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        print(f"❌ {e}")
        return 1
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON error: {e}")
        print(f"❌ Invalid JSON format: {e}")
        return 1
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(f"❌ {e}")
        return 1
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"❌ Configuration error: {e}")
        print("   Make sure ALFRED_SNIPPETS_PATH and ANTHROPIC_API_KEY are set")
        return 1
        
    except SnippetError as e:
        logger.error(f"Snippet error: {e}")
        print(f"❌ {e}")
        return 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())