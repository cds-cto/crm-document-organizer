from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict

# Services
from src.services.gpt_services import GPTServices
from src.services.google_services import GoogleOCRService
from src.services.logging_services import setup_logger
from src.services.config_loader_services import config_loader
from src.knowledges import prompt2

class CrmDocumentOrganizerService:
    def __init__(
        self,
        *,
        project_id: str = config_loader.get("GCP", "project_id", "GCP_PROJECT_ID"),
        location: str = config_loader.get("GCP", "location", "GCP_LOCATION", "us"),
        processor_id: str = config_loader.get("GCP", "processor_id", "GCP_PROCESSOR_ID"),
        bucket_name: str = config_loader.get("GCP", "bucket_name", "GCP_BUCKET_NAME"),
        logger=None,
    ) -> None:
        self.logger = logger or setup_logger(self.__class__.__name__)
        self._gpt = GPTServices()
        self._ocr = GoogleOCRService(
            project_id=project_id,
            location=location,
            processor_id=processor_id,
            bucket_name=bucket_name,
        )

    def run_ocr(self, file_bytes: bytes, file_name: str) -> str:
        try:
            self.logger.info("OCR %s", file_name)
            text = self._ocr.extract_text_from_bytes(file_bytes, file_name)
            self.logger.debug("OCR extracted %d chars", len(text))
            return text
        except Exception as e:
            self.logger.error("OCR failed for %s: %s", file_name, str(e), exc_info=True)
            raise

    def classify_category(self, ocr_text: str) -> Dict[str, Any]:
        try:
            result = self._gpt.gpt_services(
                text=ocr_text,
                model="gpt-4.1",
                prompt=prompt2.CATEGORIZING_PROMPT,
                temperature=0.1,
            )
            return result
        except Exception as e:
            self.logger.error("Category classification failed: %s", str(e), exc_info=True)
            raise

    def categorize_document(self, file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        self.logger.info("Categorizing document: %s", file_name)
        ocr_text = self.run_ocr(file_bytes, file_name)
        self.logger.info("Text extracted from document: %s", ocr_text[:100] + "...")  # Log first 100 chars
        category_info = self.classify_category(ocr_text)
        self.logger.info("Document categorized successfully.")
        return category_info

def categorizing_document(
    file_bytes: bytes,
    file_name: str,
) -> Dict[str, Any]:
    """
    High-level function to categorize a document.
    """
    service = CrmDocumentOrganizerService()
    return service.categorize_document(file_bytes, file_name)
