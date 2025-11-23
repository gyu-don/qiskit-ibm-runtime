"""
Job Manager for Runtime Jobs.

This module manages runtime job execution using QiskitRuntimeLocalService.
"""

import sys
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import threading

# Add parent directory to path to import qiskit_ibm_runtime
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from qiskit_ibm_runtime.fake_provider.local_service import QiskitRuntimeLocalService
from qiskit_ibm_runtime.fake_provider.local_runtime_job import LocalRuntimeJob

from .backend_provider import get_backend_provider


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobInfo:
    """Information about a runtime job."""

    def __init__(
        self,
        job_id: str,
        program_id: str,
        backend_name: str,
        params: Dict[str, Any],
        created_at: datetime
    ):
        """
        Initialize job info.

        Args:
            job_id: Unique job identifier
            program_id: Program ID (e.g., 'sampler', 'estimator')
            backend_name: Backend name
            params: Job parameters
            created_at: Creation timestamp
        """
        self.job_id = job_id
        self.program_id = program_id
        self.backend_name = backend_name
        self.params = params
        self.created_at = created_at
        self.status = JobStatus.QUEUED
        self.runtime_job: Optional[LocalRuntimeJob] = None
        self.error_message: Optional[str] = None
        self.result_data: Optional[Any] = None


class JobManager:
    """
    Manager for runtime jobs.

    Handles job creation, execution, and status tracking.
    """

    def __init__(self):
        """Initialize the job manager."""
        self.service = QiskitRuntimeLocalService()
        self.backend_provider = get_backend_provider()
        self.jobs: Dict[str, JobInfo] = {}
        self._lock = threading.Lock()

    def create_job(
        self,
        program_id: str,
        backend_name: str,
        params: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new runtime job.

        Args:
            program_id: Program ID ('sampler' or 'estimator')
            backend_name: Backend to run on
            params: Job parameters
            options: Runtime options

        Returns:
            Job ID

        Raises:
            ValueError: If backend not found or invalid program
        """
        # Validate backend
        backend = self.backend_provider.get_backend(backend_name)
        if backend is None:
            raise ValueError(f"Backend not found: {backend_name}")

        # Validate program
        if program_id not in ['sampler', 'estimator']:
            raise ValueError(f"Invalid program_id: {program_id}")

        # Generate job ID
        job_id = f"job-{uuid.uuid4()}"

        # Create job info
        job_info = JobInfo(
            job_id=job_id,
            program_id=program_id,
            backend_name=backend_name,
            params=params,
            created_at=datetime.utcnow()
        )

        # Store job
        with self._lock:
            self.jobs[job_id] = job_info

        # Start job execution in background
        thread = threading.Thread(
            target=self._execute_job,
            args=(job_id, backend, options or {})
        )
        thread.daemon = True
        thread.start()

        return job_id

    def _execute_job(
        self,
        job_id: str,
        backend: Any,
        options: Dict[str, Any]
    ) -> None:
        """
        Execute a job in background.

        Args:
            job_id: Job ID
            backend: Backend instance
            options: Runtime options
        """
        with self._lock:
            job_info = self.jobs.get(job_id)
            if job_info is None:
                return

        try:
            # Update status to running
            with self._lock:
                job_info.status = JobStatus.RUNNING

            # Prepare options with backend
            runtime_options = options.copy()
            runtime_options['backend'] = backend

            # Execute job
            runtime_job = self.service._run(
                program_id=job_info.program_id,
                inputs=job_info.params,
                options=runtime_options,
                calibration_id=None
            )

            # Store runtime job
            with self._lock:
                job_info.runtime_job = runtime_job

            # Wait for completion
            result = runtime_job.result()

            # Store result
            with self._lock:
                job_info.status = JobStatus.COMPLETED
                job_info.result_data = result

        except Exception as e:
            # Handle error
            with self._lock:
                job_info.status = JobStatus.FAILED
                job_info.error_message = str(e)

    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """
        Get job information.

        Args:
            job_id: Job ID

        Returns:
            JobInfo or None if not found
        """
        with self._lock:
            return self.jobs.get(job_id)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status.

        Args:
            job_id: Job ID

        Returns:
            Status dictionary or None if not found
        """
        job_info = self.get_job(job_id)
        if job_info is None:
            return None

        status_dict = {
            'id': job_info.job_id,
            'program': {'id': job_info.program_id},
            'backend': job_info.backend_name,
            'state': {
                'status': job_info.status.value,
                'reason': job_info.error_message
            },
            'created': job_info.created_at.isoformat() + 'Z',
            'session_id': job_info.job_id,  # In local mode, session_id = job_id
        }

        return status_dict

    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job result.

        Args:
            job_id: Job ID

        Returns:
            Result dictionary or None if not found or not completed
        """
        job_info = self.get_job(job_id)
        if job_info is None:
            return None

        if job_info.status != JobStatus.COMPLETED:
            return None

        if job_info.result_data is None:
            return None

        # Convert result to dictionary format
        try:
            # For PrimitiveResult, convert to serializable format
            result_dict = self._convert_result_to_dict(job_info.result_data)
            return {
                'results': result_dict,
                'metadata': {}
            }
        except Exception:
            return None

    def _convert_result_to_dict(self, result: Any) -> Any:
        """
        Convert result object to dictionary.

        Args:
            result: Result object

        Returns:
            Serializable dictionary
        """
        # Handle PrimitiveResult from Sampler/Estimator
        if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
            # Result is iterable (list of PubResults)
            return [self._convert_pub_result(pub_result) for pub_result in result]
        return {}

    def _convert_pub_result(self, pub_result: Any) -> Dict[str, Any]:
        """
        Convert PubResult to dictionary.

        Args:
            pub_result: PubResult object

        Returns:
            Dictionary representation
        """
        result_dict = {}

        # Extract data
        if hasattr(pub_result, 'data'):
            data = pub_result.data
            result_dict['data'] = {}

            # For Sampler results
            if hasattr(data, 'meas'):
                meas = data.meas
                if hasattr(meas, 'get_counts'):
                    result_dict['data']['counts'] = meas.get_counts()
                if hasattr(meas, 'get_bitstrings'):
                    bitstrings = meas.get_bitstrings()
                    result_dict['data']['bitstrings'] = [str(bs) for bs in bitstrings]

            # For Estimator results
            if hasattr(data, 'evs'):
                result_dict['data']['expectation_values'] = list(data.evs)
            if hasattr(data, 'stds'):
                result_dict['data']['standard_errors'] = list(data.stds)

        # Extract metadata
        if hasattr(pub_result, 'metadata'):
            result_dict['metadata'] = pub_result.metadata

        return result_dict

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled, False if not found or already completed
        """
        with self._lock:
            job_info = self.jobs.get(job_id)
            if job_info is None:
                return False

            if job_info.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return False

            job_info.status = JobStatus.CANCELLED
            if job_info.runtime_job is not None:
                try:
                    job_info.runtime_job.cancel()
                except Exception:
                    pass

            return True

    def list_jobs(
        self,
        limit: int = 10,
        skip: int = 0,
        backend_name: Optional[str] = None,
        program_id: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List jobs with optional filters.

        Args:
            limit: Maximum number of jobs to return
            skip: Number of jobs to skip
            backend_name: Filter by backend name
            program_id: Filter by program ID
            state: Filter by state

        Returns:
            List of job status dictionaries
        """
        with self._lock:
            jobs = list(self.jobs.values())

        # Apply filters
        if backend_name:
            jobs = [j for j in jobs if j.backend_name == backend_name]
        if program_id:
            jobs = [j for j in jobs if j.program_id == program_id]
        if state:
            jobs = [j for j in jobs if j.status.value == state]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        # Apply pagination
        jobs = jobs[skip:skip + limit]

        # Convert to status dicts
        return [self.get_job_status(j.job_id) for j in jobs]


# Global instance
_job_manager = None


def get_job_manager() -> JobManager:
    """Get the global job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
