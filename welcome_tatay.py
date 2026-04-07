#!/usr/bin/env python3
"""
Double-clap welcome script for Señor Tatay (Ubuntu Version).

Detects 2 claps → AI voice says welcome → opens YouTube

Dependencies:
 pip install sounddevice numpy pyttsx3 gTTS

Usage:
 python welcome_tatay.py
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser

import numpy as np
import sounddevice as sd
import pyttsx3
from gtts import gTTS

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
SAMPLE_RATE = 44100
BLOCK_SIZE = int(SAMPLE_RATE * 0.05)  # 50 ms per block
THRESHOLD = 0.20  # Minimum RMS to count as a clap (adjust if it fails)
COOLDOWN = 0.1  # Minimum pause between claps in seconds
DOUBLE_WINDOW = 2.0  # Time window for the second clap

YOUTUBE_URL = "https://www.youtube.com/watch?v=hEIexwwiKKU"
MESSAGE = "Welcome home, Señor Tatay."

# ──────────────────────────────────────────────────────────────────────────────
# Global state
# ──────────────────────────────────────────────────────────────────────────────
clap_times: list[float] = []
triggered = False
lock = threading.Lock()


# ──────────────────────────────────────────────────────────────────────────────
# Clap detection
# ──────────────────────────────────────────────────────────────────────────────
def audio_callback(indata, frames, time_info, status):
    global triggered, clap_times

    if triggered:
        return

    rms = float(np.sqrt(np.mean(indata ** 2)))
    now = time.time()

    if rms > THRESHOLD:
        with lock:
            # Ignore if within the cooldown of the previous clap
            if clap_times and (now - clap_times[-1]) < COOLDOWN:
                return

            clap_times.append(now)
            # Clear claps outside the window
            clap_times = [t for t in clap_times if now - t <= DOUBLE_WINDOW]

            count = len(clap_times)
            print(f" 👏 Clap {count}/2 (RMS={rms:.3f})")

            if count >= 2:
                triggered = True
                clap_times = []
                threading.Thread(target=welcome_sequence, daemon=True).start()


# ──────────────────────────────────────────────────────────────────────────────
# Welcome sequence
# ──────────────────────────────────────────────────────────────────────────────
def welcome_sequence():
 print("\n🚀 Starting welcome sequence…\n")

 speak(MESSAGE)
 open_youtube()

 print("\n✅ Sequence completed.\n")


def speak(text: str):
    """TTS with pyttsx3 and fallback to gTTS."""
    print(f" 🔊 Saying: «{text}»")

    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.setProperty("rate", 148)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"pyttsx3 failed: {e}")
        print("Falling back to gTTS")
        try:
            tts = gTTS(text=text, lang='en')
            filename = 'welcome.mp3'
            tts.save(filename)
            os.system(f'mpg321 {filename}')  # Requires mpg321 to be installed
        except Exception as e:
            print(f"gTTS failed: {e}")
            print("TTS failed, sorry!")


def open_youtube():
 print(f" 🎵 Opening YouTube…")
 webbrowser.open(YOUTUBE_URL)
 time.sleep(1.2)  # Allow the browser to load before continuing


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main():
    global triggered

    print("=" * 55)
    print(" 🎤 Listening for claps… (Ctrl+C to exit)")
    print(f" Current threshold: {THRESHOLD} (adjust THRESHOLD if it fails)")
    print("=" * 55)

    try:
        with sd.InputStream(
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                channels=1,
                dtype="float32",
                callback=audio_callback,
        ):
            while True:
                time.sleep(0.1)
                if triggered:
                    # Wait for the sequence to finish and listen again
                    time.sleep(8)
                    triggered = False
                    print("\n👂 Listening again…\n")
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
        sys.exit(0)


if __name__ == "__main__":
 main()
