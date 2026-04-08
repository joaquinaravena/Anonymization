import csv

from config import METRICS_CSV_FIELDS, RAW_DIR, METRICS_DIR
from pipeline import PIIPipeline

def load_mail_files():
    files = sorted(RAW_DIR.glob("*.txt"))
    return [(f.stem, f.read_text(encoding="utf-8")) for f in files]

def save_metrics(records):
    metrics_file = METRICS_DIR / "metrics.csv"

    with metrics_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=METRICS_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            row = {k: rec.get(k, "") for k in METRICS_CSV_FIELDS}
            writer.writerow(row)

    return metrics_file

def main():
    pipeline = PIIPipeline()

    records = []
    for mail_id, text in load_mail_files():
        records.append(pipeline.process_mail(mail_id, text))

    metrics_path = save_metrics(records)

if __name__ == "__main__":
    main()