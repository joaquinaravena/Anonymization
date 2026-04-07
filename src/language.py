from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

from config import (
    PRIMARY_ANALYZER_LANGUAGES,
    SHORT_TEXT_ANALYZER_LANGUAGE,
    MIN_CHARS_FOR_DETECTION,
)

DetectorFactory.seed = 0

def _normalize_detected_language(raw: str) -> str:
    return raw.split("-", 1)[0].lower()


def resolve_analyzer_language(text: str) -> tuple[str, str]:
    """
    Returns (analyzer_language, detected_language).
    analyzer_language is one of: en, fr, xx.
    """
    if not text or len(text.strip()) < MIN_CHARS_FOR_DETECTION:
        return SHORT_TEXT_ANALYZER_LANGUAGE, "short_text"
    try:
        raw = detect(text)
    except LangDetectException:
        return SHORT_TEXT_ANALYZER_LANGUAGE, "detect_error"
    except Exception:
        return SHORT_TEXT_ANALYZER_LANGUAGE, "detect_error"

    normalized = _normalize_detected_language(raw)
    if normalized in PRIMARY_ANALYZER_LANGUAGES:
        return normalized, normalized
    return "xx", normalized
