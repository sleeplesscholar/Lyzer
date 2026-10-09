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

MODEL_NAME = "gemma4:e2b"
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

@app.get("/")
def read_root() -> Dict[str, str]:
    return {"status": "online", "service": "CircuitMentor Engine"}


@app.post("/api/analyze", response_model=CircuitAnalysisResponse)
async def analyze_circuit(
    image: UploadFile = File(...),
    description: str = Form(default="Check this circuit setup for safety and wiring issues.")
):
    # Execute Input Validation
    image_bytes = await validate_image_file(image)
    cleaned_description = sanitize_description(description)

    # Execute Inference via Ollama
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"User Circuit Notes: {cleaned_description}",
                    "images": [image_bytes]
                }
            ],
            format=CircuitAnalysisResponse.model_json_schema()
        )

    except ollama.ResponseError as e:
        logger.error(f"Ollama response error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI model service error: {e.error}"
        )
    except Exception as e:
        logger.error(f"Failed to connect to Ollama daemon: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not reach local Ollama inference service. Ensure Ollama is running."
        )

    # Parse and Validate Model Output
    try:
        raw_json = response["message"]["content"]
        parsed_data = json.loads(raw_json)
        return CircuitAnalysisResponse(**parsed_data)

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Model returned invalid JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Model output failed structured JSON schema verification."
        )
    except Exception as e:
        logger.error(f"Schema mapping error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to format analysis response into schema."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

