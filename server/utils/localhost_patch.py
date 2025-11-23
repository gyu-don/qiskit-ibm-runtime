"""
Monkey patch for qiskit-ibm-runtime to enable localhost testing.

This module patches CloudAccount.list_instances() to return mock data
for localhost URLs, preventing IBM Cloud API calls during local development.

Usage:
    Import this module at the top of your example scripts:

    from utils.localhost_patch import apply_localhost_patch
    apply_localhost_patch()

    # Then use QiskitRuntimeService normally
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token="test-token",
        url="http://localhost:8000",
        instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
        verify=False
    )
"""

from typing import List, Dict, Any


def apply_localhost_patch() -> None:
    """
    Apply monkey patch to CloudAccount.list_instances() for localhost support.

    This patches the list_instances method to return mock instance data when
    the account URL contains 'localhost' or '127.0.0.1', preventing calls to
    IBM Cloud Global Search API during local testing.
    """
    from qiskit_ibm_runtime.accounts.account import CloudAccount

    # Save original method
    _original_list_instances = CloudAccount.list_instances

    def _patched_list_instances(self) -> List[Dict[str, Any]]:
        """Patched list_instances that returns mock data for localhost."""
        # Check if this is a localhost URL
        if self.url and ("localhost" in self.url or "127.0.0.1" in self.url):
            # Return mock instance data
            return [{
                "crn": (
                    self.instance
                    if self.instance
                    else "crn:v1:bluemix:public:quantum-computing:us-east:a/local::local"
                ),
                "plan": "lite",
                "name": "local-test-instance",
                "tags": [],
                "pricing_type": "free"
            }]

        # For non-localhost URLs, use original implementation
        return _original_list_instances(self)

    # Apply the patch
    CloudAccount.list_instances = _patched_list_instances
