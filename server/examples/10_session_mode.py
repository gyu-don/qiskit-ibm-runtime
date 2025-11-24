"""
Example: Using Session Mode for Iterative Algorithms

Session mode is ideal for iterative algorithms like VQE, QAOA, or parameter
optimization where you need to run multiple circuits in sequence and maintain
queue priority.

Session benefits:
- Queue priority: Jobs in a session run consecutively
- Reduced wait time for iterative algorithms
- Efficient for optimization loops


"""


import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Apply localhost patch BEFORE importing QiskitRuntimeService
from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

from qiskit import QuantumCircuit
from qiskit.circuit.library import RealAmplitudes
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime import Session, EstimatorV2 as Estimator
import numpy as np


def simple_vqe(estimator, circuit, hamiltonian, initial_params, max_iter=5):
    """
    Simple VQE implementation.

    Args:
        estimator: Estimator primitive
        circuit: Parameterized quantum circuit
        hamiltonian: Observable to minimize
        initial_params: Initial parameter values
        max_iter: Maximum iterations

    Returns:
        Optimized parameters and minimum energy
    """
    print("\n" + "-"*60)
    print("Simple VQE Optimization")
    print("-"*60)

    current_params = initial_params.copy()
    learning_rate = 0.1
    epsilon = 0.01  # For finite difference gradient

    print(f"Initial parameters: {current_params}")

    for iteration in range(max_iter):
        # Compute current energy
        job = estimator.run([(circuit, hamiltonian, [current_params])])
        result = job.result()
        energy = result[0].data.evs[0]

        print(f"\nIteration {iteration + 1}/{max_iter}")
        print(f"  Energy: {energy:.6f}")
        print(f"  Params: {current_params}")

        # Compute gradient using finite differences
        gradient = np.zeros_like(current_params)
        for i in range(len(current_params)):
            params_plus = current_params.copy()
            params_plus[i] += epsilon

            job = estimator.run([(circuit, hamiltonian, [params_plus])])
            result = job.result()
            energy_plus = result[0].data.evs[0]

            gradient[i] = (energy_plus - energy) / epsilon

        # Update parameters
        current_params -= learning_rate * gradient

        # Simple convergence check
        if np.linalg.norm(gradient) < 0.01:
            print(f"\nConverged!")
            break

    print(f"\nFinal energy: {energy:.6f}")
    print(f"Final parameters: {current_params}")

    return current_params, energy


def example_session_vqe(service, backend):
    """VQE example using Session mode."""
    print("\n" + "="*60)
    print("Example 1: VQE with Session Mode")
    print("="*60)

    # Create parameterized circuit
    num_qubits = 2
    ansatz = RealAmplitudes(num_qubits=num_qubits, reps=2)

    # Define Hamiltonian (example: H2 molecule)
    hamiltonian = SparsePauliOp.from_list([
        ("II", -1.0523),
        ("IZ", 0.3979),
        ("ZI", -0.3979),
        ("ZZ", -0.0112),
        ("XX", 0.1809),
    ])

    print(f"\nAnsatz: RealAmplitudes({num_qubits} qubits, 2 reps)")
    print(f"Parameters: {ansatz.num_parameters}")
    print(f"\nHamiltonian (H2 molecule):")
    print(hamiltonian)

    # Transpile
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(ansatz)
    isa_hamiltonian = hamiltonian.apply_layout(isa_circuit.layout)

    # Initial parameters
    initial_params = np.random.random(ansatz.num_parameters) * 2 * np.pi

    # Open a session
    print(f"\nOpening session on backend: {backend.name}")
    with Session(backend=backend) as session:
        # Create Estimator in session mode
        estimator = Estimator(mode=session)
        estimator.options.default_shots = 1024
        estimator.options.resilience_level = 1

        print(f"Session ID: {session.session_id}")

        # Run VQE
        optimal_params, min_energy = simple_vqe(
            estimator,
            isa_circuit,
            isa_hamiltonian,
            initial_params,
            max_iter=5
        )

    print(f"\nSession closed")
    print(f"Minimum energy found: {min_energy:.6f}")


def example_session_multiple_jobs(service, backend):
    """Example with multiple independent jobs in a session."""
    print("\n" + "="*60)
    print("Example 2: Multiple Jobs in Session")
    print("="*60)

    # Create multiple circuits
    circuits = []
    observables = []

    for angle in [0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi]:
        qc = QuantumCircuit(1)
        qc.ry(angle, 0)
        circuits.append(qc)

        # Observable: Z
        obs = SparsePauliOp.from_list([("Z", 1)])
        observables.append(obs)

    print(f"\nCreated {len(circuits)} circuits with different RY angles")
    print("Observable: Z")
    print("Expected: cos(angle)")

    # Transpile
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuits = pm.run(circuits)

    # Open session
    print(f"\nOpening session on backend: {backend.name}")
    with Session(backend=backend) as session:
        estimator = Estimator(mode=session)

        print(f"Session ID: {session.session_id}")

        # Submit multiple jobs sequentially
        jobs = []
        for i, (circuit, obs) in enumerate(zip(isa_circuits, observables)):
            isa_obs = obs.apply_layout(circuit.layout)
            job = estimator.run([(circuit, isa_obs)])
            jobs.append(job)
            print(f"  Submitted job {i+1}/{len(circuits)}: {job.job_id()}")

        # Collect results
        print(f"\nCollecting results...")
        angles = [0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi]
        for i, (job, angle) in enumerate(zip(jobs, angles)):
            result = job.result()
            ev = result[0].data.evs[0]
            expected = np.cos(angle)
            print(f"  Angle={angle:.4f}: ⟨Z⟩={ev:+.4f} (expected: {expected:+.4f})")

    print(f"\nSession closed")


def example_session_context_manager(service, backend):
    """Example showing session context manager features."""
    print("\n" + "="*60)
    print("Example 3: Session Context Manager")
    print("="*60)

    qc = QuantumCircuit(1)
    qc.h(0)
    obs = SparsePauliOp.from_list([("Z", 1)])

    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(qc)
    isa_obs = obs.apply_layout(isa_circuit.layout)

    print(f"\nUsing backend: {backend.name}")

    # Session automatically manages lifecycle
    with Session(backend=backend) as session:
        print(f"Session started: {session.session_id}")

        estimator = Estimator(mode=session)

        # Run multiple jobs
        for i in range(3):
            job = estimator.run([(isa_circuit, isa_obs)])
            result = job.result()
            ev = result[0].data.evs[0]
            print(f"  Job {i+1}: ⟨Z⟩ = {ev:+.4f}")

        # Session stays alive until context exits
        print(f"Session still active: {session.session_id}")

    # Session automatically closed when exiting context
    print(f"Session closed automatically")


def main():
    print("="*60)
    print("Session Mode Examples")
    print("="*60)
    print("\nSession mode benefits:")
    print("- Jobs run consecutively with priority")
    print("- Ideal for iterative algorithms (VQE, QAOA)")
    print("- Reduced wait time in queue")

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
        example_session_vqe(service, backend)
        example_session_multiple_jobs(service, backend)
        example_session_context_manager(service, backend)

    except Exception as e:
        print(f"\n⚠ Error running examples: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Session examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
