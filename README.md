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
git clone https://github.com/shayonpal/snippets-automation.git
cd snippets-automation
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Create `.env` file with your configuration:
```bash
cp .env.example .env
# Edit .env with your actual API key and Alfred snippets path
```

4. Make the run script executable:
```bash
chmod +x run.sh
```

5. Validate system setup:
```bash
./run.sh python3 -c "
import sys; sys.path.insert(0, 'src')
from snippet_manager import SnippetManager
manager = SnippetManager()
validation = manager.validate_setup()
print(f'Alfred folder: {validation[\"alfred_folder\"]}')
print(f'API connection: {validation[\"api_connection\"]}')
print(f'Collections: {validation[\"collections_count\"]}')
print(f'Existing snippets: {validation[\"snippets_count\"]}')
print('✅ Ready to use!' if not validation['errors'] else f'❌ Errors: {validation[\"errors\"]}')
"
```

## Usage

### Quick Start

**Create snippet from clipboard:**
```bash
./run.sh python3 scripts/add_alfred_snippet.py
# Or more simply:
./run.sh
```

**Create snippet with content:**
```bash
./run.sh python3 scripts/add_alfred_snippet.py "echo 'Hello World'"
# Or more simply:
./run.sh --add echo 'Hello World'
```

**Process starter snippets:**
```bash
./run.sh python3 scripts/batch_create_alfred_snippets.py docs/starter_snippets_wrapper.json
```

**Process example snippets:**
```bash
./run.sh python3 scripts/batch_create_alfred_snippets.py examples/sample_snippets.json
```

### Batch Creation

Create snippets from a JSON file:

```bash
./run.sh python3 scripts/batch_create_alfred_snippets.py input_snippets.json
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
./run.sh python3 scripts/add_alfred_snippet.py
```

#### From Parameter (Raycast Integration)
```bash
./run.sh python3 scripts/add_alfred_snippet.py "your snippet content here"
# Or more simply:
./run.sh --add your snippet content here
```

### Raycast Quicklink Setup

Create a Raycast Quicklink with:
- **Name**: Add Alfred Snippet
- **Link**: `file:///Users/shayon/DevProjects/snippets-automation/run.sh?arguments=--add {Query}`
- **Title**: Add Alfred Snippet
- **Description**: Create a new Alfred snippet with AI categorization

For detailed Raycast setup instructions, see `examples/raycast_setup.md`.

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

## Troubleshooting

### Common Issues

**Environment variables not found:**
```bash
# Make sure .env file exists and is properly formatted
cp .env.example .env
# Edit .env with your actual values
```

**Permission denied:**
```bash
chmod +x run.sh
```

**API connection failed:**
- Verify your `ANTHROPIC_API_KEY` is correct
- Check internet connectivity
- The system will fall back to manual input if API fails

**Alfred folder not accessible:**
- Verify the `ALFRED_SNIPPETS_PATH` in your `.env` file
- Ensure Alfred is installed and has created the snippets folder
- Check folder permissions

### Verbose Output

For debugging, add `--verbose` to any command:
```bash
./run.sh python3 scripts/add_alfred_snippet.py "test content" --verbose
```

## LLM-Assisted Snippet Generation

### Prompt for Auto-Generating Snippets

Use this prompt with any LLM to automatically generate snippet collections based on the example file format:

```
I need you to generate a JSON file containing Alfred snippets for [TOPIC/CATEGORY]. Please analyze the attached reference file to understand the structure and naming conventions.

Requirements:
- Generate 15-20 useful snippets for [TOPIC/CATEGORY]
- Follow the exact JSON structure from the reference file
- Use consistent naming conventions:
  - Collection: Title Case (e.g., "Git", "Docker", "Python")
  - Name: "Collection: Descriptive Name" format
  - Keyword: lowercase with topic prefix (e.g., "git_command", "docker_run")
  - Content: Practical, real-world commands/code
- Include both basic and advanced use cases
- Ensure keywords are unique and memorable
- Make descriptions concise but helpful

Please output ONLY the JSON in the expected format below.

### Expected JSON Output Format

{
  "snippets": [
    {
      "name": "Git: Interactive Rebase",
      "keyword": "git_rebase_interactive",
      "snippet": "git rebase -i HEAD~3",
      "collection": "Git"
    },
    {
      "name": "Docker: Run with Volume Mount",
      "keyword": "docker_run_volume",
      "snippet": "docker run -it --rm -v $(pwd):/workspace -w /workspace ubuntu:latest bash",
      "collection": "Docker"
    },
    {
      "name": "Python: List Comprehension with Filter",
      "keyword": "py_list_comp_filter",
      "snippet": "result = [x for x in items if condition(x)]",
      "collection": "Python"
    },
    {
      "name": "Terminal: Find Large Files",
      "keyword": "term_find_large",
      "snippet": "find . -type f -size +100M -exec ls -lh {} \\; | awk '{ print $9 \": \" $5 }'",
      "collection": "Terminal"
    },
    {
      "name": "SQL: Window Function Example",
      "keyword": "sql_window_func",
      "snippet": "SELECT id, name, salary, ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rank FROM employees;",
      "collection": "SQL"
    }
  ]
}
```

### Using Generated Snippets

1. **Generate with LLM**: Use the prompt above with your preferred LLM
2. **Save output**: Save the JSON to a file (e.g., `my_snippets.json`)
3. **Import**: Run the batch script:
   ```bash
   ./run.sh python3 scripts/batch_create_alfred_snippets.py my_snippets.json
   ```

### Reference Files

- `docs/starter_snippets_wrapper.json` - Example Tasks plugin snippets
- `examples/sample_snippets.json` - Mixed examples with various formats

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