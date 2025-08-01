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
from src.knowledges import prompt as prompt
from src.services.document_categorizing_services import DocumentCategorizingService, categorizing_document
from src.services.sql_find_services import MSSQLConnect, MSSQLProfileFinder

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
        self.document_categorizing_service = DocumentCategorizingService(
            project_id=project_id,
            location=location,
            processor_id=processor_id,
            bucket_name=bucket_name,
            logger=self.logger
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

    def categorizing_document(self, file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        self.logger.info("Categorizing document: %s", file_name)
        category_info = self.document_categorizing_service.categorize_document(file_bytes, file_name)
        self.logger.info("Document categorized successfully.")
        return category_info
    
    def info_grab(self, file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        info_grab = self._gpt.gpt_services(
            text=file_bytes,
            model="gpt-4.1",
            prompt=prompt.INFO_GRAB_PROMPT,
            temperature=0.1,
        )
        return info_grab
    

    def FindProfileandLiability(
            self, 
            lastname: str, 
            firstname: str, 
            reference_number: str, 
            file_number: str, 
            last4_account_number: str, 
            full_account_number: str, 
            first_12_account_number: str, 
            first_8_account_number: str, 
            email: str, 
            last4_ssn: str
        ) -> Dict[str, Any]:
        self.logger.info("Initializing DB connection...")
        db = MSSQLConnect()
        finder = MSSQLProfileFinder(db)

        try:
            self.logger.info("Testing Profile Finder with sample input...\n")
            test_data = {
                "LastName": lastname,
                "FirstName": firstname,
                "ReferenceNumber": reference_number,
                "FileNumber": file_number,                
                "Last4AccountNumber": last4_account_number,    
                "FullAccountNumber": full_account_number,
                "First12AccountNumber": first_12_account_number,
                "First8AccountNumber": first_8_account_number,
                "Email": email,
                "Last4SSN": last4_ssn,
            }
            result = finder.find_best_match(test_data)
            return result

        except Exception as e:
            return {"Error": str(e)}
        finally:
            finder.close()
            self.logger.info("Connection closed.")


    def document_organizer(self, file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        self.logger.info("Organizing document: %s", file_name)
        ocr_text = self.run_ocr(file_bytes, file_name)
        category_info = self.categorizing_document(file_bytes, file_name)
        info_grab = self.info_grab(ocr_text, file_name)
        lastname = info_grab.get("LastName", "")
        firstname = info_grab.get("FirstName", "")
        reference_number = info_grab.get("ReferenceNumber", "")
        file_number = info_grab.get("FileNumber", "")
        last4_account_number = info_grab.get("Last4AccountNumber", "")
        full_account_number = info_grab.get("FullAccountNumber", "")
        first12_account_number = info_grab.get("First12AccountNumber", "")
        first8_account_number = info_grab.get("First8AccountNumber", "")
        email = info_grab.get("Email", "")
        last4_ssn = info_grab.get("Last4SSN", "")
        account = self.FindProfileandLiability(
            lastname, 
            firstname, 
            reference_number, 
            file_number, 
            last4_account_number, 
            full_account_number, 
            first12_account_number, 
            first8_account_number, 
            email, 
            last4_ssn)
        info = {
            "LastName": lastname,
            "FirstName": firstname,
            "ReferenceNumber": reference_number,
            "FileNumber": file_number,
            "Last4AccountNumber": last4_account_number,
            "FullAccountNumber": full_account_number,
            "First12AccountNumber": first12_account_number,
            "First8AccountNumber": first8_account_number,
            "Email": email,
            "Last4SSN": last4_ssn
        }
        result = {
            "category_info": category_info,
            "info_grab": info,
            "account": account
        }
        
        self.logger.info("Document organized successfully.")
        return result
    
def organizing_document(
    file_bytes: bytes,
    file_name: str,
) -> Dict[str, Any]:
    service = CrmDocumentOrganizerService()
    return service.document_organizer(file_bytes, file_name)


