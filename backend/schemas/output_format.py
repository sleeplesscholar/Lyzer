from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Categorizes overall and individual hazard severity levels."""
    SAFE = "SAFE"
    WARNING = "WARNING"
    DANGER = "DANGER"
    UNKNOWN = "UNKNOWN"


class FrameStatus(str, Enum):
    """Indicates real-time optical/frame quality for live feeds."""
    OK = "OK"
    BLURRY = "BLURRY"
    POOR_LIGHTING = "POOR_LIGHTING"
    PARTIALLY_OCCLUDED = "PARTIALLY_OCCLUDED"


class HazardCategory(str, Enum):
    """Domain-specific electronics failure modes."""
    SHORT_CIRCUIT = "SHORT_CIRCUIT"
    REVERSED_POLARITY = "REVERSED_POLARITY"
    FLOATING_INPUT = "FLOATING_INPUT"
    MISSING_COMPONENT = "MISSING_COMPONENT"
    EXCEEDED_RATING = "EXCEEDED_RATING"
    UNGROUNDED = "UNGROUNDED"
    OTHER = "OTHER"