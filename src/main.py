import csv
from pathlib import Path

from config import RAW_DIR, METRICS_DIR
from logger_setup import setup_logger
from pipeline import PIIPipeline

def load_mail_files():
    files = sorted(RAW_DIR.glob("*.txt"))
    return [(f.stem, f.read_text(encoding="utf-8")) for f in files]

def save_metrics(records):
    metrics_file = METRICS_DIR / "metrics.csv"
    fieldnames = sorted({key for record in records for key in record.keys()})

    with metrics_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return metrics_file

def main():
    logger = setup_logger(log_file=Path("logs") / "app.log")
    pipeline = PIIPipeline(logger)

    records = []
    for mail_id, text in load_mail_files():
        records.append(pipeline.process_mail(mail_id, text))

    metrics_path = save_metrics(records)
    logger.info(f"Metrics saved to {metrics_path}")

if __name__ == "__main__":
    main()