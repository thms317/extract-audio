"""Module for extracting and downloading audio files from web archives."""

import argparse
import random
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def find_mp3_urls_from_archive(archive_url: str) -> list[str]:
    """Find and list potential MP3 URLs within an archived webpage from the Wayback Machine.

    Attempts to construct working Wayback Machine URLs, avoiding double prefixes.

    Parameters
    ----------
    archive_url : str
        The URL of the archived webpage on the Wayback Machine.

    Returns
    -------
    list[str]
        A list of unique MP3 URLs found on the page, adjusted for Wayback Machine.
    """
    try:
        response = requests.get(archive_url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.content, "html.parser")

        mp3_urls = set()

        # Extract the Wayback Machine timestamp from the archive URL
        timestamp_match = re.search(r"/web/(\d+)/", archive_url)
        wayback_timestamp = timestamp_match.group(1) if timestamp_match else None

        if not wayback_timestamp:
            print("Warning: Could not extract Wayback Machine timestamp from the URL.")

        # Search for <audio> tags with <source> tags containing .mp3
        audio_sources = soup.find_all("audio")
        for audio_tag in audio_sources:
            source_tags = audio_tag.find_all("source", src=re.compile(r"\.mp3$", re.IGNORECASE))
            for source_tag in source_tags:
                src = source_tag.get("src")
                if src:
                    mp3_urls.add(construct_wayback_url(src, archive_url, wayback_timestamp, "im_"))

            # Check audio tag src attribute
            audio_src = audio_tag.get("src")  # type: ignore[attr-defined]
            if audio_src and isinstance(audio_src, str) and audio_src.lower().endswith(".mp3"):
                mp3_urls.add(
                    construct_wayback_url(audio_src, archive_url, wayback_timestamp, "oe_"),
                )

        # Search for <a> tags with href ending in .mp3
        a_tags = soup.find_all("a", href=re.compile(r"\.mp3$", re.IGNORECASE))
        for a_tag in a_tags:
            href = a_tag.get("href")
            if href:
                mp3_urls.add(construct_wayback_url(href, archive_url, wayback_timestamp, "im_"))

        return sorted(mp3_urls)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return []
    except Exception as e:
        print(f"An error occurred while parsing the HTML: {e}")
        return []


def construct_wayback_url(url: str, archive_url: str, timestamp: str, type_prefix: str) -> str:
    """Construct a Wayback Machine URL, avoiding double prefixes."""
    if not timestamp:
        return url  # Return original URL if timestamp is missing

    if url.startswith("https://web.archive.org/web/"):
        return url  # URL already has a Wayback prefix, assume it's correct

    if url.startswith("/web/"):
        # URL already has a partial Wayback prefix, just add the domain
        return f"https://web.archive.org{url}"

    if url.startswith("/"):
        # Relative URL, needs base URL and timestamp
        base_url_match = re.search(r"https?://[^/]+", archive_url)
        if base_url_match:
            base_domain = base_url_match.group(0)
            return f"https://web.archive.org/web/{timestamp}{type_prefix}/{base_domain}{url}"
        return f"https://web.archive.org/web/{timestamp}{type_prefix}/{url[1:]}"  # Try without base domain
    # Absolute URL, needs timestamp prefix
    return f"https://web.archive.org/web/{timestamp}{type_prefix}/{url}"


def download_mp3(  # noqa: C901, PLR0912, PLR0913
    url: str,
    destination_dir: str,
    filename: str | None = None,
    max_retries: int = 3,
    delay_between_retries: int = 5,
    force_download: bool = False,
) -> tuple[bool, str, None] | tuple[bool, None, str]:
    """Download an MP3 file from the given URL and save it to the specified destination.

    Attempts to construct working Wayback Machine URLs, avoiding double prefixes.
    Includes retry logic with exponential backoff for handling connection issues.

    Parameters
    ----------
    url : str
        The URL of the MP3 file to download
    destination_dir : str
        Directory where the MP3 file will be saved
    filename : str | None, optional
        Optional custom filename, if None, extracts filename from URL
    max_retries : int, optional
        Maximum number of retry attempts (default: 3)
    delay_between_retries : int, optional
        Base delay between retries in seconds (default: 5)
    force_download : bool, optional
        If True, will download even if file exists (default: False)

    Returns
    -------
    tuple[bool, str, None] | tuple[bool, None, str]
        Tuple (success, filepath, error_message)
        success : bool
            Boolean indicating whether download was successful
        filepath : str | None
            Path where the file was saved (None if failed)
        error_message : str | None
            Description of error (None if successful)
    """
    # Create destination directory if it doesn't exist
    Path(destination_dir).mkdir(parents=True, exist_ok=True)

    # Determine filename if not provided
    if not filename:
        # Extract filename from URL
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name

        # Ensure filename ends with .mp3
        if not filename.lower().endswith(".mp3"):
            filename += ".mp3"

    filepath = Path(destination_dir) / filename
    filepath_str = str(filepath)

    # Check if file already exists and is not empty
    if not force_download and filepath.exists() and filepath.stat().st_size > 0:
        print(f"File already exists at {filepath_str}, skipping download.")
        return True, filepath_str, None

    for attempt in range(max_retries):
        try:
            # Make HTTP request with streaming enabled
            print(f"Downloading {url} (attempt {attempt + 1}/{max_retries})")

            # Use a session with increased timeout
            session = requests.Session()
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                },
            )

            response = session.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Get content length if available
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            # Download file
            with filepath.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int(100 * downloaded / total_size)
                            print(
                                f"\rProgress: {percent}% ({downloaded}/{total_size} bytes)",
                                end="",
                            )

            print()  # Newline after progress report

            # Verify file was downloaded successfully
            if filepath.stat().st_size > 0:
                return True, filepath_str, None
            # Remove empty file
            filepath.unlink()
            return False, None, "Downloaded file is empty"  # noqa: TRY300

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {e!s}"
            print(f"Attempt {attempt + 1}/{max_retries} failed: {error_msg}")

            if attempt < max_retries - 1:
                # Calculate exponential backoff with jitter
                # Using random here is fine since it's not for cryptographic purposes
                sleep_time = delay_between_retries * (2**attempt) + random.uniform(0, 2)
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                return False, None, error_msg

        except Exception as e:
            error_msg = f"Error downloading {url}: {e!s}"
            print(f"Attempt {attempt + 1}/{max_retries} failed: {error_msg}")

            if attempt < max_retries - 1:
                # Using random here is fine since it's not for cryptographic purposes
                sleep_time = delay_between_retries * (2**attempt) + random.uniform(0, 2)
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                return False, None, error_msg

    return False, None, "Maximum retry attempts reached"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract and download MP3s from Wayback Machine archives",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="https://web.archive.org/web/20210418151905/https://www.hoorspelen.eu/producties/hsp-p/pluk-van-de-petteflet.html",
        help="Archive URL to search for MP3s",
    )
    parser.add_argument(
        "-d",
        "--download",
        action="store_true",
        help="Download found MP3 files",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="mp3_downloads",
        help="Directory to save downloaded MP3s",
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        default=3,
        help="Maximum number of retry attempts per file",
    )
    parser.add_argument(
        "-w",
        "--wait",
        type=float,
        default=2.0,
        help="Wait time between downloads in seconds",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force download even if files already exist",
    )
    args = parser.parse_args()

    archive_url = args.url
    mp3_links = find_mp3_urls_from_archive(archive_url)

    if mp3_links:
        print(f"Found {len(mp3_links)} potential MP3 URLs (adjusted for Wayback Machine):")
        for url in mp3_links:
            print(url)

        if args.download:
            print(f"\nDownloading {len(mp3_links)} MP3 files to: {args.output}")
            successful = 0
            failed = 0

            for i, url in enumerate(mp3_links, 1):
                print(f"\nDownloading file {i}/{len(mp3_links)}")
                success, filepath, error = download_mp3(
                    url,
                    args.output,
                    max_retries=args.retries,
                    force_download=args.force,
                )

                if success:
                    successful += 1
                    print(f"✓ Saved to {filepath}")
                else:
                    failed += 1
                    print(f"✗ Failed: {error}")

                # Add delay between downloads to avoid rate limiting
                if i < len(mp3_links):
                    # Using random here is fine since it's not for cryptographic purposes
                    wait_time = args.wait + random.uniform(0, 1)
                    print(f"Waiting {wait_time:.2f} seconds before next download...")
                    time.sleep(wait_time)

            print(f"\nDownload complete: {successful} successful, {failed} failed")
        else:
            print("\nNote:")
            print("These URLs have been constructed based on the Wayback Machine timestamp.")
            print("Please verify if they work correctly.")
            print("Use --download to save the MP3 files.")
    else:
        print("No MP3 URLs found on the page.")
