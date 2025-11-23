"""
Example: Test all backend endpoints.

This example systematically tests all backend-related endpoints
available in the local mock server.
"""

import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Apply localhost patch BEFORE importing QiskitRuntimeService
from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

from qiskit_ibm_runtime import QiskitRuntimeService

def test_list_backends(service):
    """Test GET /v1/backends"""
    print("\n1. Testing: List Backends")
    print("-" * 60)
    try:
        backends = service.backends()
        print(f"   ✓ Success: Found {len(backends)} backends")
        for backend in backends[:3]:  # Show first 3
            print(f"     - {backend.name} ({backend.num_qubits} qubits)")
        if len(backends) > 3:
            print(f"     ... and {len(backends) - 3} more")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {type(e).__name__}: {e}")
        return False


def test_backend_configuration(service, backend):
    """Test GET /v1/backends/{id}/configuration"""
    print(f"\n2. Testing: Get Backend Configuration ({backend.name})")
    print("-" * 60)
    try:
        config = backend.configuration()
        print(f"   ✓ Success: Retrieved configuration")
        print(f"     - Backend: {config.backend_name}")
        print(f"     - Version: {config.backend_version}")
        print(f"     - Qubits: {config.n_qubits}")
        print(f"     - Basis gates: {len(config.basis_gates)} gates")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {type(e).__name__}: {e}")
        return False


def test_backend_properties(service, backend):
    """Test GET /v1/backends/{id}/properties"""
    print(f"\n3. Testing: Get Backend Properties ({backend.name})")
    print("-" * 60)
    try:
        properties = backend.properties()
        print(f"   ✓ Success: Retrieved properties")
        print(f"     - Backend: {properties.backend_name}")
        print(f"     - Last update: {properties.last_update_date}")
        print(f"     - Qubits: {len(properties.qubits)} qubits with calibration data")
        print(f"     - Gates: {len(properties.gates)} gate calibrations")

        # Show sample T1 time
        if properties.qubits and len(properties.qubits) > 0:
            t1_prop = next((p for p in properties.qubits[0] if p.name == 'T1'), None)
            if t1_prop:
                print(f"     - Sample T1 (qubit 0): {t1_prop.value:.2f} {t1_prop.unit}")

        return True
    except Exception as e:
        print(f"   ✗ Failed: {type(e).__name__}: {e}")
        return False


def test_backend_status(service, backend):
    """Test GET /v1/backends/{id}/status"""
    print(f"\n4. Testing: Get Backend Status ({backend.name})")
    print("-" * 60)
    try:
        status = backend.status()
        print(f"   ✓ Success: Retrieved status")
        print(f"     - Backend: {status.backend_name}")
        print(f"     - Operational: {status.operational}")
        print(f"     - Status: {status.status_msg}")
        print(f"     - Pending jobs: {status.pending_jobs}")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {type(e).__name__}: {e}")
        return False


def test_backend_defaults(service, backend):
    """Test GET /v1/backends/{id}/defaults (if available)"""
    print(f"\n5. Testing: Get Backend Defaults ({backend.name})")
    print("-" * 60)
    # Note: defaults() method may not be directly exposed in the public API
    # This is typically for pulse-level programming
    print(f"   ⚠ Skipped: defaults() not in public API")
    print(f"     (Used internally for pulse programming)")
    return None


def main():
    print("="*60)
    print("Testing Local Qiskit Runtime Server")
    print("="*60)
    print("Server URL: http://localhost:8000")
    print("API Version: 2025-05-01")

    # Connect to local server
    try:
        service = QiskitRuntimeService(
            channel="ibm_quantum_platform",
            token="test-token",
            url="http://localhost:8000",
            instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
            verify=False
        )
        print("✓ Connected successfully")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)

    # Run tests
    results = []

    results.append(("List Backends", test_list_backends(service)))

    # Get a backend for testing
    print("\nGetting backend for detailed tests...")
    try:
        backends = service.backends()
        if not backends:
            print("✗ No backends available")
            return
        backend = backends[0]  # Use first backend
        print(f"✓ Using backend: {backend.name}")
    except Exception as e:
        print(f"✗ Failed to get backends: {e}")
        return

    results.append(("Backend Configuration", test_backend_configuration(service, backend)))
    results.append(("Backend Properties", test_backend_properties(service, backend)))
    results.append(("Backend Status", test_backend_status(service, backend)))
    results.append(("Backend Defaults", test_backend_defaults(service, backend)))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)

    for test_name, result in results:
        status = "✓ PASS" if result is True else "✗ FAIL" if result is False else "⚠ SKIP"
        print(f"{status:10s} {test_name}")

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")

    if failed > 0:
        print("\n" + "="*60)
        print("Note: Some tests failed. Make sure:")
        print("  1. The server is running: python -m src.main")
        print("  2. Server is accessible at: http://localhost:8000")
        print("="*60)


if __name__ == "__main__":
    main()
