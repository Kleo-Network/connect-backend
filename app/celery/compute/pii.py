# PII Removal imports.
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
import re


def remove_pii(text):
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()

    results = analyzer.analyze(text=text, entities=[], language="en")

    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)

    anonymized_text = anonymized_result.text

    pii_pattern = r"<(.*?)>"
    matches = re.findall(pii_pattern, anonymized_text)
    pii_count = len(matches)

    return {"updated_text": anonymized_text, "pii_count": pii_count}
