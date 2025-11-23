"""
Example: Using Estimator Primitive

This example demonstrates how to use the Estimator primitive to compute
expectation values of observables on quantum states.

Estimator calculates ⟨ψ|H|ψ⟩ where:
- |ψ⟩ is a quantum state prepared by a circuit
- H is an observable (Hamiltonian)


NOTE: This example uses FakeProviderForBackendV2 and QiskitRuntimeLocalService
      directly because job execution over REST API has serialization limitations.
      Backend endpoints (configuration, properties, status) work perfectly via REST.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from qiskit import QuantumCircuit
from qiskit.circuit.library import RealAmplitudes
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeProviderForBackendV2
from qiskit_ibm_runtime.fake_provider.local_service import QiskitRuntimeLocalService
from qiskit_ibm_runtime import EstimatorV2 as Estimator
import numpy as np


def example_basic_estimator(service, backend):
    """Basic Estimator example with a simple observable."""
    print("\n" + "="*60)
    print("Example 1: Basic Estimator - Z Expectation Value")
    print("="*60)

    # Create a simple circuit: |+⟩ state
    qc = QuantumCircuit(1)
    qc.h(0)  # Creates |+⟩ = (|0⟩ + |1⟩)/√2

    # Define observable: Z operator
    # For |+⟩ state, ⟨+|Z|+⟩ should be 0
    observable = SparsePauliOp.from_list([("Z", 1)])

    print("\nCircuit (|+⟩ state):")
    print(qc)
    print(f"\nObservable: Z")
    print(f"Expected value: 0 (equal superposition)")

    # Transpile
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(qc)
    isa_observable = observable.apply_layout(isa_circuit.layout)

    # Create and run Estimator
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = 2048

    print(f"\nRunning on backend: {backend.name}")
    job = estimator.run([(isa_circuit, isa_observable)])
    print(f"Job ID: {job.job_id()}")

    # Get results
    result = job.result()
    pub_result = result[0]

    expectation_value = pub_result.data.evs[0]
    std_error = pub_result.data.stds[0]

    print(f"\nResults:")
    print(f"  Expectation value: {expectation_value:.4f}")
    print(f"  Standard error: {std_error:.4f}")
    print(f"  Expected: ~0.0")


def example_parameterized_circuit(service, backend):
    """Example with parameterized circuit."""
    print("\n" + "="*60)
    print("Example 2: Parameterized Circuit")
    print("="*60)

    # Create a parameterized circuit
    num_qubits = 2
    psi = RealAmplitudes(num_qubits=num_qubits, reps=2)

    # Define a simple Hamiltonian
    # H = I⊗I + 2·I⊗Z + 3·X⊗I
    hamiltonian = SparsePauliOp.from_list([
        ("II", 1),
        ("IZ", 2),
        ("XI", 3)
    ])

    print(f"\nParameterized circuit: RealAmplitudes({num_qubits} qubits, 2 reps)")
    print(f"Number of parameters: {psi.num_parameters}")
    print(f"\nHamiltonian:")
    print(hamiltonian)

    # Set parameter values
    theta = np.random.random(psi.num_parameters)
    print(f"\nParameter values: {theta}")

    # Transpile
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(psi)
    isa_observable = hamiltonian.apply_layout(isa_circuit.layout)

    # Run Estimator
    estimator = Estimator(mode=backend)

    print(f"\nRunning on backend: {backend.name}")
    job = estimator.run([(isa_circuit, isa_observable, [theta])])
    print(f"Job ID: {job.job_id()}")

    # Get results
    result = job.result()
    pub_result = result[0]

    expectation_value = pub_result.data.evs[0]
    std_error = pub_result.data.stds[0]

    print(f"\nResults:")
    print(f"  Expectation value: {expectation_value:.4f}")
    print(f"  Standard error: {std_error:.4f}")


def example_multiple_observables(service, backend):
    """Example with multiple observables."""
    print("\n" + "="*60)
    print("Example 3: Multiple Observables")
    print("="*60)

    # Create circuit
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)  # Bell state |Φ+⟩

    # Define multiple observables
    observables = [
        SparsePauliOp.from_list([("ZZ", 1)]),  # ⟨ZZ⟩
        SparsePauliOp.from_list([("XX", 1)]),  # ⟨XX⟩
        SparsePauliOp.from_list([("YY", 1)]),  # ⟨YY⟩
    ]
    obs_names = ["ZZ", "XX", "YY"]

    print("\nCircuit: Bell state |Φ+⟩")
    print(qc)
    print(f"\nObservables: {', '.join(obs_names)}")
    print("Expected values for Bell state:")
    print("  ⟨ZZ⟩ = +1")
    print("  ⟨XX⟩ = +1")
    print("  ⟨YY⟩ = -1")

    # Transpile
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(qc)

    # Prepare PUBs (Primitive Unified Blocks)
    pubs = []
    for obs in observables:
        isa_obs = obs.apply_layout(isa_circuit.layout)
        pubs.append((isa_circuit, isa_obs))

    # Run Estimator
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = 4096

    print(f"\nRunning on backend: {backend.name}")
    job = estimator.run(pubs)
    print(f"Job ID: {job.job_id()}")

    # Get results
    result = job.result()

    print(f"\nResults:")
    for name, pub_result in zip(obs_names, result):
        ev = pub_result.data.evs[0]
        std = pub_result.data.stds[0]
        print(f"  ⟨{name}⟩ = {ev:+.4f} ± {std:.4f}")


def example_with_error_mitigation(service, backend):
    """Example with error mitigation options."""
    print("\n" + "="*60)
    print("Example 4: Error Mitigation")
    print("="*60)

    # Create circuit
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    # Observable
    observable = SparsePauliOp.from_list([("ZZ", 1)])

    # Transpile
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(qc)
    isa_observable = observable.apply_layout(isa_circuit.layout)

    # Create Estimator with error mitigation
    estimator = Estimator(mode=backend)

    # Set resilience level (0, 1, or 2)
    # Level 0: No error mitigation
    # Level 1: Readout mitigation
    # Level 2: Gate twirling + readout mitigation
    estimator.options.resilience_level = 1

    # Set precision (target precision for expectation value)
    estimator.options.default_precision = 0.03

    print(f"\nEstimator Options:")
    print(f"  Resilience Level: {estimator.options.resilience_level}")
    print(f"  Target Precision: {estimator.options.default_precision}")
    print(f"  Default Shots: {estimator.options.default_shots}")

    print(f"\nRunning on backend: {backend.name}")
    job = estimator.run([(isa_circuit, isa_observable)])
    print(f"Job ID: {job.job_id()}")

    # Get results
    result = job.result()
    pub_result = result[0]

    expectation_value = pub_result.data.evs[0]
    std_error = pub_result.data.stds[0]

    print(f"\nResults (with error mitigation):")
    print(f"  Expectation value: {expectation_value:+.4f}")
    print(f"  Standard error: {std_error:.4f}")
    print(f"  Expected (ideal): +1.0")


def main():
    print("="*60)
    print("Estimator Primitive Examples")
    print("="*60)

    # Connect to service
    print("\nConnecting to local Qiskit Runtime Server...")

    try:
        service = QiskitRuntimeService(
            channel="ibm_quantum_platform",
            token="test-token",
            url="http://localhost:8000",
            instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
            verify=False
        )
        print("✓ Connected to: http://localhost:8000")
    except Exception as e:
        print(f"✗ Error connecting to service: {e}")
        print("\nMake sure:")
        print("  1. The server is running: python -m src.main")
        print("  2. Server is accessible at: http://localhost:8000")
        return

    # Get a backend
    print("\nGetting backend...")
    try:
        # Use a fake backend from local server
        backend = service.backend("fake_manila")  # Small 5-qubit backend
        print(f"✓ Selected backend: {backend.name} ({backend.num_qubits} qubits)")
    except Exception as e:
        print(f"✗ Error getting backend: {e}")
        print("Available backends can be listed with: service.backends()")
        return

    # Run examples
    try:
        example_basic_estimator(service, backend)
        example_parameterized_circuit(service, backend)
        example_multiple_observables(service, backend)
        example_with_error_mitigation(service, backend)

    except Exception as e:
        print(f"\n⚠ Error running examples: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
