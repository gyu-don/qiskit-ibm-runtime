"""Test script to debug result format."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

# Connect
service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token="test-token",
    url="http://localhost:8000",
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
    verify=False
)

# Get backend
backends = service.backends()
backend = next((b for b in backends if b.name == "fake_manila"), None)

# Create simple circuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

# Transpile
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa_circuit = pm.run(qc)

# Run
sampler = Sampler(mode=backend)
job = sampler.run([isa_circuit])
print(f"Job ID: {job.job_id()}")
print(f"Job Status: {job.status()}")

# Get result
result = job.result()

# Debug result structure
print(f"\n=== Result Debug ===")
print(f"Result type: {type(result)}")
print(f"Result repr: {repr(result)}")
print(f"Result dir: {[x for x in dir(result) if not x.startswith('_')]}")

# Try to access
try:
    print(f"\nHas __getitem__: {hasattr(result, '__getitem__')}")
    print(f"Is iterable: {hasattr(result, '__iter__')}")

    if hasattr(result, '__len__'):
        print(f"Length: {len(result)}")

    # Try different access methods
    print(f"\nTrying result[0]...")
    pub_result = result[0]
    print(f"  Success! Type: {type(pub_result)}")
except Exception as e:
    print(f"  Error: {type(e).__name__}: {e}")

    # Check if it's a dict
    if isinstance(result, dict):
        print(f"\nResult is a dict with keys: {list(result.keys())}")
        if 'results' in result:
            print(f"result['results'] type: {type(result['results'])}")
