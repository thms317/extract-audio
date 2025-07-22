# Wayback Machine Audio Scraper

A Python tool for extracting and downloading MP3 files from archived websites on the Wayback Machine. This scraper intelligently finds audio files in web archives and downloads them with robust error handling and retry logic.

## Quick Start

```bash
# Setup the project
make setup

# Find MP3s on an archived webpage (discovery only)
python src/cratedigger/scrape.py "https://web.archive.org/web/20210418151905/https://example.com/audio-page"

# Find and download MP3s
python src/cratedigger/scrape.py "https://web.archive.org/web/20210418151905/https://example.com/audio-page" --download

# Download with custom settings
python src/cratedigger/scrape.py "WAYBACK_URL" -d -o ~/Downloads/Audio -r 5 -w 3.0
```

## How It Works

The scraper analyzes archived webpages on the Wayback Machine to find MP3 files by:

1. **Parsing HTML content** from the archived page
2. **Searching for audio elements**: `<audio>` tags, `<source>` elements, and `<a>` links
3. **Constructing proper Wayback URLs** for the discovered audio files
4. **Downloading files** with retry logic and progress tracking

## Prerequisites

- **Python 3.12+**
- **Internet connection** for accessing Wayback Machine
- **Basic knowledge** of Wayback Machine URLs

### Install Dependencies
```bash
# Project setup includes all dependencies
make setup

# Or install manually
uv pip install requests beautifulsoup4
```

## Usage

### Basic Commands

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Discover MP3s without downloading
python src/cratedigger/scrape.py "WAYBACK_MACHINE_URL"

# Download discovered MP3s
python src/cratedigger/scrape.py "WAYBACK_MACHINE_URL" --download

# Use custom output directory
python src/cratedigger/scrape.py "WAYBACK_MACHINE_URL" -d -o ~/Audio/Extracted
```

### Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `url` | - | Wayback Machine URL to scrape | Demo URL |
| `--download` | `-d` | Download found MP3 files | False (discovery only) |
| `--output` | `-o` | Output directory for downloads | `mp3_downloads` |
| `--retries` | `-r` | Max retry attempts per file | 3 |
| `--wait` | `-w` | Wait time between downloads (seconds) | 2.0 |
| `--force` | `-f` | Force download even if file exists | False |

## Understanding Wayback Machine URLs

### URL Format
```
https://web.archive.org/web/TIMESTAMP/ORIGINAL_URL
```

**Example:**
```
https://web.archive.org/web/20210418151905/https://www.example.com/audio-page.html
```

- **20210418151905**: Timestamp (April 18, 2021, 15:19:05)
- **Original URL**: The archived website

### Finding Archived Pages

1. **Visit** [web.archive.org](https://web.archive.org)
2. **Search** for the original website
3. **Select** a snapshot from the calendar
4. **Copy** the full Wayback Machine URL

## Practical Examples

### Discover Audio Files
```bash
# Check what MP3s are available on an archived music site
python src/cratedigger/scrape.py \
  "https://web.archive.org/web/20200615082341/https://www.example-music-site.com/downloads"
```

**Output:**
```
Found 8 potential MP3 URLs (adjusted for Wayback Machine):
https://web.archive.org/web/20200615082341im_/https://www.example-music-site.com/track1.mp3
https://web.archive.org/web/20200615082341im_/https://www.example-music-site.com/track2.mp3
...

Note:
These URLs have been constructed based on the Wayback Machine timestamp.
Please verify if they work correctly.
Use --download to save the MP3 files.
```

### Download Audio Files
```bash
# Download all found MP3s
python src/cratedigger/scrape.py \
  "https://web.archive.org/web/20200615082341/https://www.example-music-site.com/downloads" \
  --download \
  --output ~/Music/Archived
```

**Progress Output:**
```
Found 8 potential MP3 URLs (adjusted for Wayback Machine):
...

Downloading 8 MP3 files to: ~/Music/Archived

Downloading file 1/8
Downloading https://web.archive.org/web/20200615082341im_/https://www.example-music-site.com/track1.mp3 (attempt 1/3)
Progress: 100% (3245821/3245821 bytes)
✓ Saved to /Users/username/Music/Archived/track1.mp3
Waiting 2.45 seconds before next download...

Downloading file 2/8
...

Download complete: 7 successful, 1 failed
```

### Handle Rate Limiting
```bash
# For sites with strict rate limiting, increase wait time
python src/cratedigger/scrape.py "WAYBACK_URL" \
  -d \
  -w 5.0 \
  -r 5
```

### Force Re-download
```bash
# Re-download files even if they already exist
python src/cratedigger/scrape.py "WAYBACK_URL" \
  -d \
  --force
```

## Advanced Usage

### Batch Processing Multiple Archives
```bash
#!/bin/bash
# Create a script for multiple archive URLs

urls=(
  "https://web.archive.org/web/20200101120000/https://site1.com/audio"
  "https://web.archive.org/web/20200601120000/https://site2.com/music"
  "https://web.archive.org/web/20201201120000/https://site3.com/sounds"
)

for url in "${urls[@]}"; do
  echo "Processing: $url"
  python src/cratedigger/scrape.py "$url" -d -o "downloads/$(date +%Y%m%d_%H%M%S)" -w 3.0
  echo "Waiting 30 seconds before next site..."
  sleep 30
done
```

### Selective Discovery
```bash
# First discover what's available
python src/cratedigger/scrape.py "WAYBACK_URL" > discovered_files.txt

# Review the list, then download selectively
# (You could modify the script to accept a file list)
```

## How URLs Are Constructed

The scraper intelligently handles different URL formats found in archived pages:

### URL Types Detected

1. **Audio Tags with Sources**
   ```html
   <audio>
     <source src="/music/track.mp3" type="audio/mpeg">
   </audio>
   ```

2. **Direct Audio Tag Sources**
   ```html
   <audio src="https://example.com/audio.mp3" controls>
   ```

3. **Download Links**
   ```html
   <a href="/downloads/song.mp3">Download Song</a>
   ```

### URL Construction Logic

| Original URL Type | Example | Wayback URL Generated |
|-------------------|---------|----------------------|
| Relative path | `/audio/track.mp3` | `https://web.archive.org/web/TIMESTAMP/im_/DOMAIN/audio/track.mp3` |
| Absolute URL | `https://site.com/track.mp3` | `https://web.archive.org/web/TIMESTAMP/im_/https://site.com/track.mp3` |
| Already Wayback | `https://web.archive.org/web/...` | (Used as-is) |

### Wayback Machine Prefixes

- **`im_`**: Images and media files
- **`oe_`**: Original encoding (alternative for audio)

## Error Handling and Retry Logic

### Automatic Retries
- **Exponential backoff** with jitter
- **Multiple attempts** for failed downloads
- **Progress tracking** with resumption capability

### Common Issues and Solutions

**Network Timeouts**
```bash
# Increase retry attempts for unstable connections
python src/cratedigger/scrape.py "WAYBACK_URL" -d -r 10 -w 5.0
```

**Rate Limiting (429 errors)**
```bash
# Increase wait time between requests
python src/cratedigger/scrape.py "WAYBACK_URL" -d -w 10.0
```

**File Not Found (404 errors)**
- The archived page may not have preserved all audio files
- Try different timestamps of the same page
- Some files may have been excluded from archiving

## File Organization

### Default Structure
```
mp3_downloads/
├── track1.mp3
├── track2.mp3
├── background_music.mp3
└── podcast_episode.mp3
```

### Custom Organization
```bash
# Organize by date/site
python src/cratedigger/scrape.py "WAYBACK_URL" -d -o "downloads/$(date +%Y%m%d)/site_name"
```

## Best Practices

### Respectful Scraping
1. **Use reasonable wait times** (2+ seconds between downloads)
2. **Don't overwhelm** the Wayback Machine servers
3. **Limit concurrent requests** (use the built-in rate limiting)
4. **Take breaks** between large batch operations

### Successful Extraction Tips
1. **Choose recent archives** when possible (better preservation)
2. **Try multiple timestamps** for the same page
3. **Look for dedicated audio/download pages** rather than general pages
4. **Check file sizes** - very small files might be placeholders

### Legal Considerations
- **Verify copyright status** of downloaded content
- **Respect robots.txt** and terms of service
- **Use for archival/research purposes** when appropriate
- **Check original licensing** of the archived content

## Troubleshooting

### No MP3s Found
```bash
# Check if the page actually contains audio
# Look for <audio>, <source>, or <a> tags with .mp3 links in browser inspector
```

**Possible causes:**
- Page uses JavaScript to load audio (not captured in archives)
- Audio files use different formats (.wav, .ogg, .m4a)
- Content was loaded dynamically after page render

### Download Failures
```bash
# Enable verbose output for debugging
python src/cratedigger/scrape.py "WAYBACK_URL" -d -r 5 -w 5.0
```

**Common issues:**
- **404 Not Found**: File wasn't archived or URL construction failed
- **403 Forbidden**: Access restrictions on archived content
- **Timeout**: Server overloaded or slow connection

### Empty Files Downloaded
- Check if the Wayback Machine has the actual file content
- Try different URL prefixes (im_ vs oe_)
- Verify the original file was accessible when archived

## Using as a Python Module

You can import the functions to use in your own Python code:

```python
from cratedigger.scrape import find_mp3_urls_from_archive, download_mp3

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

## Output Examples

### Discovery Mode

```bash
$ python src/cratedigger/scrape.py "WAYBACK_URL"

Found 5 potential MP3 URLs (adjusted for Wayback Machine):
https://web.archive.org/web/20200615082341im_/https://example.com/audio1.mp3
https://web.archive.org/web/20200615082341im_/https://example.com/audio2.mp3
https://web.archive.org/web/20200615082341im_/https://example.com/music/song.mp3
https://web.archive.org/web/20200615082341oe_/https://example.com/podcast.mp3
https://web.archive.org/web/20200615082341im_/https://example.com/sounds/fx.mp3

Note:
These URLs have been constructed based on the Wayback Machine timestamp.
Please verify if they work correctly.
Use --download to save the MP3 files.
```

### Download Mode

```bash
$ python src/cratedigger/scrape.py "WAYBACK_URL" --download

Found 5 potential MP3 URLs (adjusted for Wayback Machine):
...

Downloading 5 MP3 files to: mp3_downloads

Downloading file 1/5
Downloading https://web.archive.org/web/20200615082341im_/https://example.com/audio1.mp3 (attempt 1/3)
Progress: 100% (2851432/2851432 bytes)
✓ Saved to mp3_downloads/audio1.mp3
Waiting 2.67 seconds before next download...

Downloading file 2/5
File already exists at mp3_downloads/audio2.mp3, skipping download.
✓ Saved to mp3_downloads/audio2.mp3

...

Download complete: 4 successful, 1 failed
```

This tool provides an effective way to rescue audio content from archived websites, preserving digital audio history with robust downloading capabilities.
