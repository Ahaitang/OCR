"""
OCR API Router
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import List, Optional
import base64

from app.services.ocr_service import parse_images


router = APIRouter()


@router.post("/parse")
async def parse_image(
    images: Optional[List[str]] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """Parse medical record images with OCR"""
    all_images = []

    # Handle base64 encoded images
    if images:
        all_images.extend(images)

    # Handle uploaded files
    if files:
        for f in files:
            content = await f.read()
            all_images.append(base64.b64encode(content).decode('utf-8'))

    if not all_images:
        raise HTTPException(status_code=400, detail="No images provided")

    result = parse_images(all_images)

    return {
        "code": 200,
        "message": "success",
        "data": result
    }