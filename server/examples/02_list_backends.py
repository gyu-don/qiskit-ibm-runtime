"""
Example: List backends from local server.

This example demonstrates how to list all available backends
from the local mock server.

Note: The server currently returns 501 (Not Implemented) for all endpoints.
Once the server is implemented, this will return actual backend data.
"""

from qiskit_ibm_runtime import QiskitRuntimeService

def main():
    # Connect to local server
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token="test-token",
        url="http://localhost:8000",
        # instance parameter omitted to skip IBM Cloud validation
        verify=False
    )

    print("Connecting to http://localhost:8000")
    print("-" * 60)

    try:
        # List all backends
        print("\n1. Listing all backends...")
        backends = service.backends()

        print(f"   Found {len(backends)} backends:")
        for backend in backends:
            print(f"   - {backend.name}")
            print(f"     Qubits: {backend.num_qubits}")
            print(f"     Operational: {backend.status().operational}")
            print()

    except Exception as e:
        print(f"   ⚠ Error: {e}")
        print(f"   This is expected if the server is not yet implemented (returns 501)")
        print(f"   See server/IMPLEMENTATION_STATUS.md for implementation roadmap")


if __name__ == "__main__":
    main()
