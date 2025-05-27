# Raycast Integration Setup

This guide explains how to set up Raycast Quicklinks for seamless Alfred snippet creation.

## Prerequisites

1. [Raycast](https://raycast.com/) installed
2. Alfred Snippets Automation scripts configured
3. Environment variables set (`ALFRED_SNIPPETS_PATH`, `ANTHROPIC_API_KEY`)

## Setup Instructions

### 1. Create Raycast Quicklink

1. Open Raycast preferences (`Cmd + ,`)
2. Go to **Extensions** → **Quicklinks**
3. Click **Create Quicklink**

### 2. Quicklink Configuration

**Name:** `Add Alfred Snippet`

**Link:** 
```
file:///Users/shayon/DevProjects/snippets-automation/scripts/add_alfred_snippet.py?arguments={Query}
```

**Title:** `Add Alfred Snippet`

**Description:** `Create a new Alfred snippet with AI categorization`

**Icon:** Choose a snippet or text-related icon

### 3. Alternative Configurations

#### For Clipboard Content Only
If you prefer to always use clipboard content:

**Link:** 
```
file:///Users/shayon/DevProjects/snippets-automation/scripts/add_alfred_snippet.py
```

Remove the `?arguments={Query}` part to always use clipboard content.

#### With Additional Options
For power users who want more control:

**Link:** 
```
file:///Users/shayon/DevProjects/snippets-automation/scripts/add_alfred_snippet.py?arguments={Query}&flags=--verbose
```

This enables verbose output for debugging.

## Usage

### Method 1: With Content Parameter
1. Open Raycast (`Cmd + Space`)
2. Type "Add Alfred Snippet"
3. Press `Tab` and enter your snippet content
4. Press `Enter`

### Method 2: From Clipboard
1. Copy the content you want to create a snippet from
2. Open Raycast (`Cmd + Space`)
3. Type "Add Alfred Snippet" and press `Enter`

## Advanced Options

### Script Arguments

You can modify the Quicklink URL to include additional arguments:

- `--no-ai`: Disable AI categorization
- `--overwrite`: Allow overwriting existing snippets
- `--verbose`: Enable verbose output

Example:
```
file:///path/to/add_alfred_snippet.py?arguments={Query}&flags=--no-ai --overwrite
```

### Custom Workflows

For more advanced workflows, you can create multiple Quicklinks:

1. **Quick Add (High Confidence)**: Uses AI with high confidence threshold
2. **Manual Add**: Always prompts for manual metadata
3. **Overwrite Mode**: Always allows overwriting existing snippets

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure the script is executable: `chmod +x add_alfred_snippet.py`
   - Check file paths in the Quicklink URL

2. **Environment Variables Not Found**
   - Set variables in your shell profile (`.zshrc`, `.bash_profile`)
   - Restart Raycast after setting variables

3. **API Connection Failed**
   - Verify `ANTHROPIC_API_KEY` is correct
   - Check internet connection
   - Script will fall back to manual mode if API fails

### Testing the Setup

Run the script manually to test:

```bash
cd /path/to/snippets-automation
python scripts/add_alfred_snippet.py "echo 'test snippet'"
```

### Logs and Debugging

Enable verbose mode for troubleshooting:

```bash
python scripts/add_alfred_snippet.py "test content" --verbose
```

## Tips

1. **Copy Before Creating**: Copy your snippet content to clipboard before using Raycast for faster workflow
2. **Use Descriptive Content**: Better content leads to better AI categorization
3. **Review Suggestions**: Always review AI suggestions, especially for medium/low confidence
4. **Organize Collections**: Use consistent collection names for better organization