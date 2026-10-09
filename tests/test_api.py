import requests
import json

URL = "http://127.0.0.1:8000/api/analyze"
IMAGE_PATH = "tests/sample_circuits/test1.jpg"  # Path to your test image

with open(IMAGE_PATH, "rb") as img_file:
    files = {"image": ("test_breadboard.jpg", img_file, "image/jpeg")}
    data = {"description": "Check this breadboard circuit setup."}
    
    print(f"[+] Sending payload to {URL}...")
    response = requests.post(URL, files=files, data=data)

print(f"[+] HTTP Status Code: {response.status_code}")

if response.status_code == 200:
    payload = response.json()
    print("\n" + "="*50)
    print("               ANALYSIS REPORT                   ")
    print("="*50)
    print(f"Circuit Type   : {payload.get('circuit_type')}")
    print(f"Overall Safety : {payload.get('overall_safety')}")
    print(f"Summary        : {payload.get('summary')}\n")

    print("-" * 50)
    print("DETECTED COMPONENTS:")
    print("-" * 50)
    for comp in payload.get("components_detected", []):
        comp_id = comp.get("component_id", "N/A")
        name = comp.get("name", "Unknown")
        confidence = comp.get("confidence", 0.0)
        location = comp.get("location_description", "N/A")
        bbox = comp.get("bounding_box", {})
        
        print(f"• [{comp_id}] {name} (Confidence: {confidence * 100:.1f}%)")
        print(f"  Location : {location}")
        print(f"  BBox     : {bbox}\n")

    print("-" * 50)
    print("HAZARDS & VIOLATIONS:")
    print("-" * 50)
    hazards = payload.get("hazards_and_violations", [])
    if hazards:
        for hazard in hazards:
            print(f"⚠️ [{hazard.get('severity', 'WARNING')}] {hazard.get('title')}")
            print(f"   Explanation: {hazard.get('explanation')}\n")
    else:
        print("  None detected.\n")

else:
    print("[-] Error Response:")
    print(json.dumps(response.json(), indent=2))