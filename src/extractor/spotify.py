#!/usr/bin/env python3

"""Download and convert Spotify content."""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from tqdm import tqdm

DEFAULT_TARGET_DIR = "extracted/noah_v2"


def is_valid_spotify_url(url: str) -> bool:
    """Check if URL is a valid Spotify URL."""
    pattern = r"^https://open\.spotify\.com/(track|album|playlist)/[a-zA-Z0-9]{22}(\?.*)?$"
    return bool(re.match(pattern, url))


def get_spotify_content_type(url: str) -> str | None:
    """Extract content type (track, album, playlist) from Spotify URL."""
    if not is_valid_spotify_url(url):
        return None

    match = re.match(
        r"^https://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]{22})(\?.*)?$",
        url,
    )
    if match:
        return match.group(1)
    return None


# def configure_zotify(target_dir: str) -> bool:
#     """Configure Zotify to use the specified target directory."""
#     # Find Zotify config location
#     if platform.system() == "Windows":
#         config_dir = os.path.join(os.environ.get("APPDATA", ""), "Zotify")
#     else:
#         config_dir = os.path.expanduser("~/.config/zotify")

#     config_file = os.path.join(config_dir, "config.json")

#     # Check if config exists
#     if not os.path.exists(config_file):
#         try:
#             # Run zotify once to generate default config
#             subprocess.run(["zotify", "--help"], check=True, capture_output=True)
#         except subprocess.CalledProcessError as e:
#             print(f"Error initializing Zotify: {e}")
#             return False

#         if not os.path.exists(config_file):
#             print(f"Could not find or create Zotify config at {config_file}")
#             return False

#     # Now read and modify the config
#     try:
#         import json

#         with open(config_file) as f:
#             config = json.load(f)

#         # Update output directory
#         config["song_directory"] = target_dir
#         config["album_directory"] = target_dir
#         config["playlist_directory"] = target_dir

#         # Save updated config
#         with open(config_file, "w") as f:
#             json.dump(config, f, indent=4)

#         print(f"Zotify configured to use target directory: {target_dir}")
#         return True

#     except Exception as e:
#         print(f"Error updating Zotify config: {e}")
#         return False


def list_existing_files(
    directory: str,
    extensions: list[str] | None = None,
) -> list[str]:
    """List all audio files in the directory."""
    if extensions is None:
        extensions = [".ogg", ".mp3"]

    existing_files: list[str] = []
    for root, _, files in os.walk(directory):
        root_path = Path(root)
        existing_files.extend(
            str(root_path / file)
            for file in files
            if any(file.lower().endswith(ext) for ext in extensions)
        )

    return existing_files


def find_unconverted_files(directory: str) -> list[str]:
    """Find .ogg files that don't have a corresponding .mp3 file."""
    unconverted = []
    for root, _, files in os.walk(directory):
        ogg_files = [f for f in files if f.lower().endswith(".ogg")]
        for ogg_file in ogg_files:
            mp3_file = ogg_file[:-4] + ".mp3"
            ogg_path = Path(root) / ogg_file
            mp3_path = Path(root) / mp3_file
            if not mp3_path.exists():
                unconverted.append(str(ogg_path))

    return unconverted


def get_spotify_track_count(url: str) -> int | None:
    """Estimate the number of tracks in the Spotify URL."""
    try:
        content_type = get_spotify_content_type(url)
        if not content_type:
            return None

        # Use zotify to get information about the content
        cmd = ["zotify", "--info", url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
        output = result.stdout + result.stderr  # Check both stdout and stderr

        # Parse the output to find track count
        if content_type == "track":
            return 1
        if content_type == "album" or content_type == "playlist":
            # Try different patterns that might appear in Zotify output
            patterns = [
                r"Tracks: (\d+)",
                r"(\d+) tracks",
                r"(\d+) songs",
                r"Downloading (\d+) songs",
                r"Downloading (\d+) tracks",
                r"Found (\d+) items",
            ]

            for pattern in patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    return int(match.group(1))

        # Look for more generic patterns if specific ones fail
        match = re.search(r"(\d+) track", output, re.IGNORECASE)
        if match:
            return int(match.group(1))

        print(
            f"Debug - Zotify info output: {output[:200]}...",
        )  # Print first 200 chars for debugging
        return None
    except Exception as e:
        print(f"Error getting track count: {e}")
        return None


def download_spotify_content(
    url: str,
    target_dir: str = DEFAULT_TARGET_DIR,
    bulk_wait_time: int = 30,
    suppress_lyrics_errors: bool = True,
    download_format: str = "ogg",
) -> bool:
    """Download content from Spotify URL using Zotify."""
    print(f"Downloading from: {url}")
    print(f"Target directory: {target_dir}")

    # Make sure the target directory exists
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    # Find Zotify's default location
    user_home = os.path.expanduser("~")
    default_zotify_dir = os.path.join(user_home, "Music", "Zotify Music")

    # Get existing files before download in both directories
    existing_in_target = set(list_existing_files(target_dir))
    existing_in_default = (
        set()
        if not os.path.exists(default_zotify_dir)
        else set(list_existing_files(default_zotify_dir))
    )
    print(
        f"Found {len(existing_in_target)} existing files in target and {len(existing_in_default)} in Zotify's default location",
    )
    print("(Note: Existing files are tracked to identify new downloads)")

    # Try to get track count
    total_tracks = get_spotify_track_count(url)
    if total_tracks:
        print(f"Total tracks to download: {total_tracks}")

    # Run Zotify command - just use the default location for now
    cmd = ["zotify", url, "--bulk-wait-time", str(bulk_wait_time)]

    # Add format parameter if not default ogg
    if download_format != "ogg":
        cmd.extend(["--download-format", download_format])
        print(f"Using direct {download_format.upper()} conversion via Zotify")

    print("\nStarting Zotify download...")
    print("⏱️  Downloading in progress, will display real-time updates below:")

    # Use Popen instead of run to get real-time output
    try:
        process = subprocess.Popen(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )

        last_line = ""
        converting_progress = False

        # Read and display output in real-time
        while True:
            if process.stdout is None:
                break

            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break

            # Clean and display the line, overwriting the previous line
            clean_line = line.strip()

            # Skip certain error messages if suppression is enabled
            if suppress_lyrics_errors and (
                "Spotify API Error" in clean_line
                or "lyrics not available" in clean_line
                or "Skipping lyrics" in clean_line
            ):
                continue

            # Handle "waiting X seconds" message
            if "Waiting" in clean_line and "seconds" in clean_line:
                # Replace with a shorter message that doesn't say how long
                print("\rDownload successful. Processing...", end="")
                continue

            if clean_line:
                # Identify progress lines that should update in place
                is_progress_line = False

                # Check for various progress indicators
                if (
                    "%" in clean_line  # Percentage indicator
                    or any(
                        x in clean_line for x in ["⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                    )  # Spinner characters
                    or (
                        "track" in clean_line
                        and ("Preparing" in clean_line or "Converting" in clean_line)
                    )  # Progress status
                    or (
                        ": " in clean_line and any(x in clean_line for x in ["kB/s", "MB/s", "B/s"])
                    )  # Download speed
                    or
                    # Song download pattern matching (like "PinkPantheress - Stars: 15%|█▌")
                    (" - " in clean_line and ": " in clean_line and "%" in clean_line)
                    or
                    # Preparation indicators with dots
                    (clean_line.startswith("[") and ("●" in clean_line or "∙" in clean_line))
                    or
                    # Converting file progress
                    ("Converting file" in clean_line)
                ):
                    is_progress_line = True

                # Don't use our custom converting animation - let Zotify's show
                if is_progress_line:
                    # Update in place
                    print(f"\r{clean_line}", end="")
                    last_line = clean_line
                else:
                    # Regular message - print on new line
                    if last_line:
                        print()  # End the previous progress line
                        last_line = ""
                    print(clean_line)

        # Make sure we end with a newline after the last progress update
        if last_line:
            print()

        return_code = process.poll()
    except Exception as e:
        print(f"\nError during download process: {e}")
        return False

    # Check if the download was successful
    if return_code != 0:
        print(f"Error during download: exit code {return_code}")
        return False

    # Now check what new files were downloaded to the default location
    if os.path.exists(default_zotify_dir):
        current_in_default = set(list_existing_files(default_zotify_dir))
        new_files_in_default = current_in_default - existing_in_default

        if new_files_in_default:
            print(
                f"✅ Download successful! Found {len(new_files_in_default)} new files in Zotify's default location.",
            )

            # Move new files to target directory
            print(f"📦 Moving files to target directory: {target_dir}")
            for file_path in new_files_in_default:
                rel_path = os.path.relpath(file_path, default_zotify_dir)
                dest_path = os.path.join(target_dir, rel_path)

                # Make sure destination directory exists
                dest_dir = os.path.dirname(dest_path)
                os.makedirs(dest_dir, exist_ok=True)

                # Move file with shutil to handle cross-device moves
                import shutil

                try:
                    shutil.move(file_path, dest_path)
                    print(f"  ↳ Moved: {rel_path}")
                except Exception as e:
                    print(f"  ❌ Error moving {rel_path}: {e}")

            # Now check what's in the target directory
            current_in_target = set(list_existing_files(target_dir))
            new_files_in_target = current_in_target - existing_in_target

            if new_files_in_target:
                print(f"\n✨ Successfully moved {len(new_files_in_target)} files to {target_dir}")
                return True
            print("\n⚠️ Failed to move files to target directory")
            return False
        print("⚠️ No new files found in Zotify's default location. Something went wrong.")
        return False
    print("❓ Default Zotify directory not found.")
    return False


def convert_ogg_to_mp3(file_path: str, remove_original: bool = False) -> bool:
    """Convert a single .ogg file to .mp3 format using ffmpeg."""
    if not file_path.lower().endswith(".ogg"):
        print(f"Not an OGG file: {file_path}")
        return False

    output_path = file_path[:-4] + ".mp3"
    file_path_obj = Path(file_path)
    output_path_obj = Path(output_path)

    if output_path_obj.exists():
        print(f"MP3 already exists: {output_path}")
        return True

    cmd = [
        "ffmpeg",
        "-i",
        file_path,
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        output_path,
        "-y",
        "-loglevel",
        "error",
    ]
    try:
        subprocess.run(cmd, check=True, text=True, capture_output=True)  # noqa: S603

        # Verify the output file exists and has a reasonable size
        if not output_path_obj.exists() or output_path_obj.stat().st_size < 1024:
            print(f"Error: Conversion produced an invalid file: {output_path}")
            return False

        # Remove original if requested
        if remove_original and output_path_obj.exists():
            file_path_obj.unlink()

        return True  # noqa: TRY300
    except subprocess.CalledProcessError as e:
        print(f"Error converting {file_path}: {e}")
        return False


def convert_all_ogg_files(directory: str, remove_originals: bool = False) -> bool:
    """Convert all .ogg files in directory to .mp3 format with progress bar."""
    unconverted = find_unconverted_files(directory)

    if not unconverted:
        print("No unconverted OGG files found!")
        return True

    print(f"Found {len(unconverted)} unconverted OGG files")
    success_count = 0

    # Create progress bar
    progress_bar = tqdm(total=len(unconverted), desc="Converting")

    for file_path in unconverted:
        # Update progress bar with file name
        file_name = Path(file_path).name
        progress_bar.set_description(f"Converting {file_name}")

        if convert_ogg_to_mp3(file_path, remove_originals):
            success_count += 1

        progress_bar.update(1)

    progress_bar.close()

    print(f"Successfully converted {success_count} of {len(unconverted)} files")
    return success_count == len(unconverted)


def main() -> int:
    """Download and convert Spotify content."""
    parser = argparse.ArgumentParser(
        description="Spotify Music Downloader and Converter",
        epilog="""
Note: The download process involves two separate conversions:
1. Zotify converts from Spotify's format to OGG (happens during download)
2. This script converts OGG to MP3 (happens after download)

If you only need OGG files, use --keep-ogg to skip the second conversion.
If you want MP3 files faster, use --direct-mp3 to have Zotify convert directly to MP3.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Spotify URL (track, album, or playlist)",
    )
    parser.add_argument(
        "-t",
        "--target",
        default=DEFAULT_TARGET_DIR,
        help=f"Target directory (default: {DEFAULT_TARGET_DIR})",
    )
    parser.add_argument(
        "-w",
        "--wait-time",
        type=int,
        default=30,
        help="Bulk wait time between downloads in seconds (default: 30)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download and only convert existing files",
    )
    parser.add_argument(
        "--keep-ogg",
        action="store_true",
        help="Keep files in OGG format and skip MP3 conversion (faster)",
    )
    parser.add_argument(
        "--direct-mp3",
        action="store_true",
        help="Use Zotify's built-in conversion to download directly to MP3 (fastest for MP3)",
    )
    parser.add_argument(
        "--remove-originals",
        action="store_true",
        help="Remove original .ogg files after successful conversion to MP3",
    )
    parser.add_argument(
        "--show-lyrics-errors",
        action="store_true",
        help="Show errors related to lyrics fetching (hidden by default)",
    )

    args = parser.parse_args()

    # Check for conflicting args
    if args.keep_ogg and args.direct_mp3:
        print("Error: Cannot use both --keep-ogg and --direct-mp3 options")
        parser.print_help()
        return 1

    # Check if URL is provided when not skipping download
    if not args.skip_download and not args.url:
        print("Error: Spotify URL is required when downloading content")
        parser.print_help()
        return 1

    # Create target directory if it doesn't exist
    target_dir_path = Path(args.target).expanduser()
    target_dir_path.mkdir(parents=True, exist_ok=True)
    target_dir = str(target_dir_path)

    if not args.skip_download:
        # Validate URL
        if not is_valid_spotify_url(args.url):
            print(f"Invalid Spotify URL: {args.url}")
            print(
                "URL must be in format: https://open.spotify.com/(track|album|playlist)/ID",
            )
            return 1

        # Download content
        content_type = get_spotify_content_type(args.url)
        print(f"Content type: {content_type}")

        # Determine download format
        download_format = "mp3" if args.direct_mp3 else "ogg"

        success = download_spotify_content(
            args.url,
            target_dir,
            args.wait_time,
            suppress_lyrics_errors=not args.show_lyrics_errors,
            download_format=download_format,
        )
        if not success:
            print("Download failed!")
            return 1

    # Skip OGG to MP3 conversion if using direct-mp3 or keep-ogg options
    if not args.keep_ogg and not args.direct_mp3:
        # Convert OGG files to MP3
        print("\nConverting OGG files to MP3...")
        convert_all_ogg_files(target_dir, args.remove_originals)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation canceled by user")
        sys.exit(1)
