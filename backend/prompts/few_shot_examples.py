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
MULTIMETER_IMG = load_reference_image("test_multimeter.jpg")

FEW_SHOT_EXAMPLES = """
### DISCRETE BREADBOARD COMPONENT IDENTIFICATION EXAMPLES:

Use these rigorous reference patterns to distinguish between similarly shaped components on breadboard tie-points and test equipment:

1. **Resistor**: Small, opaque, cylindrical body (typically beige, light blue, or grey) featuring four or five distinct color-code bands and two axial wire leads extending straight from the ends.
- Example name: "Resistor" or "Current-Limiting Resistor"
- Key differentiator: Opaque body with colored rings; do NOT confuse with diodes or ceramic capacitors.

2. **LED (Light Emitting Diode)**: Small 3mm or 5mm component featuring a distinct, translucent or semi-clear plastic dome lens (showing internal anvil/post electrodes) paired with two axial wire leads (anode is longer).
- Example name: "LED" or "Indicator LED"
- Key differentiator: Translucent/glassy plastic dome with visible internal metal anvil posts. Determine color ONLY from the plastic dome lens itself, never from test leads. If color is ambiguous, use "LED". **Crucial Note**: Recognizable even when connected standalone without a resistor; never misidentify a standalone LED as a capacitor or cylindrical can.

3. **Electrolytic Capacitor**: Cylindrical metal or wrapped plastic can (typically black, blue, or silver) with a clearly marked vertical stripe and minus (-) symbols indicating the negative lead, standing vertically or lying horizontally.
- Example name: "Electrolytic Capacitor"
- Key differentiator: Tall cylindrical can shape with polarity markings; distinct from flat ceramic discs or resistors.

4. **Ceramic Disc Capacitor**: Small, thin, flat disc (commonly orange, yellow, or brownish-red, sometimes resembling a small bulbous coin) with two parallel wire leads emerging from the bottom.
- Example name: "Ceramic Capacitor" or "Ceramic Disc Capacitor"
- Key differentiator: Flat, disc-like or coin-like profile without color bands; distinct from cylindrical resistors or electrolytic caps.

5. **Potentiometer**: Variable resistor featuring a rotating dial, adjustment screw, or thumbwheel mounted on a bulky blue, black, or metallic rectangular casing with 3 terminal pins plugged into adjacent breadboard rows.
- Example name: "Potentiometer" or "Trimmer Potentiometer"
- Key differentiator: Mechanical adjustment dial or screw on top of a multi-pin block.

6. **Diode / Zener Diode**: Small, opaque black or clear glass cylinder with a single distinct silver or black cathode band painted near one end.
- Example name: "Rectifier Diode" or "Signal Diode"
- Key differentiator: Smaller than a resistor, lacks color-code bands, features a single stripe at one extremity.

7. **Transistor / Voltage Regulator**: Small 3-pin component characterized by a flat front face with text markings and a curved back body (TO-92 package) or a metallic mounting tab (TO-220 package).
- Example name: "NPN Transistor" or "Voltage Regulator"
- Key differentiator: D-shaped package profile or flat front face with 3 leads.

8. **Integrated Circuit (DIP IC)**: Rectangular black plastic package with a semi-circular top notch/dot and rows of parallel pins along both long sides straddling the center breadboard divider channel.
- Example name: "555 Timer IC" or "Dual Op-Amp IC"
- Key differentiator: Multi-pin dual-inline rectangular package spanning across the board channel.

9. **Jumper Wires**: Flexible, insulated solid-core or stranded wires bridging two breadboard tie-points, components, or power rails.
- Example name: "Jumper Wire"

10. **Multimeter**: Large, handheld or benchtop electronic measurement instrument characterized by a massive handheld plastic chassis (dwarf-like in scale compared to tiny breadboard components), featuring a prominent rectangular digital LCD screen at the top, a large central rotary selection dial, and thick, insulated flexible test probe leads plugged into bottom ports.
- Example name: "Digital Multimeter" or "Multimeter"
- Key differentiator: Vastly larger physical dimensions than any breadboard component (occupying a major portion of the frame context), featuring a display screen, central mode knob, and heavy multi-color probe wires.

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
    "location_description": "Connected directly across power module rails without a resistor",
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
  },
  {
    "component_id": "MM1",
    "name": "Multimeter",
    "location_description": "Handheld digital multimeter positioned alongside the breadboard with probes connected to circuit rails",
    "bounding_box": {"ymin": 0.05, "xmin": 0.65, "ymax": 0.95, "xmax": 0.98},
    "confidence": 0.96
  }
]
"""