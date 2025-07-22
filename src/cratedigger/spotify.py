#!/usr/bin/env python3

"""Download and convert Spotify content."""

import argparse
import os
import re
import shutil
import subprocess
import sys
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


def list_existing_files(
    directory: str,
    extensions: list[str] | None = None,
) -> list[str]:
    """List all audio files in the directory."""
    if extensions is None:
        extensions = [".ogg", ".mp3", ".jpg", ".jpeg", ".png"]

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
        if content_type in {"album", "playlist"}:
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
    except Exception as e:
        print(f"Error getting track count: {e}")
    return None


def download_spotify_content(  # noqa: C901, PLR0913, PLR0911, PLR0912, PLR0915
    url: str,
    target_dir: str = DEFAULT_TARGET_DIR,
    bulk_wait_time: int = 30,
    suppress_lyrics_errors: bool = True,
    download_format: str = "mp3",
    keep_library: bool = True,
    flat_structure: bool = True,
) -> bool:
    """Download content from Spotify URL using Zotify."""
    print(f"Downloading from: {url}")
    print(f"Target directory: {target_dir}")

    # Make sure the target directory exists
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    # Find Zotify's default location
    user_home = Path.home()
    default_zotify_dir = str(user_home / "Music" / "Zotify Music")

    # Get existing files before download in both directories
    existing_in_target = set(list_existing_files(target_dir))
    existing_in_default = (
        set()
        if not Path(default_zotify_dir).exists()
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

    # Add format parameter
    cmd.extend(["--download-format", download_format])
    if download_format == "mp3":
        print("Using direct MP3 conversion via Zotify")
    else:
        print(f"Using {download_format.upper()} format instead of MP3")

    print("\nStarting Zotify download...")
    print("⏱️  Downloading in progress, will display real-time updates below:")

    # Use Popen instead of run to get real-time output
    try:
        process = subprocess.Popen(  # noqa: S603
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )

        last_line = ""

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
                # Special handling for preparation and conversion status lines
                if clean_line.startswith("[") and ("●" in clean_line or "∙" in clean_line):
                    # Always print these on a new line
                    if last_line:
                        print()  # End previous line
                    print(clean_line)
                    last_line = ""
                    continue

                # For download progress bars (track downloading)
                if "%" in clean_line and ("|" in clean_line or "B/s" in clean_line):
                    # Update in place
                    print(f"\r{clean_line}", end="")
                    last_line = clean_line
                    continue

                # For other progress indicators (spinner characters)
                if any(x in clean_line for x in ["⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]):
                    print(f"\r{clean_line}", end="")
                    last_line = clean_line
                    continue

                # For all other messages, print on a new line
                if last_line:
                    print()  # End previous line
                print(clean_line)
                last_line = ""

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
    if Path(default_zotify_dir).exists():
        # Get audio files first
        audio_extensions = [".ogg", ".mp3"]
        image_extensions = [".jpg", ".jpeg", ".png"]

        # Check for new audio files
        current_audio_files = set(
            list_existing_files(default_zotify_dir, extensions=audio_extensions),
        )
        new_audio_files = current_audio_files - existing_in_default

        # Check for all image files in Zotify's directory
        all_image_files = set()
        for root, _, files in os.walk(default_zotify_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    image_path = str(Path(root) / file)
                    all_image_files.add(image_path)

        # Log about found files
        if new_audio_files:
            print(
                f"✅ Download successful! Found {len(new_audio_files)} new audio files in Zotify's default location.",
            )

            # Find all cover images in these directories
            artist_album_dirs = {str(Path(audio_file).parent) for audio_file in new_audio_files}
            related_images = set()

            for image_file in all_image_files:
                image_dir = str(Path(image_file).parent)
                # If the image is in an artist/album directory we saw, or it's named "cover.*"
                if image_dir in artist_album_dirs or Path(image_file).name.startswith(
                    "cover.",
                ):
                    related_images.add(image_file)

            # Get existing files in target to check for duplicates
            target_filenames = set()
            for _root, _, files in os.walk(target_dir):
                target_filenames.update(files)

            # Process files based on options
            if flat_structure:
                print(f"📦 Copying files to target directory (flat structure): {target_dir}")
            else:
                print(
                    f"📦 {'Copying' if keep_library else 'Moving'} files to target directory: {target_dir}",
                )

            # Process audio files
            processed_audio = 0
            processed_images = 0
            skipped_files = 0

            # Process audio files first
            for audio_file in new_audio_files:
                file_basename = Path(audio_file).name

                if flat_structure:
                    # Use flat structure - just the filename
                    dest_path = str(Path(target_dir) / file_basename)
                else:
                    # Use nested structure
                    rel_path = os.path.relpath(audio_file, default_zotify_dir)
                    dest_path = str(Path(target_dir) / rel_path)

                # Check if file already exists in target
                if Path(dest_path).exists():
                    print(f"  ↷ Skipped: {file_basename} (already exists in target)")
                    skipped_files += 1
                    continue

                # Make sure destination directory exists
                dest_path_obj = Path(dest_path)
                dest_path_obj.parent.mkdir(parents=True, exist_ok=True)

                # Copy or move based on keep_library setting
                try:
                    if keep_library:
                        shutil.copy2(audio_file, dest_path)
                        print(f"  ↳ Copied: {file_basename}")
                    else:
                        shutil.move(audio_file, dest_path)
                        print(f"  ↳ Moved: {file_basename}")
                    processed_audio += 1
                except Exception as e:
                    print(f"  ❌ Error processing {file_basename}: {e}")

            # Now process cover images
            for image_file in related_images:
                file_basename = Path(image_file).name

                if flat_structure:
                    # For flat structure with multiple cover images, we need to make the filenames unique
                    # Use parent folder name as prefix for cover art
                    parent_folder = Path(image_file).parent.name
                    if file_basename.startswith("cover."):
                        # If it's a cover file, add the parent folder name
                        name_parts = file_basename.split(".")
                        new_basename = f"{parent_folder}-{name_parts[0]}.{name_parts[1]}"
                    else:
                        new_basename = f"{parent_folder}-{file_basename}"
                    dest_path = str(Path(target_dir) / new_basename)
                else:
                    # Use nested structure
                    rel_path = os.path.relpath(image_file, default_zotify_dir)
                    dest_path = str(Path(target_dir) / rel_path)

                # Check if file already exists
                if Path(dest_path).exists():
                    print(f"  ↷ Skipped: {file_basename} (already exists in target)")
                    continue

                # Make sure destination directory exists
                dest_path_obj = Path(dest_path)
                dest_path_obj.parent.mkdir(parents=True, exist_ok=True)

                # Copy or move based on keep_library setting
                try:
                    if keep_library:
                        shutil.copy2(image_file, dest_path)
                        print(f"  ↳ Copied cover art: {Path(dest_path).name}")
                    else:
                        shutil.move(image_file, dest_path)
                        print(f"  ↳ Moved cover art: {Path(dest_path).name}")
                    processed_images += 1
                except Exception as e:
                    print(f"  ❌ Error processing cover art {file_basename}: {e}")

            # Summarize what happened
            action = "Copied" if keep_library else "Moved"
            structure = "flat structure" if flat_structure else "nested structure"
            if processed_audio > 0 or processed_images > 0:
                print(
                    f"\n✨ {action} {processed_audio} audio files and {processed_images} cover images to {target_dir} ({structure})",
                )
                if skipped_files > 0:
                    print(f"   Skipped {skipped_files} files that already existed in target")
                return True
            if skipped_files > 0:
                print("\n⚠️ All files already exist in target. Nothing new to process.")
                return True
            print("\n⚠️ Failed to process any files to target directory")
            return False
        print("⚠️ No new audio files found in Zotify's default location. Something went wrong.")
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
Note: By default, files are directly downloaded as MP3 using Zotify's built-in conversion.
Alternative options:
- Use --use-ogg to download as OGG first, then convert to MP3 (two-step process)
- Use --keep-ogg to download as OGG and skip MP3 conversion entirely
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
        help="Download as OGG format and skip MP3 conversion entirely",
    )
    parser.add_argument(
        "--use-ogg",
        action="store_true",
        help="Use two-step process: download as OGG first, then convert to MP3",
    )
    parser.add_argument(
        "--keep-library",
        action="store_true",
        help="Keep files in Zotify's default location (creates a library)",
    )
    parser.add_argument(
        "--flat-structure",
        action="store_true",
        help="Save files to target with a flat structure (no artist/album folders)",
    )
    parser.add_argument(
        "--remove-originals",
        action="store_true",
        help="Remove original .ogg files after conversion to MP3 (only with --use-ogg)",
    )
    parser.add_argument(
        "--show-lyrics-errors",
        action="store_true",
        help="Show errors related to lyrics fetching (hidden by default)",
    )

    args = parser.parse_args()

    # Check for conflicting args
    if args.keep_ogg and args.use_ogg:
        print("Error: Cannot use both --keep-ogg and --use-ogg options")
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
        download_format = "ogg" if (args.keep_ogg or args.use_ogg) else "mp3"

        success = download_spotify_content(
            args.url,
            target_dir,
            args.wait_time,
            suppress_lyrics_errors=not args.show_lyrics_errors,
            download_format=download_format,
            keep_library=args.keep_library,
            flat_structure=args.flat_structure,
        )
        if not success:
            print("Download failed!")
            return 1

    # Convert OGG to MP3 if using two-step process
    if args.use_ogg or (args.skip_download and not args.keep_ogg):
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
