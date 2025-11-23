"""
Backend Provider Integration.

This module integrates qiskit_ibm_runtime.fake_provider to provide
backend data for the REST API server.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add parent directory to path to import qiskit_ibm_runtime
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from qiskit_ibm_runtime.fake_provider import FakeProviderForBackendV2
from qiskit_ibm_runtime.fake_provider.fake_backend import FakeBackendV2

from .models import (
    BackendDevice,
    BackendConfiguration,
    BackendProperties,
    BackendStatus,
    BackendDefaults,
    BackendsResponse,
    ProcessorType,
    GateConfig,
    GateProperties,
    Nduv,
)


class BackendProvider:
    """
    Backend provider that wraps FakeProviderForBackendV2.

    Provides methods to retrieve backend information in REST API format.
    """

    def __init__(self):
        """Initialize the backend provider."""
        self.provider = FakeProviderForBackendV2()
        self._backends_cache = None

    def _get_all_backends(self) -> List[FakeBackendV2]:
        """Get all available backends."""
        if self._backends_cache is None:
            self._backends_cache = self.provider.backends()
        return self._backends_cache

    def get_backend(self, backend_name: str) -> Optional[FakeBackendV2]:
        """
        Get a specific backend by name.

        Args:
            backend_name: Name of the backend

        Returns:
            FakeBackendV2 instance or None if not found
        """
        try:
            return self.provider.backend(backend_name)
        except Exception:
            return None

    def list_backends(self, fields: Optional[str] = None) -> BackendsResponse:
        """
        List all available backends.

        Args:
            fields: Optional comma-separated list of additional fields

        Returns:
            BackendsResponse with list of backends
        """
        backends = self._get_all_backends()
        devices = []

        for backend in backends:
            config = backend.configuration()
            status = backend.status()

            # Extract processor type
            processor_type = None
            if hasattr(config, 'processor_type') and config.processor_type:
                pt = config.processor_type
                processor_type = ProcessorType(
                    family=pt.get('family', 'Unknown'),
                    revision=pt.get('revision', 1.0)
                )

            device = BackendDevice(
                backend_name=backend.name,
                backend_version=getattr(config, 'backend_version', '1.0.0'),
                operational=status.operational,
                simulator=getattr(config, 'simulator', False),
                n_qubits=backend.num_qubits,
                processor_type=processor_type,
                quantum_volume=getattr(config, 'quantum_volume', None),
                clops_h=getattr(config, 'clops_h', None),
            )

            # Add wait time if requested
            if fields and 'wait_time_seconds' in fields:
                device.queue_length = status.pending_jobs
                # Estimate wait time: 60 seconds per pending job
                device.wait_time_seconds = status.pending_jobs * 60.0

            devices.append(device)

        return BackendsResponse(devices=devices)

    def get_backend_configuration(
        self,
        backend_name: str,
        calibration_id: Optional[str] = None
    ) -> Optional[BackendConfiguration]:
        """
        Get backend configuration.

        Args:
            backend_name: Name of the backend
            calibration_id: Optional calibration ID (not used in fake backends)

        Returns:
            BackendConfiguration or None if backend not found
        """
        backend = self.get_backend(backend_name)
        if backend is None:
            return None

        config = backend.configuration()

        # Convert gate configurations
        gates = []
        if hasattr(config, 'gates') and config.gates:
            for gate in config.gates:
                gate_config = GateConfig(
                    name=gate.get('name', ''),
                    parameters=gate.get('parameters', []),
                    qasm_def=gate.get('qasm_def', None),
                    coupling_map=gate.get('coupling_map', None),
                    latency_map=gate.get('latency_map', None),
                    conditional=gate.get('conditional', False),
                    description=gate.get('description', None),
                )
                gates.append(gate_config)

        # Extract processor type
        processor_type = None
        if hasattr(config, 'processor_type') and config.processor_type:
            pt = config.processor_type
            processor_type = ProcessorType(
                family=pt.get('family', 'Unknown'),
                revision=pt.get('revision', 1.0)
            )

        # Build configuration response
        return BackendConfiguration(
            backend_name=backend.name,
            backend_version=getattr(config, 'backend_version', '1.0.0'),
            n_qubits=backend.num_qubits,
            basis_gates=getattr(config, 'basis_gates', []),
            gates=gates,
            local=getattr(config, 'local', False),
            simulator=getattr(config, 'simulator', False),
            conditional=getattr(config, 'conditional', False),
            open_pulse=getattr(config, 'open_pulse', False),
            memory=getattr(config, 'memory', False),
            max_shots=getattr(config, 'max_shots', 8192),
            max_experiments=getattr(config, 'max_experiments', 1),
            coupling_map=getattr(config, 'coupling_map', None),
            supported_instructions=getattr(config, 'supported_instructions', None),
            dynamic_reprate_enabled=getattr(config, 'dynamic_reprate_enabled', False),
            rep_delay_range=getattr(config, 'rep_delay_range', None),
            default_rep_delay=getattr(config, 'default_rep_delay', None),
            meas_map=getattr(config, 'meas_map', None),
            processor_type=processor_type,
            dt=getattr(config, 'dt', None),
            dtm=getattr(config, 'dtm', None),
            parametric_pulses=getattr(config, 'parametric_pulses', []),
            n_registers=getattr(config, 'n_registers', None),
            n_uchannels=getattr(config, 'n_uchannels', 0),
            u_channel_lo=getattr(config, 'u_channel_lo', []),
            qubit_lo_range=getattr(config, 'qubit_lo_range', None),
            meas_lo_range=getattr(config, 'meas_lo_range', None),
            acquire_alignment=getattr(config, 'acquire_alignment', None),
            pulse_alignment=getattr(config, 'pulse_alignment', None),
            meas_kernels=getattr(config, 'meas_kernels', None),
            discriminators=getattr(config, 'discriminators', None),
            quantum_volume=getattr(config, 'quantum_volume', None),
            clops_h=getattr(config, 'clops_h', None),
            supported_features=getattr(config, 'supported_features', []),
            multi_meas_enabled=getattr(config, 'multi_meas_enabled', False),
            timing_constraints=getattr(config, 'timing_constraints', None),
            online_date=getattr(config, 'online_date', None),
            credits_required=getattr(config, 'credits_required', True),
            sample_name=getattr(config, 'sample_name', None),
            description=getattr(config, 'description', None),
        )

    def get_backend_properties(
        self,
        backend_name: str,
        calibration_id: Optional[str] = None,
        updated_before: Optional[datetime] = None
    ) -> Optional[BackendProperties]:
        """
        Get backend calibration properties.

        Args:
            backend_name: Name of the backend
            calibration_id: Optional calibration ID (not used in fake backends)
            updated_before: Optional datetime filter (not used in fake backends)

        Returns:
            BackendProperties or None if backend not found or no properties
        """
        backend = self.get_backend(backend_name)
        if backend is None:
            return None

        try:
            props = backend.properties()
        except Exception:
            # Some backends may not have properties
            return None

        if props is None:
            return None

        # Convert qubit properties
        qubits_list = []
        for qubit_props in props.qubits:
            qubit_nduv_list = []
            for nduv in qubit_props:
                qubit_nduv_list.append(Nduv(
                    date=nduv.date,
                    name=nduv.name,
                    unit=nduv.unit,
                    value=nduv.value
                ))
            qubits_list.append(qubit_nduv_list)

        # Convert gate properties
        gates_list = []
        for gate_prop in props.gates:
            gate_params = []
            for param in gate_prop.parameters:
                gate_params.append(Nduv(
                    date=param.date,
                    name=param.name,
                    unit=param.unit,
                    value=param.value
                ))

            gates_list.append(GateProperties(
                qubits=gate_prop.qubits,
                gate=gate_prop.gate,
                parameters=gate_params
            ))

        # Convert general properties
        general_list = []
        if hasattr(props, 'general') and props.general:
            for gen_prop in props.general:
                general_list.append(Nduv(
                    date=gen_prop.date,
                    name=gen_prop.name,
                    unit=gen_prop.unit,
                    value=gen_prop.value
                ))

        return BackendProperties(
            backend_name=props.backend_name,
            backend_version=props.backend_version,
            last_update_date=props.last_update_date,
            qubits=qubits_list,
            gates=gates_list,
            general=general_list
        )

    def get_backend_status(self, backend_name: str) -> Optional[BackendStatus]:
        """
        Get backend operational status.

        Args:
            backend_name: Name of the backend

        Returns:
            BackendStatus or None if backend not found
        """
        backend = self.get_backend(backend_name)
        if backend is None:
            return None

        status = backend.status()

        return BackendStatus(
            backend_name=status.backend_name,
            backend_version=status.backend_version,
            operational=status.operational,
            status_msg=status.status_msg,
            pending_jobs=status.pending_jobs
        )

    def get_backend_defaults(self, backend_name: str) -> Optional[BackendDefaults]:
        """
        Get backend default pulse calibrations.

        Args:
            backend_name: Name of the backend

        Returns:
            BackendDefaults or None if backend not found or doesn't support defaults
        """
        backend = self.get_backend(backend_name)
        if backend is None:
            return None

        # Check if backend supports OpenPulse
        config = backend.configuration()
        if not getattr(config, 'open_pulse', False):
            # Simulators and non-pulse backends don't support defaults
            return None

        # Most fake backends don't have defaults data
        # This would need to be implemented if pulse-level data is available
        return None


# Global instance
_backend_provider = None


def get_backend_provider() -> BackendProvider:
    """Get the global backend provider instance."""
    global _backend_provider
    if _backend_provider is None:
        _backend_provider = BackendProvider()
    return _backend_provider
