
from fastapi import APIRouter, UploadFile, HTTPException
from app.services.pdf_extraction import extract_pdf_data

router = APIRouter()

@router.post("/")
async def upload_pdf(file: UploadFile):
    return extract_pdf_data(file)
