# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cratedigger is an audio extraction and discovery tool with two main components:
- **Spotify Music Downloader**: Downloads music from Spotify URLs using the Zotify library
- **Wayback Machine Audio Scraper**: Extracts MP3 files from archived websites

## Common Development Commands

```bash
# Setup (install tools, create venv, setup pre-commit)
make setup

# Run tests with coverage
make test

# Lint and type check (runs ruff, mypy, pydoclint)
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
src/cratedigger/
├── spotify.py     # Spotify downloading with progress tracking
├── scrape.py      # Wayback Machine audio extraction
└── convert.py     # OGG to MP3 conversion utilities
```

- Audio files downloaded to `extracted/` directory
- Supports both direct MP3 download and OGG→MP3 conversion
- Built-in rate limiting and retry logic for downloads

## Code Quality Standards

- **Linting**: Ruff with strict settings (100 char line length)
- **Type Checking**: ty type checker (replaced mypy)
- **Docstrings**: NumPy style convention via pydoclint
- **Testing**: pytest with coverage reporting

## Testing

- Test files in `tests/` directory
- Run single test: `uv run pytest tests/test_specific.py -v`
- Pytest configuration in `pyproject.toml` sets pythonpath to `["src"]`

## Entry Points

- **Main entry point**: `uv run python -m cratedigger.main`
- **Console script**: `uv run main` (via pyproject.toml entry point)
- **Spotify downloader**: `uv run python src/cratedigger/spotify.py <url>`
- **Wayback scraper**: `uv run python src/cratedigger/scrape.py <url>`
- **OGG to MP3 converter**: `uv run python src/cratedigger/convert.py <directory>`

## Development Workflow

- Use `uv sync` to sync dependencies after changes
- Use `uv build` to build the package before testing
- Single test execution: `uv run pytest tests/test_specific.py::test_function_name -v`
- Pre-commit hooks are configured for code quality checks
