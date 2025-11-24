"""
Temporary test script to send job via REST API and see what parameters are received.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

print("Setting up test...")

# Connect to local server
service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token="test-token",
    url="http://localhost:8000",
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
    verify=False
)

# Get backend
backend = service.backend("fake_manila")
print(f"Using backend: {backend.name}")

# Create simple circuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

print("Transpiling circuit...")
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa_circuit = pm.run(qc)

# Create Sampler and run
print("Creating sampler and submitting job...")
sampler = Sampler(mode=backend)
sampler.options.default_shots = 100

try:
    job = sampler.run([isa_circuit])
    print(f"Job ID: {job.job_id()}")
    print("Waiting for completion...")
    result = job.result()
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
