# tests/test_api.py
import requests
import os

API_URL = "http://127.0.0.1:8000/api/analyze"
SAMPLE_IMAGE_PATH = "tests/sample_circuits/test1.jpg"

def run_test():
    if not os.path.exists(SAMPLE_IMAGE_PATH):
        print(f"[-] Error: Test image not found at {SAMPLE_IMAGE_PATH}")
        print("    Please place a JPEG or PNG image at that location to run the test.")
        return

    print(f"[+] Sending payload to {API_URL}...")
    
    with open(SAMPLE_IMAGE_PATH, "rb") as img_file:
        files = {"image": ("test_circuit.jpg", img_file, "image/jpeg")}
        data = {"description": "Breadboard setup with an op-amp and power rails. Check for short circuits."}
        
        response = requests.post(API_URL, files=files, data=data)

    print(f"[+] HTTP Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("[+] Success! Response validated against Pydantic schema:")
        print(response.json())
    else:
        print("[-] API returned an error:")
        print(response.text)

if __name__ == "__main__":
    run_test()