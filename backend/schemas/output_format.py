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

# backend/schemas/output_format.py (Chunk 2: Spatial & Hazard Schemas)

class BoundingBox(BaseModel):
    """Normalized coordinates [0.0 - 1.0] for live overlay bounding boxes."""
    ymin: float = Field(..., ge=0.0, le=1.0, description="Top edge ratio")
    xmin: float = Field(..., ge=0.0, le=1.0, description="Left edge ratio")
    ymax: float = Field(..., ge=0.0, le=1.0, description="Bottom edge ratio")
    xmax: float = Field(..., ge=0.0, le=1.0, description="Right edge ratio")


class DetectedComponent(BaseModel):
    """Represents a discrete hardware component identified in the frame."""
    component_id: str = Field(..., description="Unique identifier for tracking across frames (e.g., R1, IC1, LED_RED)")
    name: str = Field(..., description="Component label (e.g., LM358 Op-Amp, 220 Ohm Resistor)")
    location_description: str = Field(..., description="Human-readable pin/rail placement (e.g., Pins 1-3, Rail A)")
    bounding_box: Optional[BoundingBox] = Field(None, description="Spatial coordinates for live bounding overlays")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model certainty score for identification")


class CircuitHazard(BaseModel):
    """Detailed record of a safety hazard or incorrect wiring setup."""
    hazard_id: str = Field(..., description="Unique issue code (e.g., HAZ_001)")
    category: HazardCategory = Field(..., description="Specific failure category")
    severity: RiskLevel = Field(..., description="Risk level associated with this hazard")
    title: str = Field(..., description="Short hazard heading (e.g., Direct VCC to GND Short)")
    explanation: str = Field(..., description="Engineering explanation of why this connection is dangerous")
    affected_components: List[str] = Field(default_factory=list, description="IDs or names of involved components")
    bounding_box: Optional[BoundingBox] = Field(None, description="Spatial location of the hazard on the breadboard")

# backend/schemas/output_format.py (Chunk 3: Stream Metadata & Response Payload)

class StreamTelemetry(BaseModel):
    """Metadata tailored for continuous frame-by-frame live camera feeds."""
    frame_status: FrameStatus = Field(default=FrameStatus.OK, description="Optical quality assessment of the frame")
    requires_power_kill: bool = Field(False, description="Emergency flag: True if power should be disconnected immediately")
    stable_inspection: bool = Field(True, description="False if camera movement caused low-confidence analysis")


class CircuitAnalysisResponse(BaseModel):
    """Root response model returned by /api/analyze."""
    circuit_type: str = Field(..., description="Identified circuit topology (e.g., Non-Inverting Op-Amp, Inverting Amp, LED Driver)")
    overall_safety: RiskLevel = Field(..., description="Highest risk level present in the inspected setup")
    summary: str = Field(..., description="Executive summary of the safety and wiring analysis")
    
    # Real-time / Live feed specific telemetry
    telemetry: StreamTelemetry = Field(default_factory=StreamTelemetry, description="Live camera feed quality and emergency flags")
    
    # Detailed inspection arrays
    components_detected: List[DetectedComponent] = Field(default_factory=list, description="List of recognized circuit components")
    hazards_and_violations: List[CircuitHazard] = Field(default_factory=list, description="List of detected safety hazards")
    recommendations: List[str] = Field(default_factory=list, description="Ordered step-by-step physical corrections for the user")