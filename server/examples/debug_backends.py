#!/usr/bin/env python3
"""
Debug script to investigate why qiskit_ibm_runtime client returns 0 backends.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Apply localhost patch BEFORE importing QiskitRuntimeService
from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

from qiskit_ibm_runtime import QiskitRuntimeService
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

try:
    # Connect to local server
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token="test-token",
        url="http://localhost:8000",
        instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
        verify=False
    )

    print("\n" + "="*60)
    print("Service connected successfully")
    print("="*60)

    # Try to list backends
    print("\nCalling service.backends()...")
    backends = service.backends()

    print(f"\nFound {len(backends)} backends:")
    for backend in backends:
        print(f"  - {backend.name}")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
