# Qiskit Runtime Backend API Server

A FastAPI-based mock server implementing the IBM Qiskit Runtime Backend API endpoints.

## Overview

This server provides a mock implementation of the Qiskit Runtime Backend API as specified in the [IBM Quantum Cloud API documentation](https://quantum.cloud.ibm.com/docs/en/api/qiskit-runtime-rest/tags/backends).

**API Version:** 2025-05-01

## Features

- Full type annotations using Pydantic models
- OpenAPI/Swagger documentation
- Authentication middleware
- API versioning support
- Comprehensive docstrings

## Project Structure

```
server/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application and endpoints
│   └── models.py            # Pydantic data models
├── examples/
│   ├── 01_basic_connection.py      # Basic connection example
│   ├── 02_list_backends.py         # List backends
│   ├── 03_backend_details.py       # Get backend details
│   ├── 04_test_all_endpoints.py    # Test all endpoints
│   ├── 05_save_account.py          # Save account config
│   ├── 06_custom_headers.py        # Custom HTTP headers
│   ├── 07_direct_http.py           # Direct HTTP calls
│   └── README.md                   # Examples documentation
├── docs/
│   ├── API_SPECIFICATION.md        # Detailed API specifications
│   ├── CLIENT_SERVER_MAPPING.md    # Client/server mapping
│   └── DEVELOPMENT_GUIDE.md        # Implementation guide
├── tests/
│   └── test_api.py                 # API tests
├── requirements.txt         # Python dependencies
├── IMPLEMENTATION_STATUS.md # Current status and roadmap
└── README.md               # This file
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

### Development Mode

```bash
cd server
python -m src.main
```

Or using uvicorn directly:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

You will see request logs like:
```
→ GET /v1/backends from 127.0.0.1
← ✓ 200 GET /v1/backends (12.34ms)
```

See `docs/LOGGING.md` for detailed logging configuration.

### Production Mode

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/backends` | List all available backends |
| GET | `/v1/backends/{id}/configuration` | Get backend configuration |
| GET | `/v1/backends/{id}/defaults` | Get default pulse calibrations |
| GET | `/v1/backends/{id}/properties` | Get backend properties |
| GET | `/v1/backends/{id}/status` | Get backend operational status |

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |

## Authentication

All backend endpoints require the following headers:

- `Authorization: Bearer YOUR-TOKEN`
- `Service-CRN: YOUR-SERVICE-CRN`
- `IBM-API-Version: 2025-05-01`

Example request:
```bash
curl -X GET "http://localhost:8000/v1/backends" \
  -H "Authorization: Bearer your-token-here" \
  -H "Service-CRN: crn:v1:bluemix:public:quantum-computing:..." \
  -H "IBM-API-Version: 2025-05-01"
```

## Using the Client

### Quick Start with qiskit-ibm-runtime

After starting the server, you can connect using the qiskit-ibm-runtime client:

```python
from qiskit_ibm_runtime import QiskitRuntimeService

# Connect to local server
service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token="test-token",
    url="http://localhost:8000",
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/test:test::",
    verify=False  # Disable SSL for localhost
)

# Use the service
backends = service.backends()
```

### Example Scripts

The `examples/` directory contains ready-to-run examples:

1. **01_basic_connection.py** - Basic connection setup
2. **02_list_backends.py** - List all backends
3. **03_backend_details.py** - Get configuration, properties, status
4. **04_test_all_endpoints.py** - Test all 5 backend endpoints
5. **05_save_account.py** - Save/load account configuration
6. **06_custom_headers.py** - HTTP headers and authentication
7. **07_direct_http.py** - Direct HTTP API calls (using `requests`)

Run any example:
```bash
python examples/01_basic_connection.py
```

See `examples/README.md` for detailed documentation (日本語).

## Data Models

The server uses Pydantic models for request/response validation. Key models include:

- `BackendsResponse` - List of backends
- `BackendConfiguration` - Complete backend configuration
- `BackendProperties` - Calibration properties
- `BackendStatus` - Operational status
- `BackendDefaults` - Pulse calibrations

See `src/models.py` for complete model definitions.

## Development

### Type Checking

```bash
mypy src/
```

### Code Formatting

```bash
black src/
ruff check src/
```

### Testing

```bash
pytest
```

## Implementation Status

This is a **mock/specification server**. All endpoints currently return:
- HTTP 501 (Not Implemented)

The purpose is to define the API interface, types, and documentation structure.

To implement actual functionality:
1. Replace the `raise HTTPException(status_code=501, ...)` with real logic
2. Add database/storage layer for backend data
3. Implement authentication validation
4. Add caching for frequently accessed data

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **`API_SPECIFICATION.md`** - Complete API reference with examples
- **`CLIENT_SERVER_MAPPING.md`** - Client-to-server mapping guide
- **`DEVELOPMENT_GUIDE.md`** - Implementation guide
- **`LOGGING.md`** - Logging configuration and troubleshooting

## Related Resources

- [Qiskit Runtime Documentation](https://quantum.ibm.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## License

This mock server is for development and testing purposes.
