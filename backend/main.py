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