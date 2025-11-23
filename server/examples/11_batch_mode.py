"""
Example: Using Batch Mode for Parallel Jobs

Batch mode is ideal when you have multiple independent circuits to run
and want to execute them efficiently in parallel.

Batch benefits:
- Run multiple independent jobs in parallel
- Cost-effective for large workloads
- Automatic queue management
- Good for parameter sweeps, benchmarking, error characterization


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
from qiskit_ibm_runtime import Batch, SamplerV2 as Sampler
import numpy as np


def example_parameter_sweep(service, backend):
    """Parameter sweep using Batch mode."""
    print("\n" + "="*60)
    print("Example 1: Parameter Sweep with Batch")
    print("="*60)

    # Create parameterized circuit
    qc = RealAmplitudes(num_qubits=2, reps=1)

    print(f"\nCircuit: RealAmplitudes(2 qubits, 1 rep)")
    print(f"Parameters: {qc.num_parameters}")
    print(qc)

    # Generate parameter sweep
    num_points = 10
    param_values_list = [
        np.random.random(qc.num_parameters) * 2 * np.pi
        for _ in range(num_points)
    ]

    print(f"\nGenerating {num_points} parameter sets for sweep")

    # Add measurements
    qc_with_meas = qc.copy()
    qc_with_meas.measure_all()

    # Transpile
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(qc_with_meas)

    # Create batch and submit jobs
    print(f"\nOpening batch on backend: {backend.name}")
    with Batch(backend=backend) as batch:
        sampler = Sampler(mode=batch)
        sampler.options.default_shots = 1024

        print(f"Batch ID: {batch.session_id}")

        # Submit all jobs
        jobs = []
        for i, params in enumerate(param_values_list):
            # Bind parameters
            bound_circuit = isa_circuit.assign_parameters(params)
            job = sampler.run([bound_circuit])
            jobs.append(job)
            print(f"  Submitted job {i+1}/{num_points}: {job.job_id()}")

        # Collect results
        print(f"\nCollecting results...")
        all_counts = []
        for i, job in enumerate(jobs):
            result = job.result()
            counts = result[0].data.meas.get_counts()
            all_counts.append(counts)
            print(f"  Job {i+1} completed: {len(counts)} unique bitstrings")

    print(f"\nBatch closed")
    print(f"Total jobs completed: {len(jobs)}")


def example_circuit_benchmarking(service, backend):
    """Circuit benchmarking using Batch mode."""
    print("\n" + "="*60)
    print("Example 2: Circuit Depth Benchmarking")
    print("="*60)

    # Create circuits with different depths
    depths = [5, 10, 20, 30, 40]
    circuits = []

    print(f"\nCreating circuits with depths: {depths}")

    for depth in depths:
        qc = QuantumCircuit(2)
        for _ in range(depth):
            qc.h(0)
            qc.cx(0, 1)
        qc.measure_all()
        circuits.append(qc)

    # Transpile
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuits = pm.run(circuits)

    # Run in batch
    print(f"\nOpening batch on backend: {backend.name}")
    with Batch(backend=backend) as batch:
        sampler = Sampler(mode=batch)
        sampler.options.default_shots = 2048

        # Submit all jobs at once
        jobs = []
        for i, circuit in enumerate(isa_circuits):
            job = sampler.run([circuit])
            jobs.append(job)
            print(f"  Submitted job for depth={depths[i]}: {job.job_id()}")

        # Analyze results
        print(f"\nResults:")
        print(f"{'Depth':<10} {'00 Count':<15} {'11 Count':<15} {'Fidelity':<10}")
        print("-" * 60)

        for depth, job in zip(depths, jobs):
            result = job.result()
            counts = result[0].data.meas.get_counts()

            # For Bell state, expect 50/50 split between |00⟩ and |11⟩
            count_00 = counts.get('00', 0)
            count_11 = counts.get('11', 0)
            total = sum(counts.values())
            fidelity = (count_00 + count_11) / total

            print(f"{depth:<10} {count_00:<15} {count_11:<15} {fidelity:<10.3f}")

    print(f"\nBatch closed")


def example_randomized_benchmarking(service, backend):
    """Simplified randomized benchmarking using Batch."""
    print("\n" + "="*60)
    print("Example 3: Randomized Benchmarking")
    print("="*60)

    # Create random circuits with different lengths
    num_circuits_per_length = 5
    circuit_lengths = [1, 2, 5, 10, 20]

    print(f"\nGenerating random circuits:")
    print(f"  Lengths: {circuit_lengths}")
    print(f"  Circuits per length: {num_circuits_per_length}")

    circuits = []
    lengths_for_circuits = []

    for length in circuit_lengths:
        for _ in range(num_circuits_per_length):
            qc = QuantumCircuit(1)

            # Apply random Clifford gates
            for _ in range(length):
                gate_choice = np.random.randint(0, 3)
                if gate_choice == 0:
                    qc.h(0)
                elif gate_choice == 1:
                    qc.s(0)
                else:
                    qc.x(0)

            # Add inverse to return to |0⟩
            # (simplified - real RB would compute proper inverse)

            qc.measure_all()
            circuits.append(qc)
            lengths_for_circuits.append(length)

    print(f"  Total circuits: {len(circuits)}")

    # Transpile
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuits = pm.run(circuits)

    # Run in batch
    print(f"\nOpening batch on backend: {backend.name}")
    with Batch(backend=backend) as batch:
        sampler = Sampler(mode=batch)
        sampler.options.default_shots = 1024

        # Submit all jobs
        jobs = []
        for circuit in isa_circuits:
            job = sampler.run([circuit])
            jobs.append(job)

        print(f"  Submitted {len(jobs)} jobs")

        # Analyze survival probability
        print(f"\nAnalyzing survival probabilities...")
        survival_probs = {length: [] for length in circuit_lengths}

        for job, length in zip(jobs, lengths_for_circuits):
            result = job.result()
            counts = result[0].data.meas.get_counts()

            # Probability of returning to |0⟩
            total = sum(counts.values())
            prob_0 = counts.get('0', 0) / total
            survival_probs[length].append(prob_0)

        # Print average survival probability
        print(f"\n{'Length':<10} {'Avg P(0)':<15} {'Std Dev':<15}")
        print("-" * 40)
        for length in circuit_lengths:
            probs = survival_probs[length]
            avg_prob = np.mean(probs)
            std_prob = np.std(probs)
            print(f"{length:<10} {avg_prob:<15.3f} {std_prob:<15.3f}")

    print(f"\nBatch closed")


def main():
    print("="*60)
    print("Batch Mode Examples")
    print("="*60)
    print("\nBatch mode benefits:")
    print("- Parallel execution of independent jobs")
    print("- Cost-effective for large workloads")
    print("- Ideal for parameter sweeps and benchmarking")

    # Connect to service
    print("\nConnecting to Qiskit Runtime Service...")

    try:
        service = QiskitRuntimeService(
            channel="ibm_quantum_platform",
            token="test-token",
            url="http://localhost:8000",
            instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
            verify=False
        )
    except Exception as e:
        print(f"Error connecting to service: {e}")
        print("\nTo use this example:")
        print("1. Save your IBM Quantum account:")
        print("   QiskitRuntimeService.save_account(channel='ibm_quantum', token='YOUR_TOKEN')")
        return

    # Get a backend
    print("Getting backend...")
    try:
        backend = service.backend("fake_manila")  # Small 5-qubit backend
        print(f"Selected backend: {backend.name}")
    except Exception as e:
        print(f"Error getting backend: {e}")
        print("Trying to use a simulator...")
        try:
            backend = service.backend("ibmq_qasm_simulator")
        except:
            print("No backend available.")
            return

    # Run examples
    try:
        example_parameter_sweep(service, backend)
        example_circuit_benchmarking(service, backend)
        example_randomized_benchmarking(service, backend)

    except Exception as e:
        print(f"\n⚠ Error running examples: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Batch examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
