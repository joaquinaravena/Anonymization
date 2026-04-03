import time
import json
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from config import ENTITIES, ANONYMIZED_DIR
from recognizers import build_custom_recognizers

class PIIPipeline:
    def __init__(self, logger):
        self.logger = logger
        self.analyzer = AnalyzerEngine()
        for recognizer in build_custom_recognizers():
            self.analyzer.registry.add_recognizer(recognizer)
        self.anonymizer = AnonymizerEngine()

    def analyze(self, text):
        return self.analyzer.analyze(
            text=text,
            entities=ENTITIES,
            language="en",
        )

    def anonymize(self, text, results):
        return self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
        )

    def process_mail(self, mail_id, text):
        started = time.time()

        try:
            results = self.analyze(text)
            anonymized = self.anonymize(text, results)

            output_path = ANONYMIZED_DIR / f"{mail_id}.txt"
            output_path.write_text(anonymized.text, encoding="utf-8")

            duration = time.time() - started

            record = {
                "mail_id": mail_id,
                "success": True,
                "processing_time_sec": round(duration, 4),
                "num_entities": len(results),
                "output_file": str(output_path),
                "anonymized_text": anonymized.text,
            }

            self.logger.info(json.dumps(record, ensure_ascii=False))
            return record

        except Exception as e:
            duration = time.time() - started
            record = {
                "mail_id": mail_id,
                "success": False,
                "processing_time_sec": round(duration, 4),
                "error": str(e),
            }
            self.logger.error(json.dumps(record, ensure_ascii=False))
            return record