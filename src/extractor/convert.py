#!/usr/bin/env python3

"""Convert OGG files to MP3."""

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def find_unconverted_files(directory: str) -> list[str]:
    """Find .ogg files that don't have a corresponding .mp3 file."""
    unconverted = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".ogg"):
                ogg_path = Path(root) / file
                mp3_path = ogg_path.with_suffix(".mp3")
                if not mp3_path.exists():
                    unconverted.append(str(ogg_path))
    return unconverted


def convert_ogg_to_mp3(file_path: str, remove_original: bool = False) -> bool:
    """Convert a single .ogg file to .mp3 format using ffmpeg."""
    file_path_obj = Path(file_path)
    output_path = file_path_obj.with_suffix(".mp3")
    cmd = [
        "ffmpeg",
        "-i",
        file_path,
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(output_path),
        "-y",
        "-loglevel",
        "error",
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603

        # Remove original if requested and conversion succeeded
        if remove_original and output_path.exists():
            file_path_obj.unlink()

        return True  # noqa: TRY300
    except subprocess.CalledProcessError:
        return False


def copy_audio_files(source_dir: str, target_dir: str, extension: str = ".mp3") -> int:
    """Recursively find audio files with the given extension and copy them to target directory.

    Files will be flattened (no subdirectory structure preserved).

    Args:
        source_dir: Directory to search for audio files recursively
        target_dir: Directory to copy files to (will be created if it doesn't exist)
        extension: File extension to search for (default: ".mp3")

    Returns
    -------
        Number of files copied
    """
    # Create target directory if it doesn't exist
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    # Counters
    copied_count = 0
    all_files_count = 0
    audio_files_found = 0

    print(f"Searching for *{extension} files in {source_dir}...")

    # Walk through source directory
    for root, _dirs, files in os.walk(source_dir):
        all_files_count += len(files)
        for file in files:
            # Print every 100 files to show progress
            if all_files_count % 100 == 0:
                print(f"Checked {all_files_count} files so far...")

            # Check if file has the target extension (case insensitive)
            if file.lower().endswith(extension.lower()):
                audio_files_found += 1
                source_path = Path(root) / file

                # Debug information
                print(f"Found matching file: {source_path}")

                # Handle filename conflicts by appending a number if needed
                target_filename = file
                target_path = Path(target_dir) / target_filename
                counter = 1

                while target_path.exists():
                    name = Path(file).stem
                    ext = Path(file).suffix
                    target_filename = f"{name}_{counter}{ext}"
                    target_path = Path(target_dir) / target_filename
                    counter += 1

                # Copy the file
                try:
                    shutil.copy2(str(source_path), str(target_path))
                    copied_count += 1
                    print(f"Copied: {source_path.name} → {target_filename}")
                except Exception as e:  # noqa: BLE001
                    print(f"Error copying {source_path}: {e}")

    # Print summary
    print("\nSummary:")
    print(f"Total files checked: {all_files_count}")
    print(f"Files with {extension} extension found: {audio_files_found}")
    print(f"Files successfully copied: {copied_count}")
    print(f"Destination directory: {target_dir}")

    return copied_count


def main() -> None:
    """Convert OGG files to MP3 and manage audio files."""
    parser = argparse.ArgumentParser(description="Convert OGG files to MP3 and manage audio files")
    parser.add_argument(
        "directory",
        help="Directory containing audio files",
    )
    parser.add_argument(
        "--remove-originals",
        action="store_true",
        help="Remove original OGG files after conversion",
    )
    parser.add_argument(
        "--copy-to",
        help="Copy all MP3 files to target directory (flattened structure)",
    )
    parser.add_argument(
        "--extension",
        default=".mp3",
        help="File extension to search for when copying (default: .mp3)",
    )
    args = parser.parse_args()

    # Get list of unconverted files
    files_to_convert = find_unconverted_files(args.directory)

    if not files_to_convert:
        print("No unconverted OGG files found!")
        return

    print(f"Converting {len(files_to_convert)} OGG files to MP3...")

    # Convert each file
    success_count = 0
    for i, file_path in enumerate(files_to_convert, 1):
        print(f"[{i}/{len(files_to_convert)}] Converting: {Path(file_path).name}")
        if convert_ogg_to_mp3(file_path, args.remove_originals):
            success_count += 1

    print(
        f"Conversion complete! Successfully converted {success_count} of {len(files_to_convert)} files.",
    )

    # If copy-to argument is provided, copy MP3 files
    if args.copy_to:
        print(f"\nCopying {args.extension} files to {args.copy_to}...")
        copy_audio_files(args.directory, args.copy_to, args.extension)


if __name__ == "__main__":
    copy_audio_files(
        "/Users/thomasbrouwer/code/extract-audio/extracted/Noah/Zotify Music",
        "/Users/thomasbrouwer/code/extract-audio/extracted/Noah/converted",
        extension=".mp3",
    )
