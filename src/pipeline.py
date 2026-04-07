import time
import json
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

from config import (
    BASE_DIR,
    ENTITIES,
    ANONYMIZED_DIR,
    LANGUAGE_TO_SPACY_MODEL,
)
from language import resolve_analyzer_language
from recognizers import build_custom_recognizers
from user_identity import build_user_identity
from user_only_filter import filter_user_only_results


def _build_analyzer_engine():
    models = [
        {"lang_code": lang, "model_name": model_name}
        for lang, model_name in sorted(LANGUAGE_TO_SPACY_MODEL.items())
    ]
    nlp_configuration = {
        "nlp_engine_name": "spacy",
        "models": models,
    }
    provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
    nlp_engine = provider.create_engine()
    supported_languages = sorted(LANGUAGE_TO_SPACY_MODEL.keys())
    return AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=supported_languages,
    )


class PIIPipeline:
    def __init__(self, logger):
        self.logger = logger
        self.analyzer = _build_analyzer_engine()
        for recognizer in build_custom_recognizers():
            self.analyzer.registry.add_recognizer(recognizer)
        self.anonymizer = AnonymizerEngine()

    @staticmethod
    def _output_path_for_metrics(path) -> str:
        try:
            return str(path.relative_to(BASE_DIR))
        except ValueError:
            return str(path)

    def analyze(self, text, language=None):
        if language is None:
            language, _detected_language = resolve_analyzer_language(text)
        return self.analyzer.analyze(
            text=text,
            entities=ENTITIES,
            language=language,
        )

    def anonymize(self, text, results):
        return self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
        )

    def _results_for_anonymization(self, text, results):
        """Keep only recipient-related spans."""
        all_hits = len(results)
        identity = build_user_identity(text)

        if identity.is_empty():
            return [], 0, all_hits, identity

        filtered = filter_user_only_results(text, results, identity)
        return filtered, len(filtered), all_hits, identity

    def process_mail(self, mail_id, text):
        started = time.time()
        language = None
        detected_language = None

        try:
            language, detected_language = resolve_analyzer_language(text)
            results = self.analyze(text, language=language)
            to_anonymize, kept_hits, all_hits, identity = self._results_for_anonymization(
                text, results
            )
            anonymized = self.anonymize(text, to_anonymize)

            output_path = ANONYMIZED_DIR / f"{mail_id}.txt"
            output_path.write_text(anonymized.text, encoding="utf-8")

            duration = time.time() - started

            # analyzer_hits: Presidio detections before filtering.
            # redacted_spans: spans passed to the anonymizer after recipient-only filtering.
            record = {
                "mail_id": mail_id,
                "success": True,
                "language_detected": detected_language,
                "language": language,
                "analyzer_hits": all_hits,
                "redacted_spans": kept_hits,
                "redaction_ratio": round((kept_hits / all_hits), 4) if all_hits else 0.0,
                "identity_empty": identity.is_empty(),
                "identity_source": identity.source(),
                "processing_time_sec": round(duration, 4),
                "output_file": self._output_path_for_metrics(output_path),
            }

            self.logger.info(json.dumps(record, ensure_ascii=False))
            return record

        except Exception as e:
            duration = time.time() - started
            record = {
                "mail_id": mail_id,
                "success": False,
                "language_detected": detected_language,
                "language": language,
                "redaction_ratio": "",
                "identity_source": "",
                "processing_time_sec": round(duration, 4),
                "error": str(e),
            }
            self.logger.error(json.dumps(record, ensure_ascii=False))
            return record