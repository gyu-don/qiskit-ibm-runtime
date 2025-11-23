"""
Basic example: Connecting to local FastAPI server.

This example shows how to configure qiskit-ibm-runtime client
to connect to the local mock server running at http://localhost:8000

IMPORTANT: Make sure the local server is running before executing this script:
    cd server
    python -m src.main
"""

import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Apply localhost patch BEFORE importing QiskitRuntimeService
from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

print("="*60)
print("Connecting to Local FastAPI Server")
print("="*60)

# First, check if server is running
print("\nChecking if server is running at http://localhost:8000...")

try:
    import requests
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        print("✓ Server is running!")
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
except ImportError:
    print("Note: 'requests' library not installed, skipping server check")

# Now connect using QiskitRuntimeService
print("\nConnecting with QiskitRuntimeService...")

from qiskit_ibm_runtime import QiskitRuntimeService

try:
    # Configure service to point to localhost
    # The localhost patch (applied above) handles IBM Cloud API bypass automatically
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token="test-token-for-local-server",  # Can be any string for local testing
        url="http://localhost:8000",
        instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
        verify=False  # Disable SSL verification for localhost
    )

    print("\n✓ Successfully connected to local server!")
    print(f"  Server URL: {service._account.url}")
    print(f"  Channel: {service._account.channel}")
    print(f"  Token: {service._account.token[:20]}...")

    print("\n" + "="*60)
    print("Connection test successful!")
    print("="*60)

except Exception as e:
    print(f"\n✗ Error connecting: {type(e).__name__}: {e}")
    print("\nThis is expected if:")
    print("1. The server is not running")
    print("2. The server is running on a different port")
    print("\nTo fix:")
    print("  cd server")
    print("  python -m src.main")
    sys.exit(1)
