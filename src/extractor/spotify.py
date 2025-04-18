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

DEFAULT_TARGET_DIR = "extracted/v2"


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


def list_existing_files(directory: str, extensions: list[str] | None = None) -> list[str]:
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


def check_download_progress(
    target_dir: str,
    existing_before: set[str],
    poll_interval: float = 1.0,
) -> None:
    """Provide visual feedback during download by checking directory changes."""
    print("Download in progress...")
    spinner = ["|", "/", "-", "\\"]
    spinner_idx = 0
    start_time = time.time()
    last_files_count = 0

    try:
        while True:
            # Get current files
            current_files = set(list_existing_files(target_dir))
            new_files = current_files - existing_before

            # Calculate progress indicators
            elapsed = time.time() - start_time
            files_per_min = len(new_files) / (elapsed / 60.0) if elapsed > 0 else 0

            # Update display
            if len(new_files) > last_files_count:
                print(
                    f"\rDownloaded {len(new_files)} files ({files_per_min:.1f} files/min) {spinner[spinner_idx]}",
                    end="",
                )
                last_files_count = len(new_files)
            else:
                print(
                    f"\rDownloaded {len(new_files)} files ({files_per_min:.1f} files/min) {spinner[spinner_idx]}",
                    end="",
                )

            spinner_idx = (spinner_idx + 1) % len(spinner)

            # Check if process is still running
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nProgress monitoring interrupted.")


def download_spotify_content(
    url: str,
    target_dir: str = DEFAULT_TARGET_DIR,
    bulk_wait_time: int = 30,
) -> bool:
    """Download content from Spotify URL using Zotify."""
    print(f"Downloading from: {url}")
    print(f"Target directory: {target_dir}")

    # # Configure Zotify to use the specified target directory
    # if not configure_zotify(target_dir):
    #     print("Failed to configure Zotify with the target directory.")
    #     return False

    # Get existing files before download
    existing_before = set(list_existing_files(target_dir))
    print(f"Found {len(existing_before)} existing audio files before download")

    # Run Zotify command in a separate thread to monitor progress
    cmd = ["zotify", url, "--bulk-wait-time", str(bulk_wait_time)]

    import threading

    # Start the download process
    proc = subprocess.Popen(  # noqa: S603
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Start progress monitoring thread
    progress_thread = threading.Thread(
        target=check_download_progress,
        args=(target_dir, existing_before),
    )
    progress_thread.daemon = True
    progress_thread.start()
    # Capture and display Zotify output
    if proc.stdout is not None:
        for line in proc.stdout:
            stripped_line = line.strip()
            if stripped_line:
                print(f"\r{stripped_line}")

    # Wait for completion
    proc.wait()

    # Print a newline for clean separation
    print()

    if proc.returncode != 0:
        print(f"Error during download: {proc.returncode}")
        if proc.stderr is not None:
            for line in proc.stderr:
                print(line)
        return False

    # Get files after download
    existing_after = set(list_existing_files(target_dir))

    # Find new files
    new_files = existing_after - existing_before
    print(f"Downloaded {len(new_files)} new files:")

    # Show the first 10 files, and total count if more
    sorted_new_files = sorted(new_files)
    for _idx, file in enumerate(sorted_new_files[:10]):
        print(f"  - {os.path.relpath(file, target_dir)}")

    if len(new_files) > 10:
        print(f"  ... and {len(new_files) - 10} more files")

    return True


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
    parser = argparse.ArgumentParser(description="Spotify Music Downloader and Converter")
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
        "--skip-convert",
        action="store_true",
        help="Skip conversion to MP3",
    )
    parser.add_argument(
        "--remove-originals",
        action="store_true",
        help="Remove original .ogg files after successful conversion",
    )

    args = parser.parse_args()

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
            print("URL must be in format: https://open.spotify.com/(track|album|playlist)/ID")
            return 1

        # Download content
        content_type = get_spotify_content_type(args.url)
        print(f"Content type: {content_type}")

        success = download_spotify_content(args.url, target_dir, args.wait_time)
        if not success:
            print("Download failed!")
            return 1

    if not args.skip_convert:
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
