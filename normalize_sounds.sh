#!/bin/bash

# Directory containing sound category subdirectories
SOUNDS_BASE_DIR="sounds"

# Target loudness level (in LUFS)
TARGET_LOUDNESS=-23.0 # Using LUFS standard, ensure ffmpeg version supports it well.
# Alternatively, for older ffmpeg, you might stick to dB, but LUFS is preferred for perceived loudness.

# Check if SOUNDS_BASE_DIR exists
if [ ! -d "$SOUNDS_BASE_DIR" ]; then
    echo "Error: Directory '$SOUNDS_BASE_DIR' not found."
    exit 1
fi

echo "Starting sound normalization..."

# Find all files in the SOUNDS_BASE_DIR and its subdirectories
# -type f specifies that we are looking for regular files
# -print0 and xargs -0 handle filenames with spaces or special characters safely
find "$SOUNDS_BASE_DIR" -type f -print0 | while IFS= read -r -d $'\0' file; do
    echo "Processing file: $file"
    
    # Get the file extension
    extension="${file##*.}"
    
    # Define a temporary file name in the same directory as the original
    # This avoids issues with moving files across different filesystems if /tmp is one
    temp_file_dir=$(dirname "$file")
    temp_file_base=$(basename "$file" ".$extension")_normalized
    temp_file="${temp_file_dir}/${temp_file_base}.${extension}"
    
    # Normalize the audio using ffmpeg-normalize or loudnorm
    # Using loudnorm with specified parameters for integrated loudness (I), true peak (TP), and loudness range (LRA)
    # Ensure your ffmpeg version is recent enough for these loudnorm parameters.
    if ffmpeg -i "$file" -af loudnorm=I=$TARGET_LOUDNESS:TP=-2.0:LRA=7 -ar 48000 -y "$temp_file" >/dev/null 2>&1; then
        # Replace the original file with the normalized file
        if mv "$temp_file" "$file"; then
            echo "Normalized and replaced: $file"
        else
            echo "Error: Failed to move normalized file back to $file. Temporary file: $temp_file"
            # Optionally remove temp file if move fails and you're sure
            # rm -f "$temp_file"
        fi
    else
        echo "Error: ffmpeg failed to normalize $file."
        # Remove the temp file if ffmpeg failed, as it might be corrupted or empty
        if [ -f "$temp_file" ]; then
            rm -f "$temp_file"
        fi
    fi
done

echo "Sound normalization complete."