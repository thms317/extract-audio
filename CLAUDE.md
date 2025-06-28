# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an audio extraction tool with two main components:
- **Spotify Music Downloader**: Downloads music from Spotify URLs using the Zotify library
- **Wayback Machine Audio Scraper**: Extracts MP3 files from archived websites

## Common Development Commands

```bash
# Setup (install tools, create venv, setup pre-commit)
make setup

# Run tests with coverage
make test

# Lint and type check (runs ruff, mypy, pydoclint, bandit)
make lint

# Clean project artifacts
make clean

# Generate documentation
make docs

# Show project structure
make tree
```

## Key Dependencies and Tools

- **Python**: 3.12+ (managed with uv)
- **Package Manager**: uv (not pip)
- **External Dependencies**: ffmpeg required for audio conversion
- **Zotify**: Custom fork from `https://github.com/bgeorgakas/zotify.git`

## Architecture

```
src/extractor/
├── spotify.py     # Spotify downloading with progress tracking
├── scrape.py      # Wayback Machine audio extraction
├── convert.py     # OGG to MP3 conversion utilities
└── main.py        # Entry point
```

- Audio files downloaded to `extracted/` directory
- Supports both direct MP3 download and OGG→MP3 conversion
- Built-in rate limiting and retry logic for downloads

## Code Quality Standards

- **Linting**: Ruff with strict settings (100 char line length)
- **Type Checking**: mypy with strict mode
- **Security**: bandit security scanning
- **Docstrings**: NumPy style convention
- **Testing**: pytest with coverage reporting

## Testing

- Test files in `tests/` directory
- Run single test: `uv run pytest tests/test_specific.py -v`
- Pytest configuration in `pyproject.toml` sets pythonpath to `["src"]`

## Entry Point

Main script accessible via: `uv run python -m extractor.main`
