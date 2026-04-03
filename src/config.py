from pathlib import Path

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

for path in [RAW_DIR, SAMPLES_DIR, ANONYMIZED_DIR, METRICS_DIR, LOGS_DIR]:
    path.mkdir(parents=True, exist_ok=True)