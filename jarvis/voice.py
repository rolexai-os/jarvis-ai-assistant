"""Opt-in wake-word and clap detection. Microphone monitoring never starts automatically."""
from __future__ import annotations

import time
from threading import Lock


class VoiceController:
    def __init__(self, wake_word="jarvis", clap_threshold=0.18, clap_cooldown=1.2):
        self.wake_word = wake_word.casefold()
        self.clap_threshold = float(clap_threshold)
        self.clap_cooldown = float(clap_cooldown)
        self._recognizer = None
        self._microphone = None
        self._stop_listening = None
        self._clap_stream = None
        self._last_clap = 0.0
        self._awake_until = 0.0
        self._lock = Lock()

    @property
    def wake_active(self):
        return self._stop_listening is not None

    @property
    def clap_active(self):
        return self._clap_stream is not None

    def start_wake_word(self, on_command, on_status=None):
        """Listen for 'JARVIS' in short phrases. Google recognition requires internet."""
        if self._stop_listening:
            return
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
            def received(_recognizer, audio):
                try:
                    phrase = recognizer.recognize_google(audio).strip()
                except (sr.UnknownValueError, sr.RequestError):
                    return
                low = phrase.casefold()
                with self._lock:
                    is_awake = time.monotonic() <= self._awake_until
                    if self.wake_word in low:
                        after = low.split(self.wake_word, 1)[1].strip(" ,.!?:;")
                        self._awake_until = time.monotonic() + 8.0
                        if after:
                            on_command(after)
                        else:
                            on_command("__WAKE__")
                    elif is_awake:
                        self._awake_until = 0.0
                        on_command(phrase)
            self._recognizer, self._microphone = recognizer, microphone
            self._stop_listening = recognizer.listen_in_background(microphone, received, phrase_time_limit=6)
            if on_status:
                on_status("Wake-word listening is ON. Say 'JARVIS' then a command.")
        except Exception as exc:
            self._stop_listening = None
            if on_status:
                on_status(f"Wake-word unavailable: {exc}")

    def stop_wake_word(self, on_status=None):
        stop, self._stop_listening = self._stop_listening, None
        if stop:
            try:
                stop(wait_for_stop=False)
            except Exception:
                pass
        self._recognizer = self._microphone = None
        if on_status:
            on_status("Wake-word listening is OFF.")

    def start_clap_detection(self, on_clap, on_status=None):
        """Detect a sharp loud sound by RMS threshold. Calibrate for room noise."""
        if self._clap_stream:
            return
        try:
            import numpy as np
            import sounddevice as sd
            def audio_callback(indata, frames, time_info, status):
                if status:
                    pass
                rms = float(np.sqrt(np.mean(np.square(indata.astype("float32")))))
                now = time.monotonic()
                if rms >= self.clap_threshold and now - self._last_clap >= self.clap_cooldown:
                    self._last_clap = now
                    on_clap()
            self._clap_stream = sd.InputStream(
                channels=1, samplerate=16000, blocksize=1024,
                dtype="float32", callback=audio_callback
            )
            self._clap_stream.start()
            if on_status:
                on_status("Clap detection is ON. A loud clap brings JARVIS to the foreground.")
        except Exception as exc:
            self._clap_stream = None
            if on_status:
                on_status(f"Clap detection unavailable: {exc}")

    def stop_clap_detection(self, on_status=None):
        stream, self._clap_stream = self._clap_stream, None
        if stream:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        if on_status:
            on_status("Clap detection is OFF.")


def listen_once(timeout=5, phrase_time_limit=8):
    try:
        import speech_recognition as sr
    except ImportError as exc:
        raise RuntimeError("Install SpeechRecognition and PyAudio for microphone input.") from exc
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.35)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError as exc:
        raise RuntimeError("I couldn't understand that. Try again.") from exc
    except sr.RequestError as exc:
        raise RuntimeError("Online speech service unavailable; check your connection.") from exc


def speak(text, rate=175):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as exc:
        raise RuntimeError(f"Text-to-speech unavailable: {exc}") from exc
