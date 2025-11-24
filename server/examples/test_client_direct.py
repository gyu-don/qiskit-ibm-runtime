#!/usr/bin/env python3
"""
Direct test of RuntimeClient to debug backend listing.
"""

import sys
import os
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Apply localhost patch
from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

from qiskit_ibm_runtime.api.clients import RuntimeClient
from qiskit_ibm_runtime.api.client_parameters import ClientParameters
from qiskit_ibm_runtime.api.auth import CloudAuth

try:
    # Create ClientParameters
    params = ClientParameters(
        channel="ibm_quantum_platform",
        token="test-token",
        url="http://localhost:8000",
        instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
        verify=False
    )

    print(f"Client base URL: {params.get_runtime_api_base_url()}")

    # Create RuntimeClient
    client = RuntimeClient(params)

    # Try to list backends
    print("\nCalling client.list_backends()...")
    backends = client.list_backends()

    print(f"\nFound {len(backends)} backends:")
    for backend in backends[:5]:
        print(f"  - {backend.get('backend_name', 'UNKNOWN')}")

except Exception as e:
    print(f"\n✗ Error: {e}")
    traceback.print_exc()
