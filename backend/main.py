import io
import json
import logging
from typing import Dict, Any, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from json_repair import repair_json
import ollama

from schemas.output_format import CircuitAnalysisResponse
from prompts.circuit_rules import SYSTEM_PROMPT
from prompts.few_shot_examples import RESISTOR_IMG, LED_IMG

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

# Initialize asynchronous Ollama client
ollama_client = ollama.AsyncClient()


async def validate_image_file(image: UploadFile) -> bytes:
    """
    Validates uploaded image MIME type, payload size, and image integrity.
    """
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{image.content_type}'. Allowed types: JPEG, PNG, WEBP."
        )

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

    try:
        pil_image = Image.open(io.BytesIO(contents))
        pil_image.verify()
        
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


def sanitize_model_payload(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensively inspects and patches missing schema keys returned by the LLM
    before handing the dictionary to Pydantic for validation.
    """
    # 1. Ensure components_detected exists and is a list
    components = parsed_data.get("components_detected")
    if isinstance(components, list):
        for comp in components:
            if isinstance(comp, dict):
                # Ensure confidence field exists (fallback to default 0.70)
                if "confidence" not in comp or comp["confidence"] is None:
                    comp["confidence"] = 0.70
                else:
                    # Clamp confidence float to [0.0, 1.0]
                    try:
                        comp["confidence"] = max(0.0, min(1.0, float(comp["confidence"])))
                    except (ValueError, TypeError):
                        comp["confidence"] = 0.70

                # Guarantee component_id string fallback
                if "component_id" not in comp or not comp["component_id"]:
                    comp["component_id"] = f"COMP_{id(comp) % 1000}"

    # 2. Ensure telemetry block defaults exist
    if "telemetry" not in parsed_data or not isinstance(parsed_data["telemetry"], dict):
        parsed_data["telemetry"] = {
            "frame_status": "OK",
            "requires_power_kill": False,
            "stable_inspection": True
        }

    return parsed_data


@app.get("/")
def read_root() -> Dict[str, str]:
    return {"status": "online", "service": "CircuitMentor Engine"}


@app.post("/api/analyze", response_model=CircuitAnalysisResponse)
async def analyze_circuit(
    image: UploadFile = File(...),
    description: str = Form(default="Check this circuit setup for safety and wiring issues.")
):
    # 1. Execute Input Validation
    image_bytes = await validate_image_file(image)
    cleaned_description = sanitize_description(description)

    # 2. Build Multimodal Conversation Payload with Reference Grounding
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    if RESISTOR_IMG:
        messages.extend([
            {
                "role": "user",
                "content": "Reference Example A: This visual pattern (axial cylinder, wire leads, color bands) is a Resistor.",
                "images": [RESISTOR_IMG]
            },
            {
                "role": "assistant",
                "content": "Acknowledged. I will recognize axial bodies with color bands as Resistors."
            }
        ])

    if LED_IMG:
        messages.extend([
            {
                "role": "user",
                "content": "Reference Example B: This visual pattern (colored plastic dome with two leads) is an LED.",
                "images": [LED_IMG]
            },
            {
                "role": "assistant",
                "content": "Acknowledged. I will recognize colored plastic domes as LEDs."
            }
        ])

    messages.append({
        "role": "user",
        "content": f"User Circuit Notes: {cleaned_description}",
        "images": [image_bytes]
    })

    # 3. Execute Async Inference via Ollama
    try:
        response = await ollama_client.chat(
            model=MODEL_NAME,
            messages=messages,
            format=CircuitAnalysisResponse.model_json_schema(),
            options={
                "num_predict": 2048,
                "temperature": 0.2,
            }
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

    # 4. Parse and Validate Model Output
    try:
        raw_json = response["message"]["content"].strip()
        logger.info(f"RAW MODEL OUTPUT:\n{raw_json}")

        if raw_json.startswith("```json"):
            raw_json = raw_json[7:]
        elif raw_json.startswith("```"):
            raw_json = raw_json[3:]
        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]
        
        raw_json = raw_json.strip()

        try:
            parsed_data = json.loads(raw_json)
        except json.JSONDecodeError as decode_err:
            logger.warning(f"Standard JSON decode failed: {str(decode_err)}. Attempting repair_json fallback...")
            repaired_str = repair_json(raw_json)
            parsed_data = json.loads(repaired_str)

        # Sanitize and inject missing component fields before schema mapping
        sanitized_data = sanitize_model_payload(parsed_data)

        return CircuitAnalysisResponse(**sanitized_data)

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Model returned invalid JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Model output failed JSON parsing after repair attempt."
        )
    except Exception as e:
        logger.error(f"Schema validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema mapping error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)