# Server Utils

Utilities for localhost testing with qiskit-ibm-runtime.

## localhost_patch

This module provides a monkey patch for `qiskit-ibm-runtime` to enable localhost testing without modifying the qiskit-ibm-runtime codebase.

### Problem

When using `QiskitRuntimeService` with a localhost URL, the service attempts to validate instances by calling IBM Cloud Global Search API, which fails for localhost servers.

### Solution

The `apply_localhost_patch()` function monkey patches `CloudAccount.list_instances()` to return mock instance data for localhost URLs, preventing any IBM Cloud API calls.

### Usage

```python
import sys
import os

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Apply patch BEFORE importing QiskitRuntimeService
from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

# Now use QiskitRuntimeService normally
from qiskit_ibm_runtime import QiskitRuntimeService

service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token="test-token",
    url="http://localhost:8000",
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
    verify=False
)
```

### How It Works

1. The patch intercepts `CloudAccount.list_instances()` calls
2. If the account URL contains "localhost" or "127.0.0.1", it returns mock instance data
3. Otherwise, it delegates to the original implementation
4. This prevents IBM Cloud API calls while keeping all qiskit-ibm-runtime code unchanged

### Benefits

- ✅ **Zero modifications to qiskit-ibm-runtime codebase**
- ✅ **Works with any version of qiskit-ibm-runtime**
- ✅ **No IBM Cloud API calls during localhost testing**
- ✅ **Easy to apply in any example/test file**
- ✅ **Can be disabled by simply not calling `apply_localhost_patch()`**

### For Other Examples

To use this patch in other example files:

```python
# At the top of your example file:
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.localhost_patch import apply_localhost_patch
apply_localhost_patch()

# Rest of your code...
```
