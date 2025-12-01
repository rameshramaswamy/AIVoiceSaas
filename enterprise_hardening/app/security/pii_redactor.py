import logging
from typing import List, Optional
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger("security")

class PIIRedactor:
    def __init__(self):
        # Initialize engines (loads Spacy NLP model)
        # This takes a few seconds, so it should be a Singleton in production
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # Define what entities we want to scrub
        self.entities = [
            "CREDIT_CARD", 
            "CRYPTO", 
            "EMAIL_ADDRESS", 
            "IBAN_CODE", 
            "IP_ADDRESS", 
            "PHONE_NUMBER", 
            "US_SSN",
            "US_DRIVER_LICENSE",
            "PERSON" # Use carefully, might redact Agent names
        ]

    def redact_text(self, text: str) -> str:
        """
        Scans text and replaces PII with <ENTITY_TYPE>.
        Example: "Call me at 555-0199" -> "Call me at <PHONE_NUMBER>"
        """
        if not text:
            return ""

        try:
            # 1. Analyze (Detect)
            results = self.analyzer.analyze(
                text=text,
                entities=self.entities,
                language='en'
            )

            # 2. Anonymize (Replace)
            # We replace with the entity type (e.g., <EMAIL>)
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators={
                    "DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"}),
                    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
                    "CREDIT_CARD": OperatorConfig("replace", {"new_value": "<CREDIT_CARD>"}),
                    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
                }
            )

            return anonymized_result.text

        except Exception as e:
            logger.error(f"PII Redaction failed: {e}")
            # Fail closed: If security fails, return raw text? 
            # Better to log error and return text, 
            # OR return "[REDACTION_ERROR]" to be safe.
            return text