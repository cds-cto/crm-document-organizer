# Import library
import io
import time
import os
from uuid import uuid4
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple, List
from pypdf import PdfReader, PdfWriter

#Import Google
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import ServiceUnavailable, DeadlineExceeded
from google.cloud import documentai_v1 as documentai
from google.cloud import storage

# Import other Services
from src.services.logging_services import setup_logger
from src.services.config_loader_services import config_loader

cred_path_cfg = config_loader.get("GCP", "key_file")       # e.g. polling-apps-…json
cred_path_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not cred_path_env and cred_path_cfg:
    kp = Path(cred_path_cfg).expanduser()
    if not kp.is_absolute() and config_loader._config_path:
        kp = (config_loader._config_path.parent / kp).resolve()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = kp.as_posix()

class GoogleOCRService:
    def __init__(
        self,
        *,
        project_id: str = config_loader.get("GCP", "project_id"),
        location: str = config_loader.get("GCP", "location", "us"),
        processor_id: str = config_loader.get("GCP", "processor_id"),
        bucket_name: str = config_loader.get("GCP", "bucket_name"),
    ) -> None:
        self.project_id   = project_id
        self.location     = location
        self.processor_id = processor_id
        self.bucket_name  = bucket_name

        self.logger = setup_logger(self.__class__.__name__)
        self.storage_client   = storage.Client()
        self.documentai_client = documentai.DocumentProcessorServiceClient(
            client_options=ClientOptions(
                api_endpoint=f"{self.location}-documentai.googleapis.com"
            )
        )

    # ── internal helper ─────────────────────────────────────────
    def _process_page(
        self, page_bytes: bytes, mime_type: str, page_index: int
    ) -> Tuple[int, str]:
        """
        Submit a single page to Document AI and return extracted text.
        """
        raw_document = documentai.RawDocument(
            content=page_bytes, mime_type=mime_type
        )
        request = documentai.ProcessRequest(
            name=self.documentai_client.processor_path(
                self.project_id, self.location, self.processor_id
            ),
            raw_document=raw_document,
            skip_human_review=True,
        )

        for attempt in range(3):
            try:
                result = self.documentai_client.process_document(request=request)
                return page_index, result.document.text.strip()
            except (ServiceUnavailable, DeadlineExceeded) as exc:
                wait = 2 ** attempt
                self.logger.warning(
                    "Page %s • attempt %s failed (%s) retrying in %ss",
                    page_index, attempt + 1, exc, wait,
                )
                time.sleep(wait)
            except Exception as exc:
                self.logger.error(
                    "Page %s • unexpected error: %s", page_index, exc, exc_info=True
                )
                break

        self.logger.warning("Page %s failed after retries.", page_index)
        return page_index, ""

    # ── public API ──────────────────────────────────────────────
    def extract_text_from_bytes(
        self, file_bytes: bytes, file_name: Optional[str] = None
    ) -> str:
        """
        Run OCR on PDF/image bytes and return combined text.
        Multi-page PDFs are processed in parallel.
        """
        file_name = file_name or f"{uuid4()}.pdf"
        ext = Path(file_name).suffix.lower()

        mime_map = {
            ".pdf":  "application/pdf",
            ".png":  "image/png",
            ".jpg":  "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        if ext not in mime_map:
            raise ValueError(
                f"Unsupported file type '{ext}'. Allowed: {', '.join(mime_map)}"
            )

        mime_type = mime_map[ext]
        self.logger.info("Running OCR on %s (%s bytes)", file_name, len(file_bytes))

        if ext != ".pdf":
            _, txt = self._process_page(file_bytes, mime_type, 0)
            return txt

        # Split PDF into pages and OCR in parallel
        pdf = PdfReader(io.BytesIO(file_bytes))
        results: List[str] = [""] * len(pdf.pages)
        with ThreadPoolExecutor() as pool:
            futures = []
            for idx, page in enumerate(pdf.pages):
                buf = io.BytesIO()
                writer = PdfWriter()
                writer.add_page(page)
                writer.write(buf)
                buf.seek(0)
                futures.append(
                    pool.submit(self._process_page, buf.read(), mime_type, idx)
                )

            for fut in as_completed(futures):
                i, txt = fut.result()
                results[i] = txt

        combined = "\n".join(filter(bool, results))
        self.logger.info("OCR complete, %s characters extracted", len(combined))
        return combined
