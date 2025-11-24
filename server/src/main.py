"""
FastAPI Backend Server for Qiskit Runtime API.

This module implements the Qiskit Runtime Backend API endpoints as specified in:
https://quantum.cloud.ibm.com/docs/en/api/qiskit-runtime-rest/tags/backends

API Version: 2025-05-01 (IBM-API-Version header)

Endpoints:
- GET  /v1/backends                        - List all backends
- GET  /v1/backends/{id}/configuration     - Get backend configuration
- GET  /v1/backends/{id}/defaults          - Get default pulse calibrations
- GET  /v1/backends/{id}/properties        - Get backend properties
- GET  /v1/backends/{id}/status            - Get backend status
"""

from datetime import datetime
from typing import List, Optional
import logging
import time
import json
from fastapi import FastAPI, Header, HTTPException, Query, Path, Depends, Request
from fastapi.responses import JSONResponse

from qiskit_ibm_runtime.utils import RuntimeEncoder

from .models import (
    BackendsResponse,
    BackendConfiguration,
    BackendDefaults,
    BackendProperties,
    BackendStatus,
    ErrorResponse,
    ErrorDetail,
    JobCreateRequest,
    JobResponse,
    JobResultResponse,
    JobListResponse,
    JobProgram,
    JobState,
    SessionCreateRequest,
    SessionResponse,
    SessionUpdateRequest,
)
from .backend_provider import get_backend_provider
from .job_manager import get_job_manager
from .session_manager import get_session_manager


# ============================================================================
# Logging Configuration
# ============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("qiskit_runtime_server")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Qiskit Runtime Backend API",
    description="Mock server for IBM Qiskit Runtime Backend API",
    version="2025-05-01",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# Request Logging Middleware
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming HTTP requests and responses.

    Logs:
    - Request method and path
    - Client IP address
    - Request headers (selected)
    - Response status code
    - Processing time
    """
    start_time = time.time()

    # Extract client info
    client_host = request.client.host if request.client else "unknown"

    # Log request
    logger.info(f"→ {request.method} {request.url.path} from {client_host}")

    # Log important headers
    if "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        # Mask token for security
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            masked_token = token[:10] + "..." if len(token) > 10 else "***"
            logger.debug(f"  Auth: Bearer {masked_token}")

    if "ibm-api-version" in request.headers:
        logger.debug(f"  API Version: {request.headers['ibm-api-version']}")

    if "service-crn" in request.headers:
        crn = request.headers["service-crn"]
        # Show abbreviated CRN
        if len(crn) > 50:
            logger.debug(f"  Service-CRN: {crn[:47]}...")
        else:
            logger.debug(f"  Service-CRN: {crn}")

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log response
    status_emoji = "✓" if response.status_code < 400 else "✗"
    logger.info(
        f"← {status_emoji} {response.status_code} {request.method} {request.url.path} "
        f"({process_time*1000:.2f}ms)"
    )

    return response


# ============================================================================
# Dependencies for Authentication and Headers
# ============================================================================

async def verify_api_version(
    ibm_api_version: str = Header(
        ...,
        alias="IBM-API-Version",
        description="API version (e.g., '2025-05-01')"
    )
) -> str:
    """
    Verify IBM-API-Version header is present.

    Args:
        ibm_api_version: IBM API version from header

    Returns:
        The API version string

    Raises:
        HTTPException: If API version is not supported
    """
    supported_versions = ["2024-01-01", "2025-01-01", "2025-05-01"]
    if ibm_api_version not in supported_versions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported API version. Supported versions: {supported_versions}"
        )
    return ibm_api_version


async def verify_authorization(
    authorization: str = Header(
        ...,
        description="Bearer token for authentication"
    ),
    service_crn: str = Header(
        ...,
        alias="Service-CRN",
        description="IBM Cloud service instance CRN"
    )
) -> dict:
    """
    Verify authorization headers.

    Args:
        authorization: Bearer token
        service_crn: Service instance CRN

    Returns:
        Dictionary with auth info

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected 'Bearer <token>'"
        )

    # In a real implementation, validate the token and CRN here
    # For mock purposes, we just verify they're present

    return {
        "token": authorization.replace("Bearer ", ""),
        "service_crn": service_crn
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Custom error response handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            errors=[ErrorDetail(message=str(exc.detail), code=None)],
            trace=None,
            status_code=exc.status_code
        ).model_dump()
    )


# ============================================================================
# Backend Endpoints
# ============================================================================

@app.get(
    "/v1/backends",
    response_model=BackendsResponse,
    tags=["backends"],
    summary="List Your Backends",
    description="""
    Returns a list of all the backends your service instance has access to.

    Required IAM action: quantum-computing.device.read

    The response includes basic backend information. Use the `fields` query parameter
    to request additional computed fields like wait_time_seconds.
    """
)
async def list_backends(
    fields: Optional[str] = Query(
        None,
        description="Comma-separated list of additional fields (e.g., 'wait_time_seconds')"
    ),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
) -> BackendsResponse:
    """
    List all available backends.

    Args:
        fields: Optional comma-separated list of additional fields to include
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        BackendsResponse with list of available backends

    Implementation notes:
        - Returns all backends accessible to the authenticated service instance
        - If fields includes 'wait_time_seconds', computes estimated wait time
        - Generates audit event: quantum-computing.device.read
    """
    provider = get_backend_provider()
    return provider.list_backends(fields=fields)


@app.get(
    "/v1/backends/{id}/configuration",
    tags=["backends"],
    summary="Get Backend Configuration",
    description="""
    Returns the complete configuration of a specific backend.

    Required IAM action: quantum-computing.device.read

    The configuration includes quantum system properties, gate definitions,
    topology, timing constraints, and supported features.
    """
)
async def get_backend_configuration(
    backend_id: str = Path(
        ...,
        description="Backend identifier (e.g., 'ibmq_armonk')",
        alias="id"
    ),
    calibration_id: Optional[str] = Query(
        None,
        description="Optional calibration ID to get configuration for specific calibration"
    ),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
):
    """
    Get backend configuration.

    Args:
        backend_id: Unique backend identifier
        calibration_id: Optional specific calibration ID
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        BackendConfiguration with complete backend specs

    Raises:
        HTTPException: 404 if backend not found

    Implementation notes:
        - If calibration_id provided, returns config for that calibration
        - Otherwise returns latest configuration
        - Includes gate definitions, coupling map, processor type, etc.
        - Generates audit event: quantum-computing.device.read
    """
    provider = get_backend_provider()
    config = provider.get_backend_configuration(backend_id, calibration_id)

    if config is None:
        raise HTTPException(
            status_code=404,
            detail=f"Backend not found: {backend_id}"
        )

    return config


@app.get(
    "/v1/backends/{id}/defaults",
    response_model=BackendDefaults,
    tags=["backends"],
    summary="Get Backend Default Settings",
    description="""
    Returns default pulse-level calibrations and command definitions.

    Required IAM action: quantum-computing.device.read

    Note: Simulator backends may not support this endpoint and will return 404.
    """
)
async def get_backend_defaults(
    backend_id: str = Path(
        ...,
        description="Backend identifier",
        alias="id"
    ),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
) -> BackendDefaults:
    """
    Get default pulse calibrations.

    Args:
        backend_id: Unique backend identifier
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        BackendDefaults with pulse calibrations and command definitions

    Raises:
        HTTPException: 404 if backend not found or doesn't support defaults

    Implementation notes:
        - Only available for OpenPulse-enabled backends
        - Simulators typically do not support this endpoint
        - Returns qubit/measurement frequencies, pulse library, and gate->pulse mappings
        - Generates audit event: quantum-computing.device.read
    """
    provider = get_backend_provider()
    defaults = provider.get_backend_defaults(backend_id)

    if defaults is None:
        raise HTTPException(
            status_code=404,
            detail=f"Backend defaults not available for: {backend_id}"
        )

    return defaults


@app.get(
    "/v1/backends/{id}/properties",
    response_model=BackendProperties,
    tags=["backends"],
    summary="Get Backend Properties",
    description="""
    Returns calibration properties for qubits and gates.

    Required IAM action: quantum-computing.device.read

    Properties include T1, T2, readout errors, gate errors, gate times,
    and other time-stamped calibration data.
    """
)
async def get_backend_properties(
    backend_id: str = Path(
        ...,
        description="Backend identifier",
        alias="id"
    ),
    calibration_id: Optional[str] = Query(
        None,
        description="Optional calibration ID to get properties for specific calibration"
    ),
    updated_before: Optional[datetime] = Query(
        None,
        description="Get properties from before this timestamp (ISO 8601 format)"
    ),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
) -> BackendProperties:
    """
    Get backend calibration properties.

    Args:
        backend_id: Unique backend identifier
        calibration_id: Optional specific calibration ID
        updated_before: Optional datetime to get historical properties
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        BackendProperties with calibration data

    Raises:
        HTTPException: 404 if backend not found

    Implementation notes:
        - Returns time-stamped calibration measurements
        - If updated_before specified, returns properties from that time
        - If calibration_id specified, returns that specific calibration
        - Includes per-qubit properties (T1, T2, frequency, readout_error)
        - Includes per-gate properties (gate_error, gate_length)
        - Generates audit event: quantum-computing.device.read
    """
    provider = get_backend_provider()
    properties = provider.get_backend_properties(backend_id, calibration_id, updated_before)

    if properties is None:
        raise HTTPException(
            status_code=404,
            detail=f"Backend properties not available for: {backend_id}"
        )

    return properties


@app.get(
    "/v1/backends/{id}/status",
    response_model=BackendStatus,
    tags=["backends"],
    summary="Get Backend Status",
    description="""
    Returns real-time operational status of a backend.

    Required IAM action: quantum-computing.device.read

    Status includes whether the backend is operational and queue information.
    """
)
async def get_backend_status(
    backend_id: str = Path(
        ...,
        description="Backend identifier",
        alias="id"
    ),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
) -> BackendStatus:
    """
    Get backend operational status.

    Args:
        backend_id: Unique backend identifier
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        BackendStatus with operational status and queue info

    Raises:
        HTTPException: 404 if backend not found

    Implementation notes:
        - Returns real-time status (operational/down/maintenance)
        - Includes current queue length (pending_jobs)
        - Status is updated frequently (near real-time)
        - Generates audit event: quantum-computing.device.read
    """
    provider = get_backend_provider()
    status = provider.get_backend_status(backend_id)

    if status is None:
        raise HTTPException(
            status_code=404,
            detail=f"Backend not found: {backend_id}"
        )

    return status


# ============================================================================
# Job Endpoints
# ============================================================================

@app.post(
    "/v1/jobs",
    response_model=JobResponse,
    status_code=201,
    tags=["jobs"],
    summary="Create Runtime Job",
    description="""
    Create and execute a runtime job (sampler or estimator).

    Required IAM action: quantum-computing.job.create
    """
)
async def create_job(
    request: JobCreateRequest,
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
) -> JobResponse:
    """
    Create a new runtime job.

    Args:
        request: Job creation request
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        JobResponse with job ID and initial status

    Raises:
        HTTPException: 400 if invalid parameters, 404 if backend not found
    """
    job_manager = get_job_manager()

    try:
        job_id = job_manager.create_job(
            program_id=request.program_id,
            backend_name=request.backend,
            params=request.params,
            options=request.options,
            session_id=request.session_id
        )

        # Get job status
        status = job_manager.get_job_status(job_id)

        return JobResponse(
            id=status['id'],
            program=JobProgram(id=status['program']['id']),
            backend=status['backend'],
            state=JobState(
                status=status['state']['status'],
                reason=status['state']['reason']
            ),
            created=status['created'],
            session_id=status['session_id']
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/v1/jobs/{job_id}",
    response_model=JobResponse,
    tags=["jobs"],
    summary="Get Job Status",
    description="""
    Get the status of a runtime job.

    Required IAM action: quantum-computing.job.read
    """
)
async def get_job_status_endpoint(
    job_id: str = Path(..., description="Job ID"),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
) -> JobResponse:
    """
    Get job status.

    Args:
        job_id: Job ID
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        JobResponse with current status

    Raises:
        HTTPException: 404 if job not found
    """
    job_manager = get_job_manager()
    status = job_manager.get_job_status(job_id)

    if status is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return JobResponse(
        id=status['id'],
        program=JobProgram(id=status['program']['id']),
        backend=status['backend'],
        state=JobState(
            status=status['state']['status'],
            reason=status['state']['reason']
        ),
        created=status['created'],
        session_id=status['session_id']
    )


@app.get(
    "/v1/jobs/{job_id}/results",
    tags=["jobs"],
    summary="Get Job Results",
    description="""
    Get the results of a completed job.

    Required IAM action: quantum-computing.job.read
    """
)
async def get_job_results(
    job_id: str = Path(..., description="Job ID"),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
):
    """
    Get job results.

    Args:
        job_id: Job ID
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        JSONResponse with results serialized using RuntimeEncoder

    Raises:
        HTTPException: 404 if job not found, 400 if job not completed
    """
    job_manager = get_job_manager()

    # Check if job exists
    status = job_manager.get_job_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Check if job is completed
    if status['state']['status'] != 'COMPLETED':
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {status['state']['status']}"
        )

    # Get results (PrimitiveResult object)
    result = job_manager.get_job_result(job_id)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve results")

    # Serialize using RuntimeEncoder to preserve Qiskit object types
    # The client expects the result directly, not wrapped in a dict
    json_str = json.dumps(result, cls=RuntimeEncoder)
    return JSONResponse(content=json.loads(json_str))


@app.delete(
    "/v1/jobs/{job_id}",
    status_code=204,
    tags=["jobs"],
    summary="Cancel Job",
    description="""
    Cancel a running or queued job.

    Required IAM action: quantum-computing.job.delete
    """
)
async def cancel_job(
    job_id: str = Path(..., description="Job ID"),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
):
    """
    Cancel a job.

    Args:
        job_id: Job ID
        api_version: IBM API version from header
        auth: Authentication information

    Raises:
        HTTPException: 404 if job not found
    """
    job_manager = get_job_manager()

    if not job_manager.cancel_job(job_id):
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return None


@app.get(
    "/v1/jobs",
    response_model=JobListResponse,
    tags=["jobs"],
    summary="List Jobs",
    description="""
    List runtime jobs with optional filters.

    Required IAM action: quantum-computing.job.read
    """
)
async def list_jobs(
    limit: int = Query(10, description="Maximum number of jobs to return", ge=1, le=100),
    skip: int = Query(0, description="Number of jobs to skip", ge=0),
    backend: Optional[str] = Query(None, description="Filter by backend name"),
    program: Optional[str] = Query(None, description="Filter by program ID"),
    state: Optional[str] = Query(None, description="Filter by job state"),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
) -> JobListResponse:
    """
    List jobs.

    Args:
        limit: Maximum number of jobs to return
        skip: Number of jobs to skip
        backend: Filter by backend name
        program: Filter by program ID
        state: Filter by state
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        JobListResponse with list of jobs
    """
    job_manager = get_job_manager()

    job_statuses = job_manager.list_jobs(
        limit=limit,
        skip=skip,
        backend_name=backend,
        program_id=program,
        state=state
    )

    jobs = [
        JobResponse(
            id=status['id'],
            program=JobProgram(id=status['program']['id']),
            backend=status['backend'],
            state=JobState(
                status=status['state']['status'],
                reason=status['state']['reason']
            ),
            created=status['created'],
            session_id=status['session_id']
        )
        for status in job_statuses
    ]

    return JobListResponse(
        jobs=jobs,
        count=len(jobs)
    )


# ============================================================================
# Session Endpoints
# ============================================================================

@app.post(
    "/v1/sessions",
    response_model=SessionResponse,
    status_code=201,
    tags=["sessions"],
    summary="Create Runtime Session",
    description="""
    Create a new runtime session for grouping related jobs.

    Sessions support two modes:
    - 'dedicated': Jobs run sequentially (for iterative algorithms like VQE)
    - 'batch': Jobs run in parallel (for independent workloads)

    Required IAM action: quantum-computing.session.create
    """
)
async def create_session(
    request: SessionCreateRequest,
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
) -> SessionResponse:
    """
    Create a new runtime session.

    Args:
        request: Session creation request
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        SessionResponse with session ID and details

    Raises:
        HTTPException: 400 if invalid parameters
    """
    session_manager = get_session_manager()

    try:
        session_id = session_manager.create_session(
            mode=request.mode,
            backend_name=request.backend,
            instance=request.instance,
            max_ttl=request.max_ttl
        )

        # Get session details
        session_info = session_manager.get_session(session_id)
        if session_info is None:
            raise HTTPException(status_code=500, detail="Failed to create session")

        session_dict = session_info.to_dict()

        return SessionResponse(**session_dict)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/v1/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["sessions"],
    summary="Get Session Details",
    description="""
    Get details of a runtime session.

    Required IAM action: quantum-computing.session.read
    """
)
async def get_session_details(
    session_id: str = Path(..., description="Session ID"),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
) -> SessionResponse:
    """
    Get session details.

    Args:
        session_id: Session ID
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        SessionResponse with current session details

    Raises:
        HTTPException: 404 if session not found
    """
    session_manager = get_session_manager()
    session_info = session_manager.get_session(session_id)

    if session_info is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session_dict = session_info.to_dict()
    return SessionResponse(**session_dict)


@app.patch(
    "/v1/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["sessions"],
    summary="Update Session",
    description="""
    Update session settings (e.g., stop accepting new jobs).

    Required IAM action: quantum-computing.session.update
    """
)
async def update_session(
    request: SessionUpdateRequest,
    session_id: str = Path(..., description="Session ID"),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
) -> SessionResponse:
    """
    Update session settings.

    Args:
        request: Session update request
        session_id: Session ID
        api_version: IBM API version from header
        auth: Authentication information

    Returns:
        SessionResponse with updated session details

    Raises:
        HTTPException: 404 if session not found
    """
    session_manager = get_session_manager()

    # Update session
    if not session_manager.close_session(session_id, accepting_jobs=request.accepting_jobs):
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Get updated details
    session_info = session_manager.get_session(session_id)
    if session_info is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session_dict = session_info.to_dict()
    return SessionResponse(**session_dict)


@app.delete(
    "/v1/sessions/{session_id}/close",
    status_code=204,
    tags=["sessions"],
    summary="Cancel Session",
    description="""
    Cancel a session and all its queued jobs.

    Required IAM action: quantum-computing.session.delete
    """
)
async def cancel_session(
    session_id: str = Path(..., description="Session ID"),
    api_version: str = Depends(verify_api_version),
    auth: dict = Depends(verify_authorization),
):
    """
    Cancel a session.

    Args:
        session_id: Session ID
        api_version: IBM API version from header
        auth: Authentication information

    Raises:
        HTTPException: 404 if session not found
    """
    session_manager = get_session_manager()

    if not session_manager.cancel_session(session_id):
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return None


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get(
    "/health",
    tags=["system"],
    summary="Health Check",
    description="Simple health check endpoint to verify server is running"
)
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        Dictionary with status information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2025-05-01"
    }


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get(
    "/",
    tags=["system"],
    summary="API Information",
    description="Root endpoint with API information"
)
async def root() -> dict:
    """
    Root endpoint with API information.

    Returns:
        Dictionary with API metadata
    """
    return {
        "name": "Qiskit Runtime Backend API",
        "version": "2025-05-01",
        "documentation": "/docs",
        "endpoints": {
            "backends": "/v1/backends",
            "health": "/health"
        }
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("="*60)
    logger.info("Starting Qiskit Runtime Backend API Server")
    logger.info("="*60)
    logger.info("Server: http://0.0.0.0:8000")
    logger.info("Docs:   http://0.0.0.0:8000/docs")
    logger.info("ReDoc:  http://0.0.0.0:8000/redoc")
    logger.info("="*60)

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,  # Enable access logs
        use_colors=True,  # Colorful logs
    )
