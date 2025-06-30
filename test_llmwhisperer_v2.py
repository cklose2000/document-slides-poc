#!/usr/bin/env python3
"""Test LLMWhisperer v2 API"""

import requests
import os

api_key = "TfJ6jDg8wIq4LmS93ojd2jO-pGw_oG4O19MCGX5iUFI"
base_url = "https://llmwhisperer-api.us-central.unstract.com/api/v2"

# Test different possible endpoints
endpoints = [
    "/",
    "/whisper",
    "/process",
    "/extract",
    "/status",
    "/whisper-status"
]

headers = {
    'unstract-key': api_key,
}

print("Testing LLMWhisperer v2 API endpoints...")
print(f"Base URL: {base_url}")
print("-" * 50)

for endpoint in endpoints:
    url = f"{base_url}{endpoint}"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"GET {endpoint}: Status {response.status_code}")
        if response.status_code != 404:
            print(f"  Response: {response.text[:100]}")
    except Exception as e:
        print(f"GET {endpoint}: Error - {str(e)}")

# Test with sample PDF
print("\n" + "-" * 50)
print("Testing PDF submission...")
test_pdf_path = "/mnt/c/Users/cklos/document-slides-poc/demo_files/financial_report_q3.pdf"

if os.path.exists(test_pdf_path):
    with open(test_pdf_path, 'rb') as f:
        pdf_data = f.read()
    
    # Try different submission endpoints
    submit_endpoints = ["/whisper", "/process", "/extract"]
    
    for endpoint in submit_endpoints:
        url = f"{base_url}{endpoint}"
        headers_with_content = {
            'unstract-key': api_key,
            'Content-Type': 'application/octet-stream'
        }
        
        try:
            response = requests.post(url, data=pdf_data, headers=headers_with_content, timeout=10)
            print(f"POST {endpoint}: Status {response.status_code}")
            if response.status_code in [200, 201, 202]:
                print(f"  Success! Response: {response.text[:200]}")
                break
        except Exception as e:
            print(f"POST {endpoint}: Error - {str(e)}")