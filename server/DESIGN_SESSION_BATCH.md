# Session/Batch Mode Design Document

## Overview

This document describes the design and implementation of Session and Batch execution modes for the Qiskit Runtime REST API server.

## 1. Session vs Batch: Execution Modes

### Session Mode (mode="dedicated")
**Purpose**: Iterative algorithms (VQE, QAOA, parameter optimization)

**Characteristics**:
- Jobs run **sequentially** with queue priority
- Minimal inter-job delay
- Maintains backend reservation for iterative workflows
- Ideal for algorithms that need results from previous jobs to determine next parameters

**Use Cases**:
- VQE (Variational Quantum Eigensolver) optimization loops
- QAOA parameter sweeps with feedback
- Any iterative algorithm requiring multiple rounds

### Batch Mode (mode="batch")
**Purpose**: Parallel execution of independent jobs

**Characteristics**:
- Jobs run **in parallel** (or as parallel as backend allows)
- Classical compilation happens in parallel
- Cost-effective for large workloads
- Jobs are independent and don't wait for each other

**Use Cases**:
- Parameter sweeps without feedback
- Circuit benchmarking
- Randomized benchmarking
- Running multiple independent experiments

## 2. API Specification

Based on `qiskit_ibm_runtime/api/rest/runtime_session.py`, the following endpoints are required:

### 2.1 Create Session/Batch
```
POST /v1/sessions
```

**Request Body**:
```json
{
  "mode": "dedicated" | "batch",
  "backend": "fake_manila",
  "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/local::local",
  "max_ttl": 28800  // Optional: max time-to-live in seconds
}
```

**Response**:
```json
{
  "id": "session-uuid-here",
  "mode": "dedicated",
  "backend": "fake_manila",
  "instance": "crn:...",
  "max_ttl": 28800,
  "created_at": "2024-11-24T10:00:00Z",
  "accepting_jobs": true,
  "active": true
}
```

### 2.2 Get Session Details
```
GET /v1/sessions/{session_id}
```

**Response**:
```json
{
  "id": "session-uuid",
  "mode": "dedicated",
  "backend": "fake_manila",
  "instance": "crn:...",
  "max_ttl": 28800,
  "created_at": "2024-11-24T10:00:00Z",
  "accepting_jobs": true,
  "active": true,
  "elapsed_time": 150,  // seconds since creation
  "jobs": ["job-1", "job-2", "job-3"]
}
```

### 2.3 Close Session (Stop Accepting Jobs)
```
PATCH /v1/sessions/{session_id}
```

**Request Body**:
```json
{
  "accepting_jobs": false
}
```

**Response**: Same as GET session details

### 2.4 Cancel/Terminate Session
```
DELETE /v1/sessions/{session_id}/close
```

**Effect**:
- Stops accepting new jobs
- Cancels all queued jobs
- Marks session as terminated

**Response**: 204 No Content

## 3. Data Models

### 3.1 Session Model

```python
class SessionMode(str, Enum):
    """Session execution mode."""
    DEDICATED = "dedicated"  # Sequential execution (Session)
    BATCH = "batch"          # Parallel execution (Batch)

class SessionInfo:
    """Session information."""
    session_id: str
    mode: SessionMode
    backend_name: str
    instance: str
    max_ttl: Optional[int]  # seconds
    created_at: datetime
    accepting_jobs: bool
    active: bool
    job_ids: List[str]

    # Computed properties
    elapsed_time: int  # seconds since creation
    remaining_time: Optional[int]  # seconds until max_ttl expiration
```

### 3.2 Updated Job Model

Jobs need to be associated with sessions:

```python
class JobInfo:
    job_id: str
    program_id: str
    backend_name: str
    params: Dict[str, Any]
    created_at: datetime
    status: JobStatus
    session_id: Optional[str]  # NEW: Link to session
    # ... existing fields
```

## 4. Architecture

### 4.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Endpoints                     │
│  POST /v1/sessions                                          │
│  GET /v1/sessions/{id}                                      │
│  PATCH /v1/sessions/{id}                                    │
│  DELETE /v1/sessions/{id}/close                             │
│  POST /v1/jobs (modified to accept session_id)              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      SessionManager                          │
│  - create_session(mode, backend, instance, max_ttl)         │
│  - get_session(session_id)                                  │
│  - close_session(session_id)                                │
│  - cancel_session(session_id)                               │
│  - add_job_to_session(session_id, job_id)                   │
│  - is_accepting_jobs(session_id)                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        JobManager                            │
│  - create_job(..., session_id: Optional[str])               │
│  - _execute_job_in_session_mode(job_id, mode)               │
│  - _execute_job_in_batch_mode(job_id)                       │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Session Lifecycle

```
1. Client creates session:
   POST /v1/sessions { mode: "dedicated", backend: "fake_manila" }
   → SessionManager creates SessionInfo
   → Returns session_id

2. Client submits jobs with session_id:
   POST /v1/jobs { ..., session_id: "session-uuid" }
   → JobManager checks if session is accepting jobs
   → JobManager creates job with session_id
   → SessionManager.add_job_to_session(session_id, job_id)

   For DEDICATED mode:
     - Jobs execute sequentially
     - Each job waits for previous job to complete

   For BATCH mode:
     - Jobs execute in parallel
     - No inter-job dependencies

3. Client closes session:
   PATCH /v1/sessions/{id} { accepting_jobs: false }
   → No new jobs accepted
   → Existing jobs continue

4. Session auto-closes:
   - When max_ttl expires
   - Or client calls DELETE /v1/sessions/{id}/close
```

### 4.3 Job Execution Strategies

#### Sequential Execution (Session/Dedicated Mode)
```python
# JobManager maintains a per-session job queue
# Only one job from the session runs at a time

def _execute_session_jobs(session_id: str):
    while True:
        job_id = get_next_queued_job(session_id)
        if job_id is None:
            break
        execute_job(job_id)
        wait_for_completion(job_id)
```

#### Parallel Execution (Batch Mode)
```python
# Jobs from the same batch can run concurrently
# Each job executes in its own thread (existing behavior)

def _execute_batch_jobs(session_id: str):
    job_ids = get_all_queued_jobs(session_id)
    for job_id in job_ids:
        thread = Thread(target=execute_job, args=(job_id,))
        thread.start()
```

## 5. Implementation Plan

### Phase 1: Data Models and SessionManager
1. Create `server/src/models.py` additions:
   - `SessionMode` enum
   - `SessionCreateRequest` model
   - `SessionResponse` model
   - `SessionUpdateRequest` model

2. Create `server/src/session_manager.py`:
   - `SessionInfo` class
   - `SessionManager` class with CRUD operations
   - Thread-safe session storage
   - TTL expiration handling

### Phase 2: API Endpoints
3. Update `server/src/main.py`:
   - Add session endpoints (POST, GET, PATCH, DELETE)
   - Wire up SessionManager

### Phase 3: Job Integration
4. Update `server/src/job_manager.py`:
   - Add `session_id` to `JobInfo`
   - Modify `create_job` to accept `session_id`
   - Implement sequential execution for dedicated mode
   - Maintain parallel execution for batch mode

5. Update `server/src/main.py` job endpoint:
   - Accept optional `session_id` in job creation request
   - Validate session exists and is accepting jobs

### Phase 4: Testing
6. Test with `server/examples/10_session_mode.py`
7. Test with `server/examples/11_batch_mode.py`

## 6. Key Design Decisions

### 6.1 Session Storage
- **Decision**: In-memory storage with thread locks (similar to JobManager)
- **Rationale**: Simple, matches existing architecture, sufficient for mock server
- **Future**: Could be extended to use Redis or database

### 6.2 Job Execution Control
- **Decision**: For dedicated mode, use a per-session queue with a single consumer thread
- **Rationale**: Ensures sequential execution without complex synchronization
- **For batch mode**: Keep existing parallel execution (one thread per job)

### 6.3 Session TTL
- **Decision**: Background thread checks for expired sessions every 10 seconds
- **Rationale**: Simple periodic cleanup, low overhead
- **Implementation**: Mark session as inactive, stop accepting jobs, let existing jobs finish

### 6.4 No Session Required
- **Decision**: Jobs can still be created without a session_id (backward compatible)
- **Rationale**: Maintains compatibility with existing examples (01-09)

## 7. API Contract Examples

### Example: VQE with Session Mode

```python
# Create session
with Session(backend=backend) as session:
    # session._create_session() calls:
    # POST /v1/sessions
    # { "mode": "dedicated", "backend": "fake_manila", ... }
    # Response: { "id": "session-abc123", ... }

    estimator = Estimator(mode=session)

    for iteration in range(5):
        # Each job is submitted with session_id
        # POST /v1/jobs
        # {
        #   "program_id": "estimator",
        #   "backend": "fake_manila",
        #   "params": {...},
        #   "session_id": "session-abc123"  # Added by Estimator
        # }
        job = estimator.run([circuit, observable])
        result = job.result()
        # Use result to compute next parameters

# On exit, Session.__exit__() calls:
# PATCH /v1/sessions/session-abc123
# { "accepting_jobs": false }
```

### Example: Parameter Sweep with Batch Mode

```python
# Create batch
with Batch(backend=backend) as batch:
    # batch._create_session() calls:
    # POST /v1/sessions
    # { "mode": "batch", "backend": "fake_manila", ... }
    # Response: { "id": "session-xyz789", ... }

    sampler = Sampler(mode=batch)

    jobs = []
    for params in param_sets:
        # All jobs submitted to same batch
        # Jobs run in parallel
        job = sampler.run([circuit])
        jobs.append(job)

    # Collect results (jobs may complete in any order)
    for job in jobs:
        result = job.result()

# On exit: PATCH /v1/sessions/session-xyz789 { "accepting_jobs": false }
```

## 8. Error Handling

### Error Scenarios:
1. **Session not found**: 404 error
2. **Session not accepting jobs**: 400 error with message "Session is closed"
3. **Session expired (TTL)**: 400 error with message "Session has expired"
4. **Backend mismatch**: 400 error if job's backend != session's backend
5. **Invalid mode**: 400 error if mode not in ["dedicated", "batch"]

## 9. Testing Strategy

### Unit Tests:
- SessionManager CRUD operations
- Session TTL expiration
- Job-session association

### Integration Tests:
- End-to-end session creation and job submission
- Sequential execution in dedicated mode
- Parallel execution in batch mode
- Session closure and cleanup

### Example Tests:
- Run `10_session_mode.py` successfully
- Run `11_batch_mode.py` successfully
- Verify job execution order in dedicated mode
- Verify parallel execution in batch mode

## 10. Future Enhancements

1. **Session metrics**: Track total jobs, success rate, etc.
2. **Session queueing**: Queue sessions if backend is busy
3. **Session priority**: Higher priority for sessions vs standalone jobs
4. **Session persistence**: Save to database for crash recovery
5. **Multi-backend sessions**: Support sessions across multiple backends
6. **Session monitoring**: Real-time session status updates via WebSocket

---

**Document Version**: 1.0
**Date**: 2024-11-24
**Author**: Claude Code
