import io
import json
import logging
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
import ollama

from schemas.output_format import CircuitAnalysisResponse
from prompts.circuit_rules import SYSTEM_PROMPT

# Set up logging for server-side error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CircuitMentor")

app = FastAPI(
    title="CircuitMentor API",
    description="Backend service for multimodal breadboard and schematic analysis.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = "gemma4:12b"
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

async def validate_image_file(image: UploadFile) -> bytes:
    """
    Validates uploaded image MIME type, payload size, and image integrity.
    """
    # 1. Check MIME type header
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{image.content_type}'. Allowed types: JPEG, PNG, WEBP."
        )

    # 2. Read bytes and check payload size
    contents = await image.read()
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum threshold of {MAX_FILE_SIZE_MB}MB."
        )

    # 3. Verify image file integrity via Pillow
    try:
        pil_image = Image.open(io.BytesIO(contents))
        pil_image.verify()  # Verifies file header without decoding full image
        
        # Re-open after verify() to process bytes
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format="JPEG")
        return img_byte_arr.getvalue()

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted or invalid image file content."
        )
    except Exception as e:
        logger.error(f"Image processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to process uploaded image file."
        )


def sanitize_description(description: str) -> str:
    """
    Validates and cleans user circuit description text.
    """
    cleaned = description.strip()
    if len(cleaned) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Circuit description exceeds the maximum length of 2000 characters."
        )
    return cleaned if cleaned else "Check this circuit setup for safety and wiring issues."