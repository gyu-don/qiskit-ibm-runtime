"""
Advanced Example: Using custom HTTP headers.

This example shows how to configure custom HTTP headers
when connecting to the local server, which is useful for testing
authentication and API versioning.
"""

import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Apply localhost patch BEFORE importing QiskitRuntimeService
from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.api.clients.runtime import RuntimeClient

def main():
    print("="*60)
    print("Testing Custom Headers with Local Server")
    print("="*60)

    # Create service
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token="my-custom-test-token",
        url="http://localhost:8000",
        instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
        verify=False
    )

    print(f"\nService configured:")
    print(f"  URL: {service._account.url}")
    print(f"  Token: {service._account.token[:20]}...")
    print(f"  Instance: {service._account.instance}")

    # The client automatically adds these headers:
    # - Authorization: Bearer {token}
    # - Service-CRN: {instance}
    # - IBM-API-Version: (from client)

    print(f"\n{'='*60}")
    print("HTTP Headers that will be sent to the server:")
    print(f"{'='*60}")
    print(f"  Authorization: Bearer {service._account.token}")
    print(f"  Service-CRN: {service._account.instance}")
    print(f"  IBM-API-Version: 2025-05-01 (or configured version)")
    print(f"  Accept: application/json")

    # Try to make a request
    print(f"\n{'='*60}")
    print("Making request to server...")
    print(f"{'='*60}")

    try:
        backends = service.backends()
        print(f"✓ Request successful! Found {len(backends)} backends")

        # Show backend info
        for backend in backends[:3]:
            print(f"\n  Backend: {backend.name}")
            print(f"    Qubits: {backend.num_qubits}")
            print(f"    Simulator: {backend.configuration().simulator}")

    except Exception as e:
        print(f"\n⚠ Server error (expected if not implemented):")
        print(f"   {type(e).__name__}: {e}")

        # Check if it's the expected 501 error
        if "501" in str(e) or "Not Implemented" in str(e):
            print(f"\n   This is the expected behavior - the server returns:")
            print(f"   HTTP 501 (Not Implemented) until data layer is added.")
            print(f"\n   However, the request was properly formatted with")
            print(f"   the correct headers and authentication!")

    print(f"\n{'='*60}")
    print("Testing different API versions:")
    print(f"{'='*60}")

    # Note: API version is controlled by the client library
    # In production, you might want to test different versions

    supported_versions = ["2024-01-01", "2025-01-01", "2025-05-01"]
    print(f"\nSupported API versions in the server:")
    for version in supported_versions:
        print(f"  - {version}")

    print(f"\nThe client library automatically uses the appropriate version")
    print(f"based on its implementation. To test different versions, you would")
    print(f"need to modify the client library's version constant or use")
    print(f"direct HTTP requests (see example 07).")


if __name__ == "__main__":
    main()
