# Alfred Snippets Automation

An intelligent automation system for creating and managing Alfred snippets using Anthropic's Claude API for metadata generation and categorization.

## Overview

This project provides two main capabilities:
1. **Batch creation** of Alfred snippets from a JSON file (for initial setup)
2. **Ad hoc snippet creation** via Raycast Quicklink with intelligent categorization

The system leverages Claude AI to analyze snippet content and automatically suggest appropriate collections (folders), names, descriptions, and keywords based on content analysis.

## Architecture

### Core Components

- **`batch_create_alfred_snippets.py`**: Batch processes snippets from JSON input
- **`add_alfred_snippet.py`**: Creates individual snippets with AI-powered categorization
- **`snippet_manager.py`**: Core business logic for snippet operations
- **`claude_api.py`**: Anthropic API integration for content analysis
- **`alfred_utils.py`**: Alfred-specific file format and folder operations

### Design Choices

#### AI-Powered Categorization
The system uses Claude 3.5 Haiku for fast, cost-effective content analysis to:
- Suggest appropriate collection names based on snippet content
- Generate descriptive names following naming conventions
- Create meaningful keywords with topic prefixes
- Provide concise descriptions

#### Naming Conventions
- **Snippet Name**: Title Case, descriptive (e.g., "Git: Pretty Log")
- **Keyword**: Lowercase, topic prefix + function (e.g., "git_log5")
- **Collection**: Title Case by topic (e.g., "Git", "Dataview", "Terminal")
- **Filename**: Keyword + UID (e.g., "git_log5_ABC123.json")

#### Fallback Strategy
If AI categorization fails or confidence is low:
- Present existing collections for manual selection
- Allow creation of new collections
- Prompt for manual metadata input

## Setup

### Prerequisites

- Python 3.8+
- Alfred 5 with Snippets feature
- Anthropic API key
- macOS (for native notifications)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/snippets-automation.git
cd snippets-automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export ALFRED_SNIPPETS_PATH="/Users/shayon/Documents/~App Settings [on iCloud]/Alfred.alfredpreferences/snippets"
```

## Usage

### Batch Creation

Create snippets from a JSON file:

```bash
python batch_create_alfred_snippets.py input_snippets.json
```

#### JSON Schema Example

```json
{
  "snippets": [
    {
      "content": "git log --oneline --graph --decorate --all -n 10",
      "suggested_name": "Git: Pretty Log",
      "suggested_keyword": "git_log5",
      "suggested_collection": "Git",
      "description": "Display last 10 commits in a pretty format"
    },
    {
      "content": "TABLE without ID\nFROM #project\nWHERE status = \"active\"\nSORT priority DESC",
      "suggested_name": "Dataview: Active Projects",
      "suggested_keyword": "dv_projects_active"
    }
  ]
}
```

### Ad Hoc Creation

#### From Clipboard
```bash
python add_alfred_snippet.py
```

#### From Parameter (Raycast Integration)
```bash
python add_alfred_snippet.py "your snippet content here"
```

### Raycast Quicklink Setup

Create a Raycast Quicklink with:
- **Name**: Add Alfred Snippet
- **Link**: `file:///path/to/add_alfred_snippet.py?arguments={Query}`
- **Title**: Add Alfred Snippet
- **Description**: Create a new Alfred snippet with AI categorization

## Alfred Integration

### Snippet Format

Alfred snippets use JSON format with the following structure:

```json
{
  "alfredsnippet": {
    "snippet": "snippet content here",
    "name": "Snippet Name",
    "keyword": "snippet_keyword",
    "uid": "unique-identifier"
  }
}
```

### Collection Management

Collections are represented as folders in the Alfred snippets directory. The system:
- Automatically detects existing collections
- Creates new collections when suggested by AI
- Maintains proper folder structure for Alfred compatibility

## Error Handling

The system includes robust error handling for:
- API failures with retry logic
- File I/O operations
- Duplicate snippet detection
- Invalid Alfred snippets folder structure
- Network connectivity issues

## Security

- API keys are read from environment variables only
- No credentials are stored in code or logs
- Snippet content is analyzed but not stored by the API service

## Future Extensibility

The modular design supports future enhancements:
- Additional snippet sources (web clipping, IDE integration)
- Multiple sync targets (other snippet managers)
- Advanced categorization rules
- Snippet templates and automation
- Integration with other productivity tools

## Contributing

1. Create feature branches from `main`
2. Follow PEP 8 style guidelines
3. Include tests for new functionality
4. Update documentation as needed
5. Reference GitHub issues in commit messages

## License

MIT License - see LICENSE file for details