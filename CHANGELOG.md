# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-06-24 15:04:32 EDT

### Added
- GitHub Project 5 integration for automatic issue tracking (#443da6b)
- PopClip extension support for creating snippets from selected text (#11)
- `--add` flag to run.sh for simplified direct snippet creation (#12)
- Comprehensive LLM-assisted snippet generation documentation
- Virtual environment setup validation script
- Badges for GitHub Issues and MIT License in README

### Changed
- Improved virtual environment setup instructions in README
- Enhanced run.sh script with better argument handling for unquoted input
- Updated documentation to reflect three main capabilities (batch, ad hoc, PopClip)
- Restructured project configuration for better user experience

### Fixed
- Missing 'requests' module dependency issue (#13, #3778268)
- Merge conflicts in run.sh resolved (#b1079d2)
- Raycast integration working directory issue

### Security
- Moved project-specific instructions to CLAUDE.local.md (not tracked in git)

## [0.1.0] - 2025-05-27

### Added
- Initial implementation of Alfred Snippets Automation
- Core snippet manager module with business logic (#1)
- Claude API integration for AI-powered categorization (#2)
- Alfred utilities for file format and folder operations (#3)
- Batch creation script for processing JSON files (#4)
- Ad hoc snippet creation script with intelligent categorization (#5)
- Comprehensive error handling system
- User prompting and notification system
- Duplicate snippet detection
- API retry logic with exponential backoff
- Environment-based configuration management
- Comprehensive documentation and examples