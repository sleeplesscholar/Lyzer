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
from prompts.few_shot_examples import (
    RESISTOR_IMG,
    LED_IMG,
    ELECTROLYTIC_CAP_IMG,
    CERAMIC_CAP_IMG,
    POTENTIOMETER_IMG,
)
from services.safety_rules import evaluate_electrical_rules

# Set up logging for server-side error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CircuitMentor")

app = FastAPI(
    title="CircuitMentor API",
    description="Backend service for multimodal breadboard and schematic analysis.",
    version="0.2.0"
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


async def validate_and_process_image(image: UploadFile, max_dimension: int = 1024) -> bytes:
    """
    Validates uploaded image MIME type/size, downscales dimensions to prevent VRAM OOM,
    and returns optimized JPEG bytes for Ollama.
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
        
        # Re-open after verify() to process pixels
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Resize image proportionally if larger than max_dimension to keep vision context light
        pil_image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format="JPEG", quality=85)
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
    Defensively inspects and patches missing schema keys returned by the LLM,
    and runs deterministic electrical safety engine rules before Pydantic validation.
    """
    # 1. Guarantee top-level required fields against model truncation
    if not parsed_data.get("circuit_type"):
        parsed_data["circuit_type"] = "Breadboard Prototype Circuit"

    if not parsed_data.get("summary"):
        parsed_data["summary"] = (
            "Visual inspection completed. Partial analysis generated based on detected components."
        )

    if not parsed_data.get("overall_safety"):
        parsed_data["overall_safety"] = "SAFE"

    # 2. Ensure components_detected exists and patch component/bounding_box fields
    components = parsed_data.get("components_detected")
    if isinstance(components, list):
        for comp in components:
            if isinstance(comp, dict):
                # Guarantee name string fallback
                if "name" not in comp or not comp["name"]:
                    comp["name"] = "Unknown Component"

                # Guarantee location_description string fallback
                if "location_description" not in comp or not comp["location_description"]:
                    comp["location_description"] = "Location non-determinable due to partial image crop or model truncation."

                # Ensure confidence field exists (fallback to default 0.70)
                if "confidence" not in comp or comp["confidence"] is None:
                    comp["confidence"] = 0.70
                else:
                    try:
                        comp["confidence"] = max(0.0, min(1.0, float(comp["confidence"])))
                    except (ValueError, TypeError):
                        comp["confidence"] = 0.70

                # Guarantee component_id string fallback
                if "component_id" not in comp or not comp["component_id"]:
                    comp["component_id"] = f"COMP_{id(comp) % 1000}"

                # Patch incomplete or truncated bounding boxes
                bbox = comp.get("bounding_box")
                if not isinstance(bbox, dict):
                    comp["bounding_box"] = {"ymin": 0.0, "xmin": 0.0, "ymax": 0.0, "xmax": 0.0}
                else:
                    for axis in ["ymin", "xmin", "ymax", "xmax"]:
                        if axis not in bbox or bbox[axis] is None:
                            bbox[axis] = 0.0
                        else:
                            try:
                                bbox[axis] = max(0.0, min(1.0, float(bbox[axis])))
                            except (ValueError, TypeError):
                                bbox[axis] = 0.0
    else:
        parsed_data["components_detected"] = []

    # 3. Ensure telemetry block defaults exist
    if "telemetry" not in parsed_data or not isinstance(parsed_data["telemetry"], dict):
        parsed_data["telemetry"] = {
            "frame_status": "OK",
            "requires_power_kill": False,
            "stable_inspection": True
        }

    # 4. Ensure list structures exist
    if "hazards_and_violations" not in parsed_data or not isinstance(parsed_data["hazards_and_violations"], list):
        parsed_data["hazards_and_violations"] = []
    if "recommendations" not in parsed_data or not isinstance(parsed_data["recommendations"], list):
        parsed_data["recommendations"] = []

    # 5. Correct top-level topology hallucinations
    detected_names = [
        c.get("name", "").lower() 
        for c in parsed_data.get("components_detected", []) 
        if isinstance(c, dict)
    ]
    has_active_silicon = any(
        term in " ".join(detected_names) 
        for term in ["transistor", "ic", "op-amp", "mosfet", "timer"]
    )
    if not has_active_silicon and "driver" in parsed_data.get("circuit_type", "").lower():
        parsed_data["circuit_type"] = "Simple Passive Circuit"

    # 6. Apply Deterministic Electrical Safety Engine Rules
    parsed_data = evaluate_electrical_rules(parsed_data)

    return parsed_data


@app.get("/")
def read_root() -> Dict[str, str]:
    return {"status": "online", "service": "CircuitMentor Engine"}


@app.post("/api/analyze", response_model=CircuitAnalysisResponse)
async def analyze_circuit(
    image: UploadFile = File(...),
    description: str = Form(default="Check this circuit setup for safety and wiring issues.")
):
    # 1. Execute Input Validation & Thumbnail Resizing
    image_bytes = await validate_and_process_image(image, max_dimension=1024)
    cleaned_description = sanitize_description(description)

    # 2. Build Multimodal Conversation Payload with Reference Grounding
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # Include reference images conditionally if available
    if RESISTOR_IMG:
        messages.extend([
            {"role": "user", "content": "Reference Example: Resistor (axial cylinder, color bands).", "images": [RESISTOR_IMG]},
            {"role": "assistant", "content": "Acknowledged."}
        ])

    if LED_IMG:
        messages.extend([
            {"role": "user", "content": "Reference Example: LED (colored dome lens).", "images": [LED_IMG]},
            {"role": "assistant", "content": "Acknowledged."}
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
            format="json",
            options={
                "num_predict": 2048,  # Cap token length to prevent VRAM buffer overflow
                "num_ctx": 4096,      # Context window limit
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
        raw_content = response.get("message", {}).get("content", "")
        if not raw_content or not raw_content.strip():
            logger.error(f"Ollama returned an empty response string. Full response dict: {response}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Model returned an empty response string. Ensure Ollama daemon has sufficient VRAM."
            )

        raw_json = raw_content.strip()
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

        # Sanitize, patch missing fields, and evaluate safety rules
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


@app.post("/api/verify", response_model=CircuitAnalysisResponse)
async def verify_schematic_against_breadboard(
    schematic_image: UploadFile = File(...),
    breadboard_image: UploadFile = File(...),
    description: str = Form(default="Verify if the physical breadboard setup matches the schematic diagram.")
):
    schematic_bytes = await validate_and_process_image(schematic_image, max_dimension=1024)
    breadboard_bytes = await validate_and_process_image(breadboard_image, max_dimension=1024)
    cleaned_description = sanitize_description(description)

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"User Verification Task: {cleaned_description}\nImage 1 is the Reference Schematic. Image 2 is the Physical Breadboard Build. Compare the topology and report any missing, incorrectly placed, or unlisted components.",
            "images": [schematic_bytes, breadboard_bytes]
        }
    ]

    try:
        response = await ollama_client.chat(
            model=MODEL_NAME,
            messages=messages,
            format="json",
            options={
                "num_predict": 2048,
                "num_ctx": 4096,
                "temperature": 0.2,
            }
        )
    except Exception as e:
        logger.error(f"Failed during dual-image verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during schematic vs breadboard verification."
        )

    raw_content = response.get("message", {}).get("content", "").strip()
    if not raw_content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Model returned an empty response during dual-image verification."
        )

    if raw_content.startswith("```json"):
        raw_content = raw_content[7:]
    elif raw_content.startswith("```"):
        raw_content = raw_content[3:]
    if raw_content.endswith("```"):
        raw_content = raw_content[:-3]
    
    raw_content = raw_content.strip()

    try:
        parsed_data = json.loads(raw_content)
    except json.JSONDecodeError:
        repaired_str = repair_json(raw_content)
        parsed_data = json.loads(repaired_str)

    sanitized_data = sanitize_model_payload(parsed_data)
    return CircuitAnalysisResponse(**sanitized_data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)