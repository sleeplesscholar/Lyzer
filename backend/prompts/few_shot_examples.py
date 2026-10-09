# backend/prompts/few_shot_examples.py
import os

REF_DIR = os.path.join(os.path.dirname(__file__), "reference_images")

def load_reference_image(filename: str) -> bytes:
    path = os.path.join(REF_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return b""

# Load reference image bytes
RESISTOR_IMG = load_reference_image("test_resistor.jpg")
LED_IMG = load_reference_image("test_led.jpg")

FEW_SHOT_EXAMPLES = """
### GUIDANCE FOR DISCRETE BREADBOARD COMPONENTS:

Example 1: Basic LED and Resistor Setup
If you see a small cylindrical body with color bands and wire leads, identify it strictly as a Resistor.
If you see a small colored plastic dome (red, green, blue) with two legs, identify it strictly as an LED.

Expected output structure for a simple LED circuit:
"components_detected": [
  {
    "component_id": "R1",
    "name": "Resistor",
    "location_description": "Connected across breadboard rows",
    "bounding_box": {"ymin": 0.45, "xmin": 0.35, "ymax": 0.55, "xmax": 0.48},
    "confidence": 0.85
  },
  {
    "component_id": "LED1",
    "name": "Red LED",
    "location_description": "Connected near the resistor on the rail",
    "bounding_box": {"ymin": 0.48, "xmin": 0.50, "ymax": 0.60, "xmax": 0.58},
    "confidence": 0.90
  }
]
"""