# Spotify Audio Extractor

A Python wrapper script for automating the Spotify music download and conversion process using Zotify.

## Prerequisites

- Python 3.12 or higher
- Zotify installed in a virtual environment
- ffmpeg installed on your system
- Valid Spotify credentials configured for Zotify

## Features

- Download tracks, albums, or playlists from Spotify URLs
- Check for existing files to avoid duplicate downloads
- Automatically convert downloaded .ogg files to MP3 format
- Simple command-line interface

## Usage

```bash
# Basic usage
python extract_audio.py https://open.spotify.com/album/ALBUM_ID

# Specify a custom target directory
python extract_audio.py https://open.spotify.com/track/TRACK_ID -t ~/Music/MySpotifyDownloads

# Set a custom wait time between downloads (to avoid rate limiting)
python extract_audio.py https://open.spotify.com/playlist/PLAYLIST_ID -w 60

# Only convert existing files (skip download)
python extract_audio.py https://open.spotify.com/album/ALBUM_ID --skip-download

# Only download files (skip conversion)
python extract_audio.py https://open.spotify.com/album/ALBUM_ID --skip-convert
```

## Command-line Options

- `url`: Required Spotify URL (track, album, or playlist)
- `-t, --target`: Target directory for downloads (default: ~/Music/Zotify Music)
- `-w, --wait-time`: Bulk wait time between downloads in seconds (default: 30)
- `--skip-download`: Skip download and only convert existing files
- `--skip-convert`: Skip conversion to MP3

## Examples

```bash
# Download an album and convert to MP3
python extract_audio.py https://open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3

# Download a playlist with a longer wait time between tracks
python extract_audio.py https://open.spotify.com/playlist/37i9dQZEVXcQ9COmYvdajy -w 45

# Only convert existing OGG files in a specific directory
python extract_audio.py https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6 -t ~/Music/Zotify\ Music --skip-download
```

## Notes

- This script requires Zotify to be properly installed and configured with valid Spotify credentials
- See the [Spotify Music Downloader Guide](docs/spotify_downloader.md) for detailed setup instructions
- MP3 conversion requires ffmpeg to be installed on your system


## More examples

```bash
python extract_audio.py https://open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3
python extract_audio.py https://open.spotify.com/playlist/37i9dQZEVXcQ9COmYvdajy -w 45
python extract_audio.py https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6 -t ~/Music/Zotify\ Music --skip-download
```
