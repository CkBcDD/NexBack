"""
This script generates audio files for the letters in AUDIO_POOL using edge-tts.
I used this script to generate .mp3 audios,
and I manaully converted them to .opus using FFmpeg for better performance in the app,
which is not included in this script.
U can use it as a reference or modify it as needed.

Here's the FFmpeg command I used for conversion:
    -c:a libopus ^
    -ar 24000 ^
    -ac 1 ^
    -b:a 32k ^
    -vbr on ^
    -compression_level 10 ^
"""

import asyncio
import os

import edge_tts

AUDIO_POOL = "ABCHKLQR"
OUTPUT_DIR = "resources/audio"
VOICE = "en-US-JennyNeural"  # Clear female voice


async def generate_audio():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"Generating audio files in {OUTPUT_DIR} using voice {VOICE}...")

    for char in AUDIO_POOL:
        text = char
        # Add some pause or specific pronunciation if needed, but single letter usually works fine.
        # Sometimes "A" might be read as "a" (article) vs "A" (letter).
        # To ensure letter pronunciation, we might need to tweak, but let's try direct first.
        # For "A", "H", etc. usually fine.

        output_file = os.path.join(OUTPUT_DIR, f"{char}.mp3")
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_file)
        print(f"Generated {output_file}")


if __name__ == "__main__":
    asyncio.run(generate_audio())
