# backend/services/safety_rules.py
import logging
from typing import Dict, Any, List

logger = logging.getLogger("CircuitMentor")


def evaluate_electrical_rules(parsed_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies deterministic electrical safety rules to detected components and updates 
    hazards, recommendations, and overall_safety accordingly with robust keyword fallback checks.
    """
    components = parsed_payload.get("components_detected", [])
    hazards = parsed_payload.get("hazards_and_violations", [])
    recommendations = parsed_payload.get("recommendations", [])
    overall_safety = parsed_payload.get("overall_safety", "SAFE")
    telemetry = parsed_payload.get("telemetry", {})
    summary_text = parsed_payload.get("summary", "").lower()

    # Standardize component metadata extraction
    comp_names = []
    comp_descriptions = []
    for c in components:
        if isinstance(c, dict):
            comp_names.append(c.get("name", "").lower())
            comp_descriptions.append(c.get("location_description", "").lower())

    has_led = any("led" in name for name in comp_names)
    
    # Expanded keyword list for robust resistor detection across LLM naming variations
    resistor_keywords = ["resistor", "current-limiting", "bands", "ohm", "axial", "striped", "carbon"]
    
    # Primary check: Component object list contains resistor-related keywords in name or description
    obj_has_resistor = any(
        any(kw in name or kw in desc for kw in resistor_keywords)
        for name, desc in zip(comp_names, comp_descriptions)
    )
    
    # Fallback check: Check if summary or descriptions textually reference a resistor, 
    # explicitly filtering out negative statements (e.g., "no resistor")
    summary_lower = summary_text.lower()
    summary_mentions_resistor = any(kw in summary_lower for kw in resistor_keywords)
    is_negated = any(
        neg in summary_lower 
        for neg in ["no resistor", "without resistor", "missing resistor", "lacks resistor", "no current-limiting"]
    )
    
    text_has_resistor = (summary_mentions_resistor and not is_negated) or any(
        any(kw in desc for kw in resistor_keywords) for desc in comp_descriptions
    )
    
    has_resistor = obj_has_resistor or text_has_resistor

    has_ic = any("ic" in name or "chip" in name or "integrated circuit" in name or "555" in name for name in comp_names)
    has_capacitor = any("capacitor" in name for name in comp_names)
    has_power_source = any("v-src" in name or "voltage source" in name or "battery" in name or "power" in name for name in comp_names)
    has_ground = any("gnd" in name or "ground" in name for name in comp_names)

    # ------------------------------------------------------------------------
    # RULE 1: LED present without a Series Current-Limiting Resistor
    # ------------------------------------------------------------------------
    if has_led and not has_resistor:
        logger.info("[Safety Engine Rule Triggered] LED detected without valid series current-limiting resistor.")
        
        already_reported = any("resistor" in str(h.get("title", "")).lower() for h in hazards)
        if not already_reported:
            hazards.append({
                "hazard_id": "HZ_MISSING_RESISTOR",
                "category": "MISSING_COMPONENT",
                "title": "Missing Series Current-Limiting Resistor",
                "explanation": "An LED is present in the circuit layout but lacks an in-line banded current-limiting resistor. Connecting an LED directly across power sources causes thermal runaway, excessive current draw, and permanent burnout.",
                "severity": "DANGER",
                "affected_components": ["LED"]
            })
            recommendations.append("Insert a 220Ω to 1kΩ banded current-limiting resistor in series with the LED anode path.")

        overall_safety = "DANGER"
        telemetry["requires_power_kill"] = True

    # ------------------------------------------------------------------------
    # RULE 2: Direct Power-to-Ground Short Circuit Detection
    # ------------------------------------------------------------------------
    if has_power_source and has_ground and not has_resistor and not has_led and not has_ic and not has_capacitor:
        logger.info("[Safety Engine Rule Triggered] Potential direct short circuit between power and ground.")
        
        already_reported = any("short" in str(h.get("title", "")).lower() for h in hazards)
        if not already_reported:
            hazards.append({
                "hazard_id": "HZ_POWER_SHORT_CIRCUIT",
                "category": "SHORT_CIRCUIT",
                "title": "Direct Power-to-Ground Short Circuit",
                "explanation": "The circuit contains a direct bridge between power rails and ground without any intervening resistive load or component, risking severe power supply damage or fire.",
                "severity": "DANGER",
                "affected_components": ["V-SRC", "GND"]
            })
            recommendations.append("Disconnect direct power-to-ground paths and insert a load or proper resistor network.")

        overall_safety = "DANGER"
        telemetry["requires_power_kill"] = True

    # ------------------------------------------------------------------------
    # RULE 3: Active IC / Microcontroller without Decoupling Capacitor
    # ------------------------------------------------------------------------
    if has_ic and not has_capacitor:
        logger.info("[Safety Engine Rule Triggered] IC detected without decoupling capacitor.")
        
        already_reported = any("decoupling" in str(h.get("title", "")).lower() or "capacitor" in str(h.get("title", "")).lower() for h in hazards)
        if not already_reported:
            hazards.append({
                "hazard_id": "HZ_MISSING_DECOUPLING",
                "category": "MISSING_COMPONENT",
                "title": "Missing Decoupling Capacitor",
                "explanation": "An active integrated circuit was detected without an adjacent bypass/decoupling capacitor to stabilize power rails.",
                "severity": "WARNING",
                "affected_components": ["IC"]
            })
            recommendations.append("Place a 0.1µF ceramic disc capacitor across the IC VCC and GND supply pins.")

        if overall_safety != "DANGER":
            overall_safety = "WARNING"

    # Save mutated lists/flags back into the dictionary
    parsed_payload["hazards_and_violations"] = hazards
    parsed_payload["recommendations"] = recommendations
    parsed_payload["overall_safety"] = overall_safety
    parsed_payload["telemetry"] = telemetry

    return parsed_payload