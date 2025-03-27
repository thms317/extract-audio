# Spotify Music Downloader Guide

This guide provides step-by-step instructions for downloading music from Spotify using Zotify and converting the downloaded files to MP3 format.

## Prerequisites

- Python 3.12 or higher
- Git
- ffmpeg (for audio conversion)
- uv package manager (https://github.com/astral-sh/uv)

## Step 1: Setup Python Environment

First, create a dedicated Python virtual environment for Zotify:

```bash
# Create a new directory for the project
mkdir spotify-downloader
cd spotify-downloader

# Create a Python virtual environment using uv
uv venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

## Step 2: Generate Spotify Credentials

To download from Spotify, you need valid credentials. The easiest way is using librespot-auth:

```bash
# Clone the librespot-auth repository
git clone https://github.com/dspearson/librespot-auth.git
cd librespot-auth

# Install dependencies using uv
uv pip install -r requirements.txt

# Run the authentication script
python librespot_auth.py

# Follow the prompts:
# 1. Enter your Spotify username/email
# 2. Enter your password
# 3. The script will generate credentials.json
```

Save the generated `credentials.json` file to the Zotify configuration directory:
- macOS: `~/Library/Application Support/Zotify/credentials.json`
- Linux: `~/.config/Zotify/credentials.json`
- Windows: `%APPDATA%\Zotify\credentials.json`

```bash
# For macOS (create directory if it doesn't exist)
mkdir -p ~/Library/Application\ Support/Zotify/
cp credentials.json ~/Library/Application\ Support/Zotify/

# For Linux
# mkdir -p ~/.config/Zotify/
# cp credentials.json ~/.config/Zotify/

# For Windows (PowerShell)
# mkdir -p $env:APPDATA\Zotify
# cp credentials.json $env:APPDATA\Zotify\
```

## Step 3: Install and Configure Zotify

You can install Zotify using uv or use a forked version with additional features:

### Option 1: Standard Installation

```bash
# Return to your project directory
cd ..
uv pip install zotify
```

### Option 2: Install from the bgeorgakas Fork (Recommended)

This fork provides workarounds for rate limiting and audio key errors:

```bash
# Clone the forked repository
git clone https://github.com/bgeorgakas/zotify.git
cd zotify

# Install the package using uv
uv pip install -e .

# Return to your project directory
cd ..
```

## Step 4: Download Music from Spotify

You can download individual tracks, albums, or playlists:

```bash
# Activate your virtual environment if it's not already active
source .venv/bin/activate

# Download a single track
zotify https://open.spotify.com/track/TRACK_ID_HERE

# Download an album
zotify https://open.spotify.com/album/ALBUM_ID_HERE

# Download a playlist
zotify https://open.spotify.com/playlist/PLAYLIST_ID_HERE

# Download multiple links from a file (one URL per line)
# First create a file:
echo "https://open.spotify.com/track/TRACK_ID_1" > links.txt
echo "https://open.spotify.com/album/ALBUM_ID_1" >> links.txt

# Then download:
zotify -d links.txt
```

If you're using the bgeorgakas fork, add the `--bulk-wait-time` parameter to avoid rate limits:

```bash
zotify -d links.txt --credentials-location /path/to/credentials.json --bulk-wait-time 30
```

Downloaded files will be saved to:
- macOS: `~/Music/Zotify Music/[Artist]/[Album]/[Track].ogg`
- Linux: `~/Music/Zotify Music/[Artist]/[Album]/[Track].ogg`
- Windows: `%USERPROFILE%\Music\Zotify Music\[Artist]\[Album]\[Track].ogg`

## Step 5: Convert .ogg Files to MP3 Format

Zotify downloads songs in .ogg format. To convert them to MP3, use ffmpeg:

### Install ffmpeg

```bash
# On macOS (using Homebrew)
brew install ffmpeg

# On Ubuntu/Debian
# sudo apt update
# sudo apt install ffmpeg

# On Windows (using Chocolatey)
# choco install ffmpeg
```

### Convert Individual Files

```bash
# Basic conversion
ffmpeg -i input.ogg -codec:a libmp3lame -q:a 2 output.mp3
```

### Convert All Files in a Directory

Use the included conversion script:

```bash
# Run the script on your Zotify music directory
./convert_ogg_to_mp3.sh ~/Music/Zotify\ Music
```

The script will recursively process all directories and convert .ogg files to MP3 format.

## Quick Reference

To set up and download in one go:

```bash
# Create and activate environment
uv venv
source .venv/bin/activate

# Get credentials
git clone https://github.com/dspearson/librespot-auth.git
cd librespot-auth
uv pip install -r requirements.txt
python librespot_auth.py
mkdir -p ~/Library/Application\ Support/Zotify/
cp credentials.json ~/Library/Application\ Support/Zotify/
cd ..

# Install Zotify (fork version)
git clone https://github.com/bgeorgakas/zotify.git
cd zotify
uv pip install -e .
cd ..

# Download music
zotify https://open.spotify.com/track/YOUR_TRACK_ID --bulk-wait-time 30

# Install ffmpeg and convert files
brew install ffmpeg
cd ~/Music/Zotify\ Music
for f in $(find . -name "*.ogg"); do
    ffmpeg -i "$f" -codec:a libmp3lame -q:a 2 "${f%.ogg}.mp3"
done
```

## Troubleshooting

### Rate Limiting Issues

If you encounter "Audio key error" messages:
- Use the `--bulk-wait-time 30` parameter to add a delay between downloads
- Take a break for a few hours if you hit the rate limit
- Consider using a different Spotify account

### Authentication Issues

If authentication fails:
- Ensure you're using the correct Spotify credentials
- Try regenerating the credentials.json file
- Check that the credentials file is in the correct location

### Conversion Issues

If ffmpeg conversion fails:
- Make sure ffmpeg is properly installed: `ffmpeg -version`
- Check if the input file exists and is a valid .ogg file
- Ensure you have write permissions in the output directory
