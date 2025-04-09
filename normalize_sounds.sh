#!/bin/bash

# Directory containing sound files
SOUNDS_DIR="sounds"

# Target loudness level (in dB)
TARGET_LOUDNESS=-23

# Process each file in the directory
for file in "$SOUNDS_DIR"/*; do
    # Get the file extension
    extension="${file##*.}"
    
    # Create a temporary file for the normalized audio
    temp_file="${file%.*}_normalized.${extension}"
    
    # Normalize the audio
    ffmpeg -i "$file" -af loudnorm=I=$TARGET_LOUDNESS:TP=-1.5:LRA=11 "$temp_file"
    
    # Replace the original file with the normalized file
    mv "$temp_file" "$file"
done