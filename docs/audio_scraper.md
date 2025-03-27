# Wayback Machine Audio Scraper

This guide explains how to use `scrape_audio.py` to extract and download MP3 files from archived websites in the Wayback Machine.

## Overview

The Wayback Machine Audio Scraper is a tool that:

1. Extracts MP3 URLs from archived webpages in the Internet Archive's Wayback Machine
2. Constructs proper Wayback Machine URLs to access the actual audio files
3. Downloads the MP3 files with robust retry logic and progress tracking

The tool is especially useful for recovering audio content from websites that no longer exist or have changed, but were archived by the Internet Archive.

## Prerequisites

- Python 3.12 or higher
- Python libraries: `requests`, `beautifulsoup4` (bs4)

## Installation

```bash
# Install required dependencies
uv pip install requests beautifulsoup4
```

## Basic Usage

```bash
# Basic search for MP3s on an archived page (no download)
python -m extractor.scrape_audio "https://web.archive.org/web/20210418151905/https://example.com/page-with-audio.html"

# Download found MP3 files
python -m extractor.scrape_audio "https://web.archive.org/web/20210418151905/https://example.com/page-with-audio.html" --download
```

## Command-line Options

The script provides several command-line options to customize its behavior:

| Option | Short | Description |
|--------|-------|-------------|
| `--download` | `-d` | Download the MP3 files found on the page |
| `--output OUTPUT` | `-o` | Directory to save downloaded MP3s (default: `mp3_downloads`) |
| `--retries N` | `-r` | Maximum number of retry attempts per file (default: 3) |
| `--wait SECONDS` | `-w` | Wait time between downloads in seconds (default: 2.0) |
| `--force` | `-f` | Force download even if files already exist |

## Examples

### Example 1: List MP3 files without downloading

```bash
python -m extractor.scrape_audio "https://web.archive.org/web/20210418151905/https://www.hoorspelen.eu/producties/hsp-p/pluk-van-de-petteflet.html"
```

This will scan the archived page and list any MP3 URLs it finds, but won't download them.

### Example 2: Download all MP3s to a specific folder

```bash
python -m extractor.scrape_audio "https://web.archive.org/web/20210418151905/https://www.hoorspelen.eu/producties/hsp-p/pluk-van-de-petteflet.html" --download --output ./my_mp3s
```

This will download all found MP3 files to the `./my_mp3s` directory.

### Example 3: Increase wait time between downloads

```bash
python -m extractor.scrape_audio "https://web.archive.org/web/20210418151905/https://example.com/page-with-audio.html" --download --wait 5
```

This will wait 5 seconds between each download, which can help avoid triggering rate limits.

### Example 4: Force re-download of files

```bash
python -m extractor.scrape_audio "https://web.archive.org/web/20210418151905/https://example.com/page-with-audio.html" --download --force
```

This will download all files even if they already exist locally.

## How It Works

1. **URL Discovery**: The script scans the HTML of the archived page for three types of elements:
   - `<audio>` tags with MP3 sources
   - Direct `<audio src="...">` tags containing MP3 files
   - `<a href="...">` links ending with .mp3

2. **URL Construction**: For each found URL, the script ensures it's properly formatted for the Wayback Machine by:
   - Extracting the Wayback Machine timestamp from the original URL
   - Adding necessary prefixes and domains for relative URLs
   - Avoiding duplicate prefixes for already-formatted URLs

3. **Download Process**:
   - Creates the destination directory if it doesn't exist
   - Extracts filename from URL or uses a provided one
   - Implements retry logic with exponential backoff for failed downloads
   - Shows download progress for each file
   - Verifies downloaded files are not empty

## Troubleshooting

### No MP3 URLs Found

If the script doesn't find any MP3 URLs:
- Check if the page actually contains MP3 files
- Verify that the Wayback Machine timestamp in the URL is correct
- Some websites may use non-standard ways to embed audio that aren't detected

### Download Failures

If downloads are failing:
- Increase the number of retries with `--retries`
- Increase the wait time between downloads with `--wait`
- Check if the Wayback Machine is experiencing issues
- Some archived files might be incomplete or corrupted in the Wayback Machine

### URL Construction Issues

If the script finds URLs but they don't work when accessed:
- The URL construction might need adjustment for that specific website
- The archive might not have captured the audio files properly
- Try using a different Wayback Machine timestamp if available

## Advanced Usage

### Using as a Module

You can import the functions from the script to use in your own Python code:

```python
from extractor.scrape_audio import find_mp3_urls_from_archive, download_mp3

# Get MP3 URLs from an archived page
urls = find_mp3_urls_from_archive("https://web.archive.org/web/20210418151905/https://example.com/page.html")

# Download a specific MP3
success, filepath, error = download_mp3(
    urls[0],                  # URL to download
    "./downloads",            # Destination directory
    filename="my_audio.mp3",  # Custom filename
    max_retries=5,            # Max retry attempts
    force_download=True       # Overwrite existing file
)

if success:
    print(f"Downloaded to {filepath}")
else:
    print(f"Download failed: {error}")
```
