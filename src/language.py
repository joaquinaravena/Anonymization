from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

from config import (
    DEFAULT_LANGUAGE,
    LANGUAGE_TO_SPACY_MODEL,
    MIN_CHARS_FOR_DETECTION,
)

DetectorFactory.seed = 0

_SUPPORTED = frozenset(LANGUAGE_TO_SPACY_MODEL.keys())


def _resolve_to_supported(raw: str) -> str | None:
    if raw in _SUPPORTED:
        return raw
    primary = raw.split("-", 1)[0]
    if primary in _SUPPORTED:
        return primary
    return None


def detect_mail_language(text: str) -> str:
    if not text or len(text.strip()) < MIN_CHARS_FOR_DETECTION:
        return DEFAULT_LANGUAGE
    try:
        raw = detect(text)
    except LangDetectException:
        return DEFAULT_LANGUAGE
    except Exception:
        return DEFAULT_LANGUAGE
    resolved = _resolve_to_supported(raw)
    return resolved if resolved is not None else DEFAULT_LANGUAGE
