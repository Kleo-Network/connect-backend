# PII Removal imports.
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
import re


def remove_pii(text):
    # Initialize Presidio engines for PII detection and anonymization
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()

    # For adding CUSTOM pattern to detect
    # time_pattern = Pattern(
    #     name="time_pattern",
    #     regex="(1[0-2]|0?[1-9]):[0-5][0-9] (AM|PM)",
    #     score=1
    # )
    # time_recognizer = PatternRecognizer(supported_entity='TIME', patterns=[time_pattern])
    # analyzer.registry.add_recognizer(time_recognizer)

    # Step 1: Analyze the text for PII entities
    results = analyzer.analyze(text=text, entities=[], language="en")

    # Anonymize the text based on detected PII and the anonymization configuration
    anonymized_text = anonymizer.anonymize(text=text, analyzer_results=results)

    updated_text = anonymized_text.text
    pii_pattern = r"<(.*?)>"
    matches = re.findall(pii_pattern, anonymized_text)
    pii_count = len(matches)

    return {updated_text, pii_count}
