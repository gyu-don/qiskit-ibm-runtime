"""
Example: Get backend details from local server.

This example shows how to retrieve detailed information about a specific backend:
- Configuration (gates, topology, capabilities)
- Properties (calibration data: T1, T2, errors)
- Status (operational status, queue length)
"""

from qiskit_ibm_runtime import QiskitRuntimeService
from datetime import datetime

def print_configuration(backend):
    """Print backend configuration details."""
    config = backend.configuration()

    print(f"\n{'='*60}")
    print(f"Configuration: {config.backend_name}")
    print(f"{'='*60}")
    print(f"Version:        {config.backend_version}")
    print(f"Qubits:         {config.n_qubits}")
    print(f"Simulator:      {config.simulator}")
    print(f"Open Pulse:     {config.open_pulse}")
    print(f"Max Shots:      {config.max_shots}")
    print(f"Basis Gates:    {', '.join(config.basis_gates)}")

    if hasattr(config, 'processor_type') and config.processor_type:
        print(f"Processor:      {config.processor_type.get('family', 'N/A')} "
              f"r{config.processor_type.get('revision', 'N/A')}")

    if hasattr(config, 'quantum_volume') and config.quantum_volume:
        print(f"Quantum Volume: {config.quantum_volume}")

    if config.coupling_map:
        print(f"Coupling Map:   {len(config.coupling_map)} edges")
        print(f"                {config.coupling_map[:5]}..." if len(config.coupling_map) > 5 else f"                {config.coupling_map}")


def print_properties(backend):
    """Print backend properties (calibration data)."""
    props = backend.properties()

    print(f"\n{'='*60}")
    print(f"Properties: {props.backend_name}")
    print(f"{'='*60}")
    print(f"Last Update:    {props.last_update_date}")
    print(f"\nQubit Properties:")

    # Print T1, T2, frequency for first 3 qubits
    for i, qubit_props in enumerate(props.qubits[:3]):
        print(f"\n  Qubit {i}:")
        for prop in qubit_props:
            if prop.name in ['T1', 'T2', 'frequency', 'readout_error']:
                print(f"    {prop.name:15s}: {prop.value:.4f} {prop.unit}")

    if len(props.qubits) > 3:
        print(f"\n  ... and {len(props.qubits) - 3} more qubits")

    # Print gate errors
    if props.gates:
        print(f"\nGate Properties (sample):")
        for gate_prop in props.gates[:5]:
            gate_error = next((p.value for p in gate_prop.parameters if p.name == 'gate_error'), None)
            gate_length = next((p.value for p in gate_prop.parameters if p.name == 'gate_length'), None)
            qubits_str = ','.join(map(str, gate_prop.qubits))
            print(f"  {gate_prop.gate}({qubits_str}): ", end="")
            if gate_error:
                print(f"error={gate_error:.4f}", end="")
            if gate_length:
                print(f", length={gate_length:.1f}ns", end="")
            print()


def print_status(backend):
    """Print backend operational status."""
    status = backend.status()

    print(f"\n{'='*60}")
    print(f"Status: {status.backend_name}")
    print(f"{'='*60}")
    print(f"Operational:    {'✓ Yes' if status.operational else '✗ No'}")
    print(f"Status Message: {status.status_msg}")
    print(f"Pending Jobs:   {status.pending_jobs}")

    # Estimate wait time (rough calculation)
    if status.pending_jobs > 0:
        estimated_wait = status.pending_jobs * 2  # Assume 2 min per job
        print(f"Est. Wait Time: ~{estimated_wait} minutes")


def main():
    # Connect to local server
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token="test-token",
        url="http://localhost:8000",
        instance="crn:v1:bluemix:public:quantum-computing:us-east:a/test:test::",
        verify=False
    )

    print(f"Connected to: http://localhost:8000")

    # Specify backend name (adjust as needed)
    backend_name = "ibm_brisbane"

    try:
        print(f"\nGetting backend: {backend_name}")
        backend = service.backend(backend_name)

        # Get configuration
        print_configuration(backend)

        # Get properties
        print_properties(backend)

        # Get status
        print_status(backend)

    except Exception as e:
        print(f"\n⚠ Error: {type(e).__name__}: {e}")
        print("\nNote: The local server currently returns 501 (Not Implemented)")
        print("See server/IMPLEMENTATION_STATUS.md for the implementation roadmap")


if __name__ == "__main__":
    main()
