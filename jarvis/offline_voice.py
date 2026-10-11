"""Optional offline speech-to-text using Vosk and a local model folder.

Install requirements-voice-offline.txt and set JARVIS_VOSK_MODEL_PATH to a
downloaded Vosk model directory. Audio is processed locally by this module.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def listen_once_offline(timeout=8, sample_rate=16000):
    model_path = os.getenv("JARVIS_VOSK_MODEL_PATH", "").strip()
    if not model_path or not Path(model_path).is_dir():
        raise RuntimeError("Set JARVIS_VOSK_MODEL_PATH to a downloaded Vosk model folder.")
    try:
        import sounddevice as sd
        from vosk import KaldiRecognizer, Model
    except ImportError as exc:
        raise RuntimeError("Install offline voice dependencies: pip install -r requirements-voice-offline.txt") from exc

    model = Model(model_path)
    recognizer = KaldiRecognizer(model, sample_rate)
    import queue
    audio_queue = queue.Queue()

    def callback(indata, frames, time_info, status):
        audio_queue.put(bytes(indata))

    try:
        with sd.RawInputStream(samplerate=sample_rate, blocksize=4000, dtype="int16",
                               channels=1, callback=callback):
            import time
            end = time.monotonic() + max(1, float(timeout))
            while time.monotonic() < end:
                try:
                    chunk = audio_queue.get(timeout=0.25)
                except queue.Empty:
                    continue
                if recognizer.AcceptWaveform(chunk):
                    text = json.loads(recognizer.Result()).get("text", "").strip()
                    if text:
                        return text
            final = json.loads(recognizer.FinalResult()).get("text", "").strip()
            if final:
                return final
            partial = json.loads(recognizer.PartialResult()).get("partial", "").strip()
            if partial:
                return partial
    except Exception as exc:
        raise RuntimeError(f"Offline microphone capture failed: {exc}") from exc
    raise RuntimeError("No speech recognized. Check the microphone and Vosk model language.")
