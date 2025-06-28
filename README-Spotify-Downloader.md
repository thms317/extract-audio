# Spotify Music Downloader

A Python tool for downloading music from Spotify and converting it to MP3 format using Zotify. Supports tracks, albums, and playlists with intelligent file organization and conversion options.

## Quick Start

```bash
# Setup the project
make setup

# Download a track as MP3 (default)
python src/extractor/spotify.py "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh"

# Download an album with custom target directory
python src/extractor/spotify.py "https://open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3" -t ~/Downloads/Music

# Download a playlist with rate limiting
python src/extractor/spotify.py "https://open.spotify.com/playlist/37i9dQZEVXcQ9COmYvdajy" -w 45
```

## Prerequisites

### Required Software
- **Python 3.12+**
- **uv package manager** (installed via `make setup`)
- **ffmpeg** for audio conversion
- **Valid Spotify account**

### Install ffmpeg
```bash
# macOS (using Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg
```

## Setup Instructions

### 1. Project Setup
```bash
# Clone and setup the project
git clone <repository-url>
cd extract-audio
make setup
```

### 2. Spotify Credentials
Generate Spotify credentials using librespot-auth:

```bash
# Clone the authentication tool
git clone https://github.com/dspearson/librespot-auth.git
cd librespot-auth

# Install dependencies and generate credentials
uv pip install -r requirements.txt
python librespot_auth.py

# Follow the prompts to enter your Spotify username and password
# This will generate a credentials.json file
```

Copy the generated credentials to the correct location:
```bash
# macOS
mkdir -p ~/Library/Application\ Support/Zotify/
cp credentials.json ~/Library/Application\ Support/Zotify/

# Linux
mkdir -p ~/.config/Zotify/
cp credentials.json ~/.config/Zotify/

# Windows (PowerShell)
mkdir -p $env:APPDATA\Zotify
cp credentials.json $env:APPDATA\Zotify\
```

## Usage

### Basic Commands

```bash
# Activate the virtual environment (if not already active)
source .venv/bin/activate

# Download a single track
python src/extractor/spotify.py "https://open.spotify.com/track/TRACK_ID"

# Download an album
python src/extractor/spotify.py "https://open.spotify.com/album/ALBUM_ID"

# Download a playlist
python src/extractor/spotify.py "https://open.spotify.com/playlist/PLAYLIST_ID"
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `url` | Spotify URL (required unless using `--skip-download`) | - |
| `-t, --target` | Target directory for downloads | `extracted/noah_v2` |
| `-w, --wait-time` | Wait time between downloads (seconds) | 30 |
| `--skip-download` | Skip download, only convert existing files | False |
| `--keep-ogg` | Download as OGG, skip MP3 conversion | False |
| `--use-ogg` | Download as OGG first, then convert to MP3 | False |
| `--keep-library` | Keep files in Zotify's default location | False |
| `--flat-structure` | Save files without artist/album folders | False |
| `--remove-originals` | Remove OGG files after MP3 conversion | False |
| `--show-lyrics-errors` | Show lyrics-related error messages | False |

### Download Formats

**Direct MP3 (Default)**
```bash
python src/extractor/spotify.py "https://open.spotify.com/album/ALBUM_ID"
```
Downloads directly as MP3 using Zotify's built-in conversion.

**Two-Step Process (OGG → MP3)**
```bash
python src/extractor/spotify.py "https://open.spotify.com/album/ALBUM_ID" --use-ogg
```
Downloads as OGG first, then converts to MP3 for maximum compatibility.

**OGG Only**
```bash
python src/extractor/spotify.py "https://open.spotify.com/album/ALBUM_ID" --keep-ogg
```
Downloads as OGG format only, no MP3 conversion.

### File Organization

**Nested Structure (Default)**
```
extracted/noah_v2/
├── Artist Name/
│   ├── Album Name/
│   │   ├── 01 - Track Name.mp3
│   │   ├── 02 - Track Name.mp3
│   │   └── cover.jpg
│   └── Another Album/
└── Another Artist/
```

**Flat Structure**
```bash
python src/extractor/spotify.py "SPOTIFY_URL" --flat-structure
```
```
extracted/noah_v2/
├── Artist - Track Name.mp3
├── Artist - Another Track.mp3
├── Artist-cover.jpg
└── AnotherArtist-cover.jpg
```

## Practical Examples

### Download a Complete Album
```bash
# Download The Beatles - Abbey Road
python src/extractor/spotify.py "https://open.spotify.com/album/0ETFjACtuP2ADo6LFhL6HN" \
  -t ~/Music/Beatles \
  -w 45
```

### Download Multiple Playlists with Rate Limiting
```bash
# For large playlists, use longer wait times to avoid rate limits
python src/extractor/spotify.py "https://open.spotify.com/playlist/37i9dQZEVXcQ9COmYvdajy" \
  -w 60 \
  --flat-structure
```

### Convert Existing Files Only
```bash
# If you have OGG files that need conversion to MP3
python src/extractor/spotify.py "dummy_url" \
  --skip-download \
  -t ~/Music/ExistingFiles
```

### Create a Music Library
```bash
# Keep files in Zotify's location AND copy to target
python src/extractor/spotify.py "https://open.spotify.com/album/ALBUM_ID" \
  --keep-library \
  -t ~/Music/MyCollection
```

## Output and Progress

The tool provides real-time download progress:

```
Downloading from: https://open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3
Target directory: extracted/noah_v2
Found 0 existing files in target and 45 in Zotify's default location
Total tracks to download: 12

Starting Zotify download...
⏱️  Downloading in progress, will display real-time updates below:

[●] Preparing to download album: Abbey Road
[∙] Track 1/12: Come Together
████████████████████████████████████████ 100% | 3.2MB/3.2MB | 1.2MB/s
Download successful. Processing...

✅ Download successful! Found 12 new audio files in Zotify's default location.
📦 Copying files to target directory (flat structure): extracted/noah_v2
  ↳ Copied: Come Together.mp3
  ↳ Copied: Something.mp3
  ...
  ↳ Copied cover art: Abbey Road-cover.jpg

✨ Copied 12 audio files and 1 cover images to extracted/noah_v2 (flat structure)
```

## Rate Limiting and Best Practices

### Avoiding Rate Limits
- Use `--wait-time 45` or higher for large downloads
- Take breaks between large playlist downloads
- Avoid downloading too many items in quick succession

### Recommended Settings
```bash
# For albums (10-15 tracks)
-w 30

# For large playlists (50+ tracks)
-w 60

# For very large playlists (100+ tracks)
-w 90
```

## Troubleshooting

### Common Issues

**"Audio key error" or Rate Limiting**
```bash
# Increase wait time and try again
python src/extractor/spotify.py "SPOTIFY_URL" -w 90
```

**Authentication Errors**
```bash
# Regenerate credentials
cd librespot-auth
python librespot_auth.py
# Copy new credentials.json to Zotify directory
```

**ffmpeg Not Found**
```bash
# Install ffmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Linux
```

**No Files Downloaded**
- Check that the Spotify URL is valid and accessible
- Verify Zotify credentials are properly configured
- Ensure you have an active Spotify subscription

### Debug Information

Enable detailed output:
```bash
python src/extractor/spotify.py "SPOTIFY_URL" --show-lyrics-errors
```

## File Locations

### Default Directories
- **Zotify Default**: `~/Music/Zotify Music/`
- **Tool Default**: `extracted/noah_v2/`
- **Credentials**:
  - macOS: `~/Library/Application Support/Zotify/credentials.json`
  - Linux: `~/.config/Zotify/credentials.json`
  - Windows: `%APPDATA%\Zotify\credentials.json`

### Supported Formats
- **Input**: Spotify URLs (tracks, albums, playlists)
- **Output**: MP3 (default), OGG (optional)
- **Cover Art**: JPG, PNG

## Advanced Usage

### Batch Processing
```bash
# Create a script for multiple downloads
#!/bin/bash
albums=(
  "https://open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3"
  "https://open.spotify.com/album/6dVIqQ8qmQ58ufgt541SVh"
  "https://open.spotify.com/album/2PPc7mrWkAXwfhB3horOE7"
)

for album in "${albums[@]}"; do
  python src/extractor/spotify.py "$album" -w 90 -t ~/Music/Collection
  sleep 300  # 5-minute break between albums
done
```

### Integration with Other Tools
```bash
# Convert to other formats after download
find extracted/noah_v2 -name "*.mp3" -exec ffmpeg -i {} -c:a flac {}.flac \;

# Organize by year (requires additional metadata tools)
# Use tools like eyeD3 or mutagen for advanced metadata handling
```

This tool provides a robust solution for downloading and organizing music from Spotify while respecting rate limits and providing excellent user feedback throughout the process.
