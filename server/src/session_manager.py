"""
Session Manager for Runtime Sessions.

This module manages runtime sessions (dedicated mode and batch mode).
Sessions group related jobs and control their execution order.
"""

import uuid
import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum


class SessionMode(str, Enum):
    """Session execution mode."""
    DEDICATED = "dedicated"  # Sequential execution
    BATCH = "batch"          # Parallel execution


class SessionInfo:
    """Information about a runtime session."""

    def __init__(
        self,
        session_id: str,
        mode: SessionMode,
        backend_name: str,
        instance: Optional[str] = None,
        max_ttl: Optional[int] = None,
        created_at: Optional[datetime] = None
    ):
        """
        Initialize session info.

        Args:
            session_id: Unique session identifier
            mode: Session mode (dedicated or batch)
            backend_name: Backend name
            instance: IBM Cloud instance CRN
            max_ttl: Maximum time-to-live in seconds
            created_at: Creation timestamp
        """
        self.session_id = session_id
        self.mode = mode
        self.backend_name = backend_name
        self.instance = instance
        self.max_ttl = max_ttl
        self.created_at = created_at or datetime.utcnow()
        self.accepting_jobs = True
        self.active = True
        self.job_ids: List[str] = []

    def elapsed_time(self) -> int:
        """
        Get elapsed time since session creation.

        Returns:
            Elapsed time in seconds
        """
        delta = datetime.utcnow() - self.created_at
        return int(delta.total_seconds())

    def remaining_time(self) -> Optional[int]:
        """
        Get remaining time until TTL expiration.

        Returns:
            Remaining time in seconds, or None if no TTL set
        """
        if self.max_ttl is None:
            return None

        elapsed = self.elapsed_time()
        remaining = self.max_ttl - elapsed
        return max(0, remaining)

    def is_expired(self) -> bool:
        """
        Check if session has expired.

        Returns:
            True if session has exceeded max_ttl
        """
        if self.max_ttl is None:
            return False

        return self.elapsed_time() >= self.max_ttl

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session info to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'id': self.session_id,
            'mode': self.mode.value if isinstance(self.mode, SessionMode) else self.mode,
            'backend': self.backend_name,
            'instance': self.instance,
            'max_ttl': self.max_ttl,
            'created_at': self.created_at.isoformat() + 'Z',
            'accepting_jobs': self.accepting_jobs,
            'active': self.active,
            'elapsed_time': self.elapsed_time(),
            'jobs': self.job_ids.copy()
        }


class SessionManager:
    """
    Manager for runtime sessions.

    Handles session creation, lifecycle management, and job association.
    """

    def __init__(self):
        """Initialize the session manager."""
        self.sessions: Dict[str, SessionInfo] = {}
        self._lock = threading.Lock()
        self._ttl_check_thread: Optional[threading.Thread] = None
        self._stop_ttl_check = threading.Event()
        self._start_ttl_checker()

    def _start_ttl_checker(self):
        """Start background thread to check for expired sessions."""
        if self._ttl_check_thread is not None and self._ttl_check_thread.is_alive():
            return

        def check_ttl():
            """Periodically check for expired sessions."""
            while not self._stop_ttl_check.wait(timeout=10):
                self._check_expired_sessions()

        self._ttl_check_thread = threading.Thread(target=check_ttl, daemon=True)
        self._ttl_check_thread.start()

    def _check_expired_sessions(self):
        """Mark expired sessions as inactive."""
        with self._lock:
            for session in self.sessions.values():
                if session.is_expired() and session.active:
                    session.active = False
                    session.accepting_jobs = False

    def create_session(
        self,
        mode: str,
        backend_name: str,
        instance: Optional[str] = None,
        max_ttl: Optional[int] = None
    ) -> str:
        """
        Create a new session.

        Args:
            mode: Session mode ('dedicated' or 'batch')
            backend_name: Backend to use
            instance: IBM Cloud instance CRN
            max_ttl: Maximum time-to-live in seconds

        Returns:
            Session ID

        Raises:
            ValueError: If mode is invalid
        """
        # Validate mode
        if mode not in [SessionMode.DEDICATED.value, SessionMode.BATCH.value]:
            raise ValueError(f"Invalid session mode: {mode}. Must be 'dedicated' or 'batch'")

        # Convert mode to enum
        session_mode = SessionMode(mode)

        # Generate session ID
        session_id = f"session-{uuid.uuid4()}"

        # Create session info
        session_info = SessionInfo(
            session_id=session_id,
            mode=session_mode,
            backend_name=backend_name,
            instance=instance,
            max_ttl=max_ttl,
            created_at=datetime.utcnow()
        )

        # Store session
        with self._lock:
            self.sessions[session_id] = session_info

        return session_id

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get session information.

        Args:
            session_id: Session ID

        Returns:
            SessionInfo or None if not found
        """
        with self._lock:
            return self.sessions.get(session_id)

    def close_session(self, session_id: str, accepting_jobs: bool = False) -> bool:
        """
        Close session (stop accepting new jobs).

        Args:
            session_id: Session ID
            accepting_jobs: Whether to accept new jobs

        Returns:
            True if closed, False if not found
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session is None:
                return False

            session.accepting_jobs = accepting_jobs
            return True

    def cancel_session(self, session_id: str) -> bool:
        """
        Cancel session (mark as inactive and stop accepting jobs).

        Args:
            session_id: Session ID

        Returns:
            True if cancelled, False if not found
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session is None:
                return False

            session.active = False
            session.accepting_jobs = False
            return True

    def add_job_to_session(self, session_id: str, job_id: str) -> bool:
        """
        Add a job to a session.

        Args:
            session_id: Session ID
            job_id: Job ID

        Returns:
            True if added, False if session not found
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session is None:
                return False

            if job_id not in session.job_ids:
                session.job_ids.append(job_id)
            return True

    def is_accepting_jobs(self, session_id: str) -> bool:
        """
        Check if session is accepting new jobs.

        Args:
            session_id: Session ID

        Returns:
            True if accepting jobs, False otherwise
        """
        session = self.get_session(session_id)
        if session is None:
            return False

        # Check if expired
        if session.is_expired():
            with self._lock:
                session.active = False
                session.accepting_jobs = False
            return False

        return session.accepting_jobs and session.active

    def get_session_jobs(self, session_id: str) -> List[str]:
        """
        Get list of job IDs in a session.

        Args:
            session_id: Session ID

        Returns:
            List of job IDs, or empty list if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return []

        return session.job_ids.copy()

    def shutdown(self):
        """Shutdown the session manager and stop background threads."""
        self._stop_ttl_check.set()
        if self._ttl_check_thread is not None:
            self._ttl_check_thread.join(timeout=5)


# Global instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
