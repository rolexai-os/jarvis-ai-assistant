"""Optional one-shot speech input and spoken output."""
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
