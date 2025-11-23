"""
Basic example: Connecting to local FastAPI server.

This example demonstrates direct HTTP connection to the local mock server.

IMPORTANT: Make sure the local server is running before executing this script:
    cd server
    python -m src.main

NOTE: Due to QiskitRuntimeService's built-in IBM Cloud validation,
we use direct HTTP requests for the most reliable local server testing.
For actual usage with implemented endpoints, see example 07_direct_http.py
"""

import sys

print("="*60)
print("Connecting to Local FastAPI Server")
print("="*60)

# Check if server is running
print("\nStep 1: Checking if server is running...")

try:
    import requests
except ImportError:
    print("✗ Error: 'requests' library not found")
    print("\nPlease install it:")
    print("  pip install requests")
    sys.exit(1)

try:
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        print("✓ Server is running!")
        health_data = response.json()
        print(f"  Status: {health_data.get('status')}")
        print(f"  Version: {health_data.get('version')}")
    else:
        print(f"✗ Server responded with status {response.status_code}")
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print("\n✗ Error: Cannot connect to server at http://localhost:8000")
    print("\nPlease start the server first:")
    print("  cd server")
    print("  python -m src.main")
    print("\nThen run this example again.")
    sys.exit(1)

# Test API root endpoint
print("\nStep 2: Testing API root endpoint...")
try:
    response = requests.get("http://localhost:8000/", timeout=2)
    if response.status_code == 200:
        print("✓ API root accessible!")
        api_info = response.json()
        print(f"  Name: {api_info.get('name')}")
        print(f"  Version: {api_info.get('version')}")
        print(f"  Documentation: http://localhost:8000{api_info.get('documentation')}")
except Exception as e:
    print(f"✗ Error accessing API root: {e}")
    sys.exit(1)

# Test backends endpoint (will return 501 as not implemented)
print("\nStep 3: Testing backends endpoint...")
headers = {
    "Authorization": "Bearer test-token",
    "Service-CRN": "crn:v1:bluemix:public:quantum-computing:us-east:a/test:test::",
    "IBM-API-Version": "2025-05-01"
}

try:
    response = requests.get(
        "http://localhost:8000/v1/backends",
        headers=headers,
        timeout=2
    )
    print(f"  Response status: {response.status_code}")

    if response.status_code == 501:
        print("  ✓ Server responded (501 Not Implemented - expected)")
        print("  This confirms the server is working correctly!")
        error_data = response.json()
        print(f"  Message: {error_data.get('detail')}")
    elif response.status_code == 200:
        print("  ✓ Server returned data!")
        print(f"  Response: {response.json()}")
    else:
        print(f"  Unexpected status code: {response.status_code}")
        print(f"  Response: {response.text}")

except Exception as e:
    print(f"✗ Error testing backends endpoint: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✓ Connection test successful!")
print("="*60)
print("\nThe local server is working correctly.")
print("You can now:")
print("  - View the API docs: http://localhost:8000/docs")
print("  - Test other endpoints using examples 02-07")
print("  - See server logs in the terminal where you started the server")
print("="*60)
