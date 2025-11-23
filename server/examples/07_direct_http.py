"""
Direct HTTP Example: Calling the API without qiskit-ibm-runtime.

This example shows how to call the local server API directly using
the `requests` library, which is useful for testing the raw HTTP endpoints.
"""

import requests
import json
from datetime import datetime

# Server configuration
BASE_URL = "http://localhost:8000"
HEADERS = {
    "Authorization": "Bearer test-token",
    "Service-CRN": "crn:v1:bluemix:public:quantum-computing:us-east:a/test:test::",
    "IBM-API-Version": "2025-05-01",
    "Accept": "application/json"
}


def test_health_check():
    """Test the health check endpoint."""
    print("\n1. Health Check")
    print("-" * 60)

    response = requests.get(f"{BASE_URL}/health")
    print(f"   GET /health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_list_backends():
    """Test listing all backends."""
    print("\n2. List Backends")
    print("-" * 60)

    response = requests.get(
        f"{BASE_URL}/v1/backends",
        headers=HEADERS
    )

    print(f"   GET /v1/backends")
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
    else:
        print(f"   Error: {response.text}")

    return response.status_code in [200, 501]


def test_list_backends_with_fields():
    """Test listing backends with additional fields."""
    print("\n3. List Backends with Fields")
    print("-" * 60)

    response = requests.get(
        f"{BASE_URL}/v1/backends",
        headers=HEADERS,
        params={"fields": "wait_time_seconds"}
    )

    print(f"   GET /v1/backends?fields=wait_time_seconds")
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
    else:
        print(f"   Error: {response.text}")

    return response.status_code in [200, 501]


def test_backend_configuration(backend_id="ibm_brisbane"):
    """Test getting backend configuration."""
    print(f"\n4. Get Backend Configuration ({backend_id})")
    print("-" * 60)

    response = requests.get(
        f"{BASE_URL}/v1/backends/{backend_id}/configuration",
        headers=HEADERS
    )

    print(f"   GET /v1/backends/{backend_id}/configuration")
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        # Print subset of data (full response is large)
        print(f"   Response (partial):")
        print(f"     backend_name: {data.get('backend_name')}")
        print(f"     n_qubits: {data.get('n_qubits')}")
        print(f"     basis_gates: {data.get('basis_gates')}")
    else:
        print(f"   Error: {response.text}")

    return response.status_code in [200, 404, 501]


def test_backend_properties(backend_id="ibm_brisbane"):
    """Test getting backend properties."""
    print(f"\n5. Get Backend Properties ({backend_id})")
    print("-" * 60)

    response = requests.get(
        f"{BASE_URL}/v1/backends/{backend_id}/properties",
        headers=HEADERS
    )

    print(f"   GET /v1/backends/{backend_id}/properties")
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   Response (partial):")
        print(f"     backend_name: {data.get('backend_name')}")
        print(f"     last_update_date: {data.get('last_update_date')}")
        print(f"     num_qubits: {len(data.get('qubits', []))}")
        print(f"     num_gates: {len(data.get('gates', []))}")
    else:
        print(f"   Error: {response.text}")

    return response.status_code in [200, 404, 501]


def test_backend_status(backend_id="ibm_brisbane"):
    """Test getting backend status."""
    print(f"\n6. Get Backend Status ({backend_id})")
    print("-" * 60)

    response = requests.get(
        f"{BASE_URL}/v1/backends/{backend_id}/status",
        headers=HEADERS
    )

    print(f"   GET /v1/backends/{backend_id}/status")
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
    else:
        print(f"   Error: {response.text}")

    return response.status_code in [200, 404, 501]


def test_backend_defaults(backend_id="ibm_brisbane"):
    """Test getting backend defaults."""
    print(f"\n7. Get Backend Defaults ({backend_id})")
    print("-" * 60)

    response = requests.get(
        f"{BASE_URL}/v1/backends/{backend_id}/defaults",
        headers=HEADERS
    )

    print(f"   GET /v1/backends/{backend_id}/defaults")
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   Response (partial):")
        print(f"     qubit_freq_est: {data.get('qubit_freq_est', [])[:3]}...")
        print(f"     meas_freq_est: {data.get('meas_freq_est', [])[:3]}...")
        print(f"     buffer: {data.get('buffer')}")
    else:
        print(f"   Error: {response.text}")

    return response.status_code in [200, 404, 501]


def test_missing_auth():
    """Test request without authentication."""
    print("\n8. Test Missing Authentication")
    print("-" * 60)

    # Request without headers
    response = requests.get(f"{BASE_URL}/v1/backends")

    print(f"   GET /v1/backends (no auth headers)")
    print(f"   Status: {response.status_code}")
    print(f"   Expected: 422 (Validation Error)")

    return response.status_code == 422


def test_invalid_api_version():
    """Test request with invalid API version."""
    print("\n9. Test Invalid API Version")
    print("-" * 60)

    invalid_headers = HEADERS.copy()
    invalid_headers["IBM-API-Version"] = "1999-01-01"

    response = requests.get(
        f"{BASE_URL}/v1/backends",
        headers=invalid_headers
    )

    print(f"   GET /v1/backends (with API version: 1999-01-01)")
    print(f"   Status: {response.status_code}")
    print(f"   Expected: 400 (Bad Request)")
    print(f"   Error: {response.json().get('detail', 'N/A')}")

    return response.status_code == 400


def main():
    print("="*60)
    print("Direct HTTP API Testing")
    print("="*60)
    print(f"Server: {BASE_URL}")
    print(f"API Version: {HEADERS['IBM-API-Version']}")

    # Run all tests
    results = []
    results.append(("Health Check", test_health_check()))
    results.append(("List Backends", test_list_backends()))
    results.append(("List Backends with Fields", test_list_backends_with_fields()))
    results.append(("Backend Configuration", test_backend_configuration()))
    results.append(("Backend Properties", test_backend_properties()))
    results.append(("Backend Status", test_backend_status()))
    results.append(("Backend Defaults", test_backend_defaults()))
    results.append(("Missing Authentication", test_missing_auth()))
    results.append(("Invalid API Version", test_invalid_api_version()))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10s} {test_name}")

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    print("\n" + "="*60)
    print("Note: 501 responses are expected for unimplemented endpoints")
    print("See: server/IMPLEMENTATION_STATUS.md")
    print("="*60)


if __name__ == "__main__":
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library not found")
        print("Install it with: pip install requests")
        exit(1)

    main()
