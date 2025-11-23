"""
Basic example: Connecting to local FastAPI server.

This example shows how to configure qiskit-ibm-runtime client
to connect to the local mock server running at http://localhost:8000
"""

from qiskit_ibm_runtime import QiskitRuntimeService

# Configure service to point to localhost
service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token="test-token-for-local-server",  # Can be any string for local testing
    url="http://localhost:8000",
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/test-account:test-service::",
    verify=False  # Disable SSL verification for localhost
)

print("✓ Successfully connected to local server at http://localhost:8000")
print(f"Service URL: {service._account.url}")
print(f"Channel: {service._account.channel}")
