#!/bin/bash

# Script to convert .ogg files to .mp3 format using ffmpeg
# Usage: ./convert_ogg_to_mp3.sh [directory]
# If no directory is specified, it will use the current directory

# Function to convert a single file
convert_file() {
    input_file="$1"
    output_file="${input_file%.ogg}.mp3"

    echo "Converting: $input_file"
    ffmpeg -i "$input_file" -codec:a libmp3lame -q:a 2 "$output_file" -loglevel warning

    # Check if conversion was successful
    if [ $? -eq 0 ]; then
        echo "✓ Successfully converted to: $output_file"
        # Uncomment to delete original .ogg file after successful conversion
        # rm "$input_file"
    else
        echo "✗ Failed to convert: $input_file"
    fi
}

# Process a directory
process_directory() {
    local dir="$1"
    echo "Processing directory: $dir"

    # Find all .ogg files in the current directory
    for ogg_file in "$dir"/*.ogg; do
        # Check if the file exists (in case the wildcard didn't match any files)
        [ -e "$ogg_file" ] || continue
        convert_file "$ogg_file"
    done

    # Process subdirectories recursively
    for subdir in "$dir"/*/; do
        [ -d "$subdir" ] || continue
        process_directory "$subdir"
    done
}

# Start processing from the specified directory or current directory
start_dir="${1:-.}"
process_directory "$start_dir"

echo "Conversion complete!"
