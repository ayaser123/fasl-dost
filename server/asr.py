"""Speech-to-text via faster-whisper (optional dependency)."""
import os, tempfile

_model = None


def available() -> bool:
    try:
        import faster_whisper  # noqa
        return True
    except ImportError:
        return False


def transcribe(data: bytes, suffix: str = ".webm"):
    """Returns (text, detected_lang, language_probability)."""
    global _model
    from faster_whisper import WhisperModel
    if _model is None:
        _model = WhisperModel(os.getenv("FASL_WHISPER", "small"), compute_type="int8")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
    try:
        segs, info = _model.transcribe(f.name, task="transcribe",
                                       language=None, vad_filter=True)
        text = " ".join(s.text.strip() for s in segs).strip()
        return text, info.language, info.language_probability
    finally:
        os.unlink(f.name)
