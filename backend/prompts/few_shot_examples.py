import os

REF_DIR = os.path.join(os.path.dirname(__file__), "reference_images")

def load_reference_image(filename: str) -> bytes:
    path = os.path.join(REF_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return b""

# Load reference image bytes for visual ground-truth prompting
RESISTOR_IMG = load_reference_image("test_resistor.jpg")
LED_IMG = load_reference_image("test_led.jpg")
ELECTROLYTIC_CAP_IMG = load_reference_image("test_electrolytic_capacitor.jpg")
CERAMIC_CAP_IMG = load_reference_image("test_ceramic_capacitor.jpg")
POTENTIOMETER_IMG = load_reference_image("test_potentiometer.jpg")

FEW_SHOT_EXAMPLES = """
### DISCRETE BREADBOARD COMPONENT IDENTIFICATION EXAMPLES:

Use these reference patterns to identify physical components plugged directly into breadboard tie-points:

1. **Resistor**: Small cylindrical body with four or five color code bands and axial wire leads.
- Example name: "Resistor" or "Current-Limiting Resistor"
- Do NOT guess resistance value unless color bands are crisp and unambiguous.

2. **LED (Light Emitting Diode)**: Small 3mm or 5mm clear or colored plastic dome with two leads (anode/cathode).
- Example name: "LED" or "Indicator LED"
- NOTE: Determine color ONLY from the plastic dome lens itself, NEVER from nearby knobs, wire insulation, or test leads. If color is ambiguous, use "LED".

3. **Electrolytic Capacitor**: Cylindrical metal/plastic can (typically black, blue, or silver) with a distinct vertical stripe indicating the negative (-) lead, standing vertically or lying horizontally.
- Example name: "Electrolytic Capacitor"
- Check orientation and polarity relative to breadboard power rails where visible.

4. **Ceramic Disc Capacitor**: Small, thin, flat yellow/orange disc (or small bulbous coin shape) with two parallel wire leads.
- Example name: "Ceramic Capacitor" or "Ceramic Disc Capacitor"

5. **Potentiometer**: Variable resistor with a rotating knob or thumbwheel, typically housed in a blue, black, or metallic casing with 3 terminal pins plugged into adjacent breadboard rows.
- Example name: "Potentiometer" or "Trimmer Potentiometer"

6. **Diode / Zener Diode**: Small black or glass cylinder with a single silver or black cathode band near one end.
- Example name: "Rectifier Diode" or "Signal Diode"

7. **Transistor / Voltage Regulator**: Small 3-pin component with a flat front and curved back (TO-92 package) or a metal tab (TO-220 package).
- Example name: "NPN Transistor" or "Voltage Regulator"

8. **Integrated Circuit (DIP IC)**: Rectangular black plastic package with pins on two parallel sides straddling the center breadboard divider channel.
- Example name: "555 Timer IC" or "Dual Op-Amp IC"

9. **Jumper Wires**: Flexible insulated solid-core wires bridging two breadboard tie-points or power rails.
- Example name: "Jumper Wire"

---

### Expected Structural Output Example:

"components_detected": [
  {
    "component_id": "R1",
    "name": "Resistor",
    "location_description": "Connected across row 15 between terminal strip and power rail",
    "bounding_box": {"ymin": 0.42, "xmin": 0.38, "ymax": 0.52, "xmax": 0.46},
    "confidence": 0.88
  },
  {
    "component_id": "LED1",
    "name": "LED",
    "location_description": "Plugged into terminal row 15 near resistor anode",
    "bounding_box": {"ymin": 0.48, "xmin": 0.45, "ymax": 0.58, "xmax": 0.52},
    "confidence": 0.91
  },
  {
    "component_id": "C1",
    "name": "Electrolytic Capacitor",
    "location_description": "Spanning power rail and terminal row 10",
    "bounding_box": {"ymin": 0.20, "xmin": 0.15, "ymax": 0.35, "xmax": 0.25},
    "confidence": 0.85
  },
  {
    "component_id": "C2",
    "name": "Ceramic Capacitor",
    "location_description": "Small orange disc connected between row 12 and ground rail",
    "bounding_box": {"ymin": 0.30, "xmin": 0.28, "ymax": 0.38, "xmax": 0.33},
    "confidence": 0.89
  },
  {
    "component_id": "RV1",
    "name": "Potentiometer",
    "location_description": "3-pin variable resistor with dial spanning terminal rows 20 to 22",
    "bounding_box": {"ymin": 0.60, "xmin": 0.50, "ymax": 0.75, "xmax": 0.65},
    "confidence": 0.92
  },
  {
    "component_id": "IC1",
    "name": "Integrated Circuit",
    "location_description": "8-pin DIP package straddling center divider channel",
    "bounding_box": {"ymin": 0.35, "xmin": 0.40, "ymax": 0.55, "xmax": 0.60},
    "confidence": 0.85
  }
]
"""