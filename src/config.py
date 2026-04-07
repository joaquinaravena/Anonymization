from pathlib import Path

# Presidio loads one spaCy model per key; add languages here and install the matching package.
# Without a French model, detection falls back to English and PERSON often misses French text.
# Use a *core* French model (e.g. fr_core_news_md) — fr_dep_* packages have no NER pipe, so Presidio
# will not detect PERSON/LOCATION at all.
LANGUAGE_TO_SPACY_MODEL = {
    "en": "en_core_web_trf",
    "fr": "fr_core_news_md",
}

DEFAULT_LANGUAGE = "en"

# Skip langdetect below this length (empty/small snippets are unreliable).
MIN_CHARS_FOR_DETECTION = 40

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
SAMPLES_DIR = DATA_DIR / "samples"
OUTPUTS_DIR = BASE_DIR / "outputs"
ANONYMIZED_DIR = OUTPUTS_DIR / "anonymized"
METRICS_DIR = OUTPUTS_DIR / "metrics"
LOGS_DIR = BASE_DIR / "logs"

ENTITIES = [
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "PERSON",
    "LOCATION",
    "CREDIT_CARD",
    "DATE_TIME",
    "URL",
    "ACCOUNT_NUMBER",
    "ADDRESS",
]

# rapidfuzz ratio 0–100 for PERSON vs known name aliases.
USER_ONLY_FUZZY_MATCH_THRESHOLD = 85
USER_ONLY_MIN_NAME_TOKEN_LEN = 2

# Header names (normalized) whose lines may contain recipient-only redaction.
USER_ONLY_REDACT_HEADERS = ("to", "cc")

# If no recipient identity can be built, anonymize all Presidio hits (safer than storing raw text).
ANONYMIZE_ALL_IF_NO_IDENTITY = True

# CSV column order for metrics (one row per mail). Excludes full anonymized body — see output_file.
METRICS_CSV_FIELDS = [
    "mail_id",
    "success",
    "language",
    "analyzer_hits",
    "redacted_spans",
    "identity_empty",
    "processing_time_sec",
    "output_file",
    "error",
]

for path in [RAW_DIR, SAMPLES_DIR, ANONYMIZED_DIR, METRICS_DIR, LOGS_DIR]:
    path.mkdir(parents=True, exist_ok=True)