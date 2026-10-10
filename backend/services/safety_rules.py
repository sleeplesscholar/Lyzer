# backend/services/safety_rules.py
import logging
from typing import Dict, Any, List

logger = logging.getLogger("CircuitMentor")


def evaluate_electrical_rules(parsed_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies deterministic electrical safety rules to detected components and updates 
    hazards, recommendations, and overall_safety accordingly.
    """
    components = parsed_payload.get("components_detected", [])
    hazards = parsed_payload.get("hazards_and_violations", [])
    recommendations = parsed_payload.get("recommendations", [])
    overall_safety = parsed_payload.get("overall_safety", "SAFE")
    telemetry = parsed_payload.get("telemetry", {})

    # Standardize component name lookups
    comp_names = [c.get("name", "").lower() for c in components if isinstance(c, dict)]
    
    has_led = any("led" in name for name in comp_names)
    has_resistor = any("resistor" in name for name in comp_names)
    has_ic = any("ic" in name or "chip" in name or "integrated circuit" in name for name in comp_names)
    has_capacitor = any("capacitor" in name for name in comp_names)

    # ------------------------------------------------------------------------
    # RULE 1: LED present without a Series Current-Limiting Resistor
    # ------------------------------------------------------------------------
    if has_led and not has_resistor:
        logger.info("[Safety Engine Rule Triggered] LED detected without current-limiting resistor.")
        
        # Check if LLM already added a hazard for resistor missing
        already_reported = any("resistor" in str(h).lower() for h in hazards)
        if not already_reported:
            hazards.append({
                "hazard_id": "HZ_MISSING_RESISTOR",
                "category": "MISSING_COMPONENT",  # Updated from OVERCURRENT to match Pydantic Enum
                "title": "Missing Series Current-Limiting Resistor",
                "explanation": "An LED is connected without a series current-limiting resistor. Connecting an LED directly across power rails will cause excessive current draw, destroying the LED or overloading the power supply.",
                "severity": "DANGER",
                "affected_components": ["LED"]
            })
            recommendations.append("Insert a 220Ω to 1kΩ current-limiting resistor in series with the LED anode or cathode.")

        overall_safety = "DANGER"
        telemetry["requires_power_kill"] = True

    # ------------------------------------------------------------------------
    # RULE 2: Active IC / Microcontroller without Decoupling Capacitor
    # ------------------------------------------------------------------------
    if has_ic and not has_capacitor:
        logger.info("[Safety Engine Rule Triggered] IC detected without decoupling capacitor.")
        
        already_reported = any("decoupling" in str(h).lower() or "capacitor" in str(h).lower() for h in hazards)
        if not already_reported:
            hazards.append({
                "hazard_id": "HZ_MISSING_DECOUPLING",
                "category": "MISSING_COMPONENT",  # Updated from POWER_STABILITY to match Pydantic Enum
                "title": "Missing Decoupling Capacitor",
                "explanation": "Integrated circuit detected without a bypass/decoupling capacitor near its power supply pins.",
                "severity": "WARNING",
                "affected_components": ["IC"]
            })
            recommendations.append("Place a 0.1µF ceramic capacitor across the IC VCC and GND pins to suppress power rail noise.")

        if overall_safety != "DANGER":
            overall_safety = "WARNING"

    # Save mutated lists/flags back into the dictionary
    parsed_payload["hazards_and_violations"] = hazards
    parsed_payload["recommendations"] = recommendations
    parsed_payload["overall_safety"] = overall_safety
    parsed_payload["telemetry"] = telemetry

    return parsed_payload