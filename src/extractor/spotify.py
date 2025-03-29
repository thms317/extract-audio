"""Spotify Music Downloader Module.

This module provides functionality to download music from Spotify and convert to MP3 format.
It can be used both as a command-line tool and as a module within other Python scripts.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


def setup_credentials(credentials_path: str | None = None) -> str:
    """Set up Spotify credentials for Zotify.

    Args:
        credentials_path: Optional path to existing credentials.json file.
            If provided, will use this file instead of generating new credentials.

    Returns
    -------
        str: Path to the credentials.json file
    """
    if credentials_path and os.path.exists(credentials_path):
        print(f"Using existing credentials from: {credentials_path}")
        return credentials_path

    # Determine platform-specific default credentials location
    if sys.platform == "darwin":  # macOS
        default_creds_dir = os.path.expanduser("~/Library/Application Support/Zotify")
    elif sys.platform == "win32":  # Windows
        default_creds_dir = os.path.join(os.environ.get("APPDATA", ""), "Zotify")
    else:  # Linux and others
        default_creds_dir = os.path.expanduser("~/.config/Zotify")

    default_creds_path = os.path.join(default_creds_dir, "credentials.json")

    # Check if credentials already exist
    if os.path.exists(default_creds_path):
        print(f"Using existing credentials from: {default_creds_path}")
        return default_creds_path

    # Create credentials directory if it doesn't exist
    os.makedirs(default_creds_dir, exist_ok=True)

    # Try to use librespot-auth to generate credentials
    try:
        print("No credentials found. Running librespot-auth to generate credentials...")
        subprocess.run(
            [sys.executable, "-m", "librespot_auth"],
            check=True,
        )

        # Check if credentials were created in current directory
        if os.path.exists("credentials.json"):
            # Move to default location
            os.rename("credentials.json", default_creds_path)
            print(f"Credentials created and moved to: {default_creds_path}")
            return default_creds_path
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"Error generating credentials: {e}")
        print(
            "Please install librespot-auth or manually create credentials as described in the docs."
        )
        sys.exit(1)

    return default_creds_path


def get_default_download_dir() -> str:
    """Get Zotify's default download directory based on the platform.

    Returns
    -------
        str: Path to the default download directory
    """
    if sys.platform == "darwin" or sys.platform.startswith("linux"):  # macOS or Linux
        download_dir = os.path.expanduser("~/Music/Zotify Music")
    else:  # Windows
        download_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Music", "Zotify Music")

    return download_dir


def modify_zotify_config(output_dir: str) -> bool:
    """Modify Zotify's config.json to use specified output directory.

    Args:
        output_dir: Directory to save downloaded files

    Returns
    -------
        bool: True if successful, False otherwise
    """
    try:
        # Determine config file location
        if sys.platform == "darwin":  # macOS
            config_dir = os.path.expanduser("~/Library/Application Support/Zotify")
        elif sys.platform == "win32":  # Windows
            config_dir = os.path.join(os.environ.get("APPDATA", ""), "Zotify")
        else:  # Linux and others
            config_dir = os.path.expanduser("~/.config/Zotify")

        config_path = os.path.join(config_dir, "config.json")

        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)

        # Load existing config or create new one
        config = {}
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)

        # Update download directory
        config["downloadDirectory"] = output_dir

        # Save updated config
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return True
    except Exception as e:
        print(f"Warning: Could not modify Zotify config: {e}")
        return False


def detect_content_type(url: str) -> str:
    """Detect if the Spotify URL is for a track, album, or playlist.

    Args:
        url: Spotify URL

    Returns
    -------
        str: Content type ('track', 'album', 'playlist', or 'unknown')
    """
    pattern = r"https://open\.spotify\.com/(track|album|playlist)/[a-zA-Z0-9]+"
    match = re.match(pattern, url)

    if match:
        return match.group(1)

    return "unknown"


def download_from_spotify(
    urls: list[str],
    output_dir: str | None = None,
    credentials_path: str | None = None,
    bulk_wait_time: int = 30,
    convert_to_mp3: bool = True,
    skip_existing: bool = True,
    quality: str = "320",
) -> list[str]:
    """Download songs, albums or playlists from Spotify using Zotify.

    Args:
        urls: List of Spotify URLs (track, album, or playlist)
        output_dir: Directory to save downloaded files (uses Zotify default if None)
        credentials_path: Path to Spotify credentials.json file
        bulk_wait_time: Wait time between downloads to avoid rate limits
        convert_to_mp3: Whether to convert downloaded .ogg files to MP3
        skip_existing: Skip downloading if file already exists
        quality: Audio quality (320, 160, or 96 kbps)

    Returns
    -------
        List[str]: Paths to downloaded files
    """
    # Validate URLs
    for url in urls:
        if not url.startswith("https://open.spotify.com/"):
            raise ValueError(f"Invalid Spotify URL: {url}")

    # Detect content type (track, album, playlist)
    content_type = detect_content_type(urls[0])
    print(f"Content type: {content_type}")
    print(f"Downloading from: {urls[0]}")

    # Get default directory before potential modification
    default_dir = get_default_download_dir()

    # Set up target directory
    target_dir = output_dir if output_dir else default_dir
    print(f"Target directory: {target_dir}")

    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

        # Important: Modify Zotify config to use the target directory
        # This is more reliable than command-line arguments
        if output_dir:
            modify_zotify_config(os.path.abspath(target_dir))

    # Get existing files before download
    existing_files = set()
    if os.path.exists(target_dir):
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith((".ogg", ".mp3")):
                    existing_files.add(os.path.join(root, file))

    print(f"Found {len(existing_files)} existing audio files before download")

    # Set up credentials
    creds_path = setup_credentials(credentials_path)

    # Create temp file with URLs if there are multiple
    downloads_file = None
    cmd = ["zotify"]

    if len(urls) > 1:
        temp_file = "spotify_links.txt"
        with open(temp_file, "w") as f:
            f.write("\n".join(urls))
        cmd.extend(["-d", temp_file])
        downloads_file = temp_file
    else:
        cmd.append(urls[0])

    # Add options
    if creds_path:
        cmd.extend(["--credentials-location", creds_path])

    if bulk_wait_time:
        cmd.extend(["--bulk-wait-time", str(bulk_wait_time)])

    # Note: We're setting the directory through the config now,
    # but we'll also pass it on the command line for redundancy
    if output_dir:
        cmd.extend(["--download-dir", os.path.abspath(target_dir)])

    if skip_existing:
        cmd.append("--skip-existing")

    if quality:
        cmd.extend(["--bitrate", quality])

    # Run Zotify
    try:
        subprocess.run(cmd, check=True)
        print("Download completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error during download: {e}")
        raise
    finally:
        # Clean up temp file if created
        if downloads_file and os.path.exists(downloads_file):
            os.remove(downloads_file)

    # Find newly downloaded files
    new_files = []
    if os.path.exists(target_dir):
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".ogg"):
                    full_path = os.path.join(root, file)
                    if full_path not in existing_files:
                        new_files.append(full_path)

    print(f"Downloaded {len(new_files)} new files:")
    for file in new_files:
        print(f"- {os.path.basename(file)}")

    # Convert to MP3 if requested
    if convert_to_mp3 and new_files:
        convert_ogg_to_mp3(new_files)

    return new_files


def convert_ogg_to_mp3(ogg_files: list[str], quality: str = "2") -> list[str]:
    """Convert .ogg files to MP3 format using ffmpeg.

    Args:
        ogg_files: List of .ogg file paths to convert
        quality: FFmpeg quality setting (lower is better, 2 is good quality)

    Returns
    -------
        List[str]: Paths to the created MP3 files
    """
    if not ogg_files:
        print("No OGG files found to convert.")
        return []

    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Warning: ffmpeg not found, cannot convert to MP3")
        return []

    print("Converting OGG files to MP3...")
    mp3_files = []
    total = len(ogg_files)

    for i, ogg_file in enumerate(ogg_files, 1):
        mp3_file = ogg_file.replace(".ogg", ".mp3")

        print(f"[{i}/{total}] Converting: {os.path.basename(ogg_file)}")

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    ogg_file,
                    "-codec:a",
                    "libmp3lame",
                    "-q:a",
                    quality,
                    mp3_file,
                    "-loglevel",
                    "warning",
                    "-y",  # Overwrite existing files
                ],
                check=True,
                capture_output=True,
            )
            mp3_files.append(mp3_file)

            # Optionally delete the original .ogg file
            # os.remove(ogg_file)

        except subprocess.CalledProcessError as e:
            print(f"Error converting {ogg_file}: {e}")
            print(
                f"FFmpeg stderr: {e.stderr.decode() if hasattr(e, 'stderr') else 'No error output'}"
            )

    print(f"Conversion complete: {len(mp3_files)}/{total} files converted to MP3")
    return mp3_files


def find_unconverted_ogg_files(directory: str) -> list[str]:
    """Find OGG files without corresponding MP3 versions.

    Args:
        directory: Directory to search for OGG files

    Returns
    -------
        List[str]: Paths to OGG files without MP3 versions
    """
    if not os.path.exists(directory):
        return []

    unconverted = []

    for root, _, files in os.walk(directory):
        ogg_files = {f for f in files if f.endswith(".ogg")}
        mp3_files = {f.replace(".mp3", ".ogg") for f in files if f.endswith(".mp3")}

        # Find OGG files without corresponding MP3 files
        need_conversion = ogg_files - mp3_files

        for file in need_conversion:
            unconverted.append(os.path.join(root, file))

    return unconverted


def download_from_file(
    file_path: str,
    output_dir: str | None = None,
    credentials_path: str | None = None,
    bulk_wait_time: int = 30,
    convert_to_mp3: bool = True,
    skip_existing: bool = True,
    quality: str = "320",
) -> list[str]:
    """Download Spotify URLs from a text file (one URL per line).

    Args:
        file_path: Path to text file containing Spotify URLs (one per line)
        output_dir: Directory to save downloaded files
        credentials_path: Path to Spotify credentials file
        bulk_wait_time: Wait time between downloads to avoid rate limits
        convert_to_mp3: Whether to convert downloaded .ogg files to MP3
        skip_existing: Skip downloading if file already exists
        quality: Audio quality (320, 160, or 96 kbps)

    Returns
    -------
        List[str]: Paths to downloaded files
    """
    with open(file_path) as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(urls)} URLs from {file_path}")

    return download_from_spotify(
        urls=urls,
        output_dir=output_dir,
        credentials_path=credentials_path,
        bulk_wait_time=bulk_wait_time,
        convert_to_mp3=convert_to_mp3,
        skip_existing=skip_existing,
        quality=quality,
    )


def main() -> None:
    """Entry point for the Spotify downloader when run as a script."""
    parser = argparse.ArgumentParser(
        description="Download music from Spotify and convert to MP3",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Main arguments
    parser.add_argument(
        "url",
        nargs="?",
        help="Spotify URL (track, album, or playlist)",
    )

    parser.add_argument(
        "-f",
        "--file",
        help="File containing Spotify URLs (one per line)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        help="Directory to save downloaded files",
    )

    # For compatibility with old script which used -t/--target
    parser.add_argument(
        "-t",
        "--target",
        dest="target_dir",
        help="Directory to save downloaded files (same as --output-dir)",
    )

    parser.add_argument(
        "-c",
        "--credentials",
        help="Path to Spotify credentials.json file",
    )

    parser.add_argument(
        "-w",
        "--wait-time",
        type=int,
        default=30,
        help="Wait time between downloads to avoid rate limits",
    )

    parser.add_argument(
        "-q",
        "--quality",
        choices=["320", "160", "96"],
        default="320",
        help="Audio quality (kbps)",
    )

    parser.add_argument(
        "--no-convert",
        action="store_true",
        help="Don't convert downloaded files to MP3 (keep as OGG)",
    )

    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Don't skip existing files (redownload)",
    )

    parser.add_argument(
        "--convert-existing",
        action="store_true",
        help="Convert all existing OGG files to MP3, not just newly downloaded ones",
    )

    args = parser.parse_args()

    # Determine output directory (supporting both old -t and new -o options)
    output_dir = args.output_dir or args.target_dir

    # Validate inputs
    if not args.url and not args.file and not (args.convert_existing and output_dir):
        parser.error(
            "Either a URL, a file with URLs, or --convert-existing with -o/--output-dir must be provided"
        )

    if args.url and args.file:
        parser.error("Please provide either a URL or a file with URLs, not both")

    try:
        # Process convert-existing command if specified
        if args.convert_existing and output_dir:
            print(f"Looking for unconverted OGG files in {output_dir}...")
            ogg_files = find_unconverted_ogg_files(output_dir)

            if ogg_files:
                print(f"Found {len(ogg_files)} unconverted OGG files")
                convert_ogg_to_mp3(ogg_files)
            else:
                print("No unconverted OGG files found!")

            if not args.url and not args.file:
                return

        # Download files
        if args.file:
            download_from_file(
                file_path=args.file,
                output_dir=output_dir,
                credentials_path=args.credentials,
                bulk_wait_time=args.wait_time,
                convert_to_mp3=not args.no_convert,
                skip_existing=not args.no_skip,
                quality=args.quality,
            )
        elif args.url:
            download_from_spotify(
                urls=[args.url],
                output_dir=output_dir,
                credentials_path=args.credentials,
                bulk_wait_time=args.wait_time,
                convert_to_mp3=not args.no_convert,
                skip_existing=not args.no_skip,
                quality=args.quality,
            )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
