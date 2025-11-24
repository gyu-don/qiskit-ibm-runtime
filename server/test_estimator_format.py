"""Test script to debug estimator result format."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator

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
qc = QuantumCircuit(1)
qc.h(0)

# Observable
observable = SparsePauliOp.from_list([("Z", 1)])

# Transpile
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa_circuit = pm.run(qc)
isa_observable = observable.apply_layout(isa_circuit.layout)

# Run
estimator = Estimator(mode=backend)
job = estimator.run([(isa_circuit, isa_observable)])
print(f"Job ID: {job.job_id()}")

# Get result
result = job.result()

# Debug result structure
print(f"\n=== Result Debug ===")
print(f"Result type: {type(result)}")
print(f"Result length: {len(result)}")

pub_result = result[0]
print(f"\nPubResult type: {type(pub_result)}")
print(f"PubResult.data type: {type(pub_result.data)}")
print(f"PubResult.data dir: {[x for x in dir(pub_result.data) if not x.startswith('_')]}")

if hasattr(pub_result.data, 'evs'):
    print(f"\nevs type: {type(pub_result.data.evs)}")
    print(f"evs value: {pub_result.data.evs}")
    print(f"evs shape: {pub_result.data.evs.shape if hasattr(pub_result.data.evs, 'shape') else 'N/A'}")
    print(f"evs is array: {hasattr(pub_result.data.evs, '__getitem__')}")

    # Try accessing
    try:
        print(f"\nTrying evs[0]...")
        val = pub_result.data.evs[0]
        print(f"  Success! Value: {val}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
        print(f"  Try without indexing...")
        print(f"  evs value: {pub_result.data.evs}")

if hasattr(pub_result.data, 'stds'):
    print(f"\nstds type: {type(pub_result.data.stds)}")
    print(f"stds value: {pub_result.data.stds}")
