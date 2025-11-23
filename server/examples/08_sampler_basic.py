"""
Example: Using Sampler Primitive

This example demonstrates how to use the Sampler primitive to get
measurement results from quantum circuits.

Sampler returns quasi-probability distributions (measurement counts)
from executing quantum circuits.

NOTE: This example uses FakeProviderForBackendV2 and QiskitRuntimeLocalService
      directly because job execution over REST API has serialization limitations.
      Backend endpoints (configuration, properties, status) work perfectly via REST.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeProviderForBackendV2
from qiskit_ibm_runtime.fake_provider.local_service import QiskitRuntimeLocalService
from qiskit_ibm_runtime import SamplerV2 as Sampler


def create_bell_circuit():
    """Create a Bell state circuit."""
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc


def create_ghz_circuit(num_qubits=3):
    """Create a GHZ state circuit."""
    qc = QuantumCircuit(num_qubits)
    qc.h(0)
    for i in range(num_qubits - 1):
        qc.cx(i, i + 1)
    qc.measure_all()
    return qc


def example_basic_sampler(service, backend):
    """Basic Sampler example with a Bell state."""
    print("\n" + "="*60)
    print("Example 1: Basic Sampler with Bell State")
    print("="*60)

    # Create Bell state circuit
    bell = create_bell_circuit()
    print("\nCircuit:")
    print(bell)

    # Transpile for backend
    print("\nTranspiling for backend...")
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(bell)
    print(f"Transpiled circuit depth: {isa_circuit.depth()}")

    # Create Sampler
    sampler = Sampler(mode=backend)
    sampler.options.default_shots = 1024

    print(f"\nRunning on backend: {backend.name}")
    print(f"Shots: {sampler.options.default_shots}")

    # Run the circuit
    print("\nSubmitting job...")
    job = sampler.run([isa_circuit])
    print(f"Job ID: {job.job_id()}")
    print(f"Job Status: {job.status()}")

    # Get results
    print("\nWaiting for results...")
    result = job.result()

    # Access the first (and only) pub result
    pub_result = result[0]

    # Get counts
    counts = pub_result.data.meas.get_counts()
    print(f"\nMeasurement counts:")
    for bitstring, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {bitstring}: {count}")

    # Expected result: approximately 50% |00⟩ and 50% |11⟩ for Bell state
    print("\nExpected: ~50% |00⟩ and ~50% |11⟩ (Bell state)")


def example_multiple_circuits(service, backend):
    """Example with multiple circuits."""
    print("\n" + "="*60)
    print("Example 2: Running Multiple Circuits")
    print("="*60)

    # Create multiple circuits
    bell = create_bell_circuit()
    ghz3 = create_ghz_circuit(3)

    circuits = [bell, ghz3]
    circuit_names = ["Bell State", "GHZ-3 State"]

    # Transpile all circuits
    print("\nTranspiling circuits...")
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuits = pm.run(circuits)

    # Create Sampler and run all circuits
    sampler = Sampler(mode=backend)
    sampler.options.default_shots = 2048

    print(f"\nRunning {len(circuits)} circuits on {backend.name}")
    job = sampler.run(isa_circuits)
    print(f"Job ID: {job.job_id()}")

    # Get results
    result = job.result()

    # Display results for each circuit
    for i, (name, pub_result) in enumerate(zip(circuit_names, result)):
        print(f"\n{name}:")
        counts = pub_result.data.meas.get_counts()
        for bitstring, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {bitstring}: {count}")


def example_with_options(service, backend):
    """Example with custom Sampler options."""
    print("\n" + "="*60)
    print("Example 3: Sampler with Custom Options")
    print("="*60)

    # Create circuit
    qc = create_bell_circuit()

    # Transpile
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(qc)

    # Create Sampler with custom options
    sampler = Sampler(mode=backend)

    # Configure options
    sampler.options.default_shots = 4096
    sampler.options.dynamical_decoupling.enable = True
    sampler.options.dynamical_decoupling.sequence_type = "XY4"

    print(f"\nSampler Options:")
    print(f"  Shots: {sampler.options.default_shots}")
    print(f"  Dynamical Decoupling: {sampler.options.dynamical_decoupling.enable}")
    print(f"  DD Sequence: {sampler.options.dynamical_decoupling.sequence_type}")

    # Run
    job = sampler.run([isa_circuit])
    print(f"\nJob ID: {job.job_id()}")

    result = job.result()
    pub_result = result[0]
    counts = pub_result.data.meas.get_counts()

    print(f"\nResults:")
    for bitstring, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {bitstring}: {count}")


def main():
    print("="*60)
    print("Sampler Primitive Examples")
    print("="*60)

    # Get provider and backend
    print("\nSetting up FakeProvider...")

    try:
        provider = FakeProviderForBackendV2()
        backend = provider.backend("fake_manila")  # Small 5-qubit backend
        print(f"✓ Selected backend: {backend.name} ({backend.num_qubits} qubits)")

        # Note: You can also test backend properties here
        config = backend.configuration()
        print(f"  Backend version: {config.backend_version}")
        print(f"  Basis gates: {', '.join(config.basis_gates[:5])}{'...' if len(config.basis_gates) > 5 else ''}")
    except Exception as e:
        print(f"✗ Error getting backend: {e}")
        return

    # Create local service for job execution
    service = QiskitRuntimeLocalService()

    # Run examples
    try:
        example_basic_sampler(service, backend)
        example_multiple_circuits(service, backend)
        example_with_options(service, backend)

    except Exception as e:
        print(f"\n⚠ Error running examples: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
