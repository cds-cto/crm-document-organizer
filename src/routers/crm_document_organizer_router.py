# Import fastapi
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
# from fastapi.concurrency import run_in_threadpool

# Import the convenience handler we just defined
from src.services import organizing_document


router = APIRouter(
    prefix="/api/organizer",
    tags=["Document Organization"],
)

@router.post("/process")
async def crm_document_organizer(
    file: UploadFile = File(...),
):
    file_bytes = await file.read()
    result = organizing_document(
        file_bytes=file_bytes,
        file_name=file.filename,
    )

    return JSONResponse(content=result)

