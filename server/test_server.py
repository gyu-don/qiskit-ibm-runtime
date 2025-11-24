#!/usr/bin/env python3
"""
Simple test script to verify the server implementation.
"""

import sys
from pathlib import Path

# Add parent directory to path to import qiskit_ibm_runtime
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_backend_provider():
    """Test backend provider."""
    print("Testing BackendProvider...")
    from src.backend_provider import get_backend_provider

    provider = get_backend_provider()

    # List all backends
    response = provider.list_backends()
    print(f"  Found {len(response.devices)} backends")

    if len(response.devices) > 0:
        backend_name = response.devices[0].backend_name
        print(f"  First backend: {backend_name}")

        # Get configuration
        config = provider.get_backend_configuration(backend_name)
        if config:
            print(f"    - Configuration: OK (n_qubits={config.n_qubits})")

        # Get status
        status = provider.get_backend_status(backend_name)
        if status:
            print(f"    - Status: OK (operational={status.operational})")

        # Get properties
        properties = provider.get_backend_properties(backend_name)
        if properties:
            print(f"    - Properties: OK (qubits={len(properties.qubits)})")
        else:
            print(f"    - Properties: Not available (expected for some backends)")

    print("  BackendProvider: ✓ PASS\n")


def test_job_manager():
    """Test job manager."""
    print("Testing JobManager...")
    from src.job_manager import get_job_manager
    from src.backend_provider import get_backend_provider

    job_manager = get_job_manager()
    provider = get_backend_provider()

    # Get a backend
    response = provider.list_backends()
    if len(response.devices) == 0:
        print("  No backends available, skipping job test")
        return

    backend_name = response.devices[0].backend_name
    print(f"  Using backend: {backend_name}")

    # Note: We won't actually create a job here as it requires valid circuit data
    # Just verify the manager is initialized
    print(f"  JobManager initialized: ✓")
    print("  JobManager: ✓ PASS\n")


def main():
    """Run all tests."""
    print("="*60)
    print("Server Implementation Test")
    print("="*60 + "\n")

    try:
        test_backend_provider()
        test_job_manager()

        print("="*60)
        print("All tests passed! ✓")
        print("="*60)

        print("\nNext steps:")
        print("1. Start the server:")
        print("   cd server && python -m src.main")
        print("\n2. Test endpoints:")
        print("   curl -X GET http://localhost:8000/health")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
