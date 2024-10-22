# PII Removal imports.
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
import re


def remove_pii(text):
    # Initialize Presidio engines for PII detection and anonymization
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()

    # Step 1: Analyze the text for PII entities
    results = analyzer.analyze(text=text, entities=[], language="en")

    # Anonymize the text based on detected PII and the anonymization configuration
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)

    # Extract the anonymized text from the EngineResult object
    anonymized_text = anonymized_result.text

    pii_pattern = r"<(.*?)>"
    matches = re.findall(pii_pattern, anonymized_text)
    pii_count = len(matches)

    return {"updated_text": anonymized_text, "pii_count": pii_count}
