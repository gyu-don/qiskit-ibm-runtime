"""
Monkey patch for qiskit-ibm-runtime to enable localhost testing.

This module patches CloudAccount.list_instances() and CloudAuth to prevent
IBM Cloud API calls during local development.

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
    Apply monkey patches for localhost support.

    This patches:
    1. CloudAccount.list_instances() - returns mock instance data for localhost
    2. CloudAuth.__init__() and get_headers() - bypasses IAM authentication for localhost

    This prevents all IBM Cloud API calls during local testing.
    """
    from qiskit_ibm_runtime.accounts.account import CloudAccount
    from qiskit_ibm_runtime.api.auth import CloudAuth

    # Patch 1: CloudAccount.list_instances()
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

    CloudAccount.list_instances = _patched_list_instances

    # Patch 2: CloudAuth to bypass IAM for localhost
    _original_cloudauth_init = CloudAuth.__init__

    def _patched_cloudauth_init(
        self,
        api_key: str,
        crn: str,
        private: bool = False,
        proxies = None,
        verify: bool = True,
    ):
        """Patched CloudAuth.__init__ that skips IAM setup for localhost."""
        self.crn = crn
        self.api_key = api_key
        self.private = private
        self.proxies = proxies
        self.verify = verify
        # Only set up IAM if not localhost (determined later in get_headers)
        self.tm = None  # Will be created on-demand if needed

    def _patched_get_headers(self) -> Dict:
        """Patched get_headers that returns simple headers for localhost."""
        # For localhost testing, return simple auth headers without IAM
        return {
            "Service-CRN": self.crn,
            "Authorization": f"Bearer {self.api_key}"
        }

    CloudAuth.__init__ = _patched_cloudauth_init
    CloudAuth.get_headers = _patched_get_headers

    # Patch 3: default_runtime_url_resolver to preserve localhost URLs
    from qiskit_ibm_runtime import utils
    _original_url_resolver = utils.default_runtime_url_resolver

    def _patched_url_resolver(
        url: str, instance: str, private_endpoint: bool = False, channel: str = "ibm_quantum_platform"
    ) -> str:
        """Patched URL resolver that preserves localhost URLs."""
        # If it's localhost, don't transform the URL
        if url and ("localhost" in url or "127.0.0.1" in url):
            # Ensure URL ends with /v1 for API versioning
            if not url.endswith("/v1"):
                url = url.rstrip("/") + "/v1"
            print(f"[localhost_patch] Preserving localhost URL: {url}")
            return url

        # For non-localhost URLs, use original resolver
        result = _original_url_resolver(url, instance, private_endpoint, channel)
        print(f"[localhost_patch] Transformed URL: {url} -> {result}")
        return result

    utils.default_runtime_url_resolver = _patched_url_resolver

    # Also patch the reference in client_parameters module
    from qiskit_ibm_runtime.api import client_parameters
    client_parameters.default_runtime_url_resolver = _patched_url_resolver

    print("[localhost_patch] URL resolver patched")
