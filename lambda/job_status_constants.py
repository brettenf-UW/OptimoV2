"""
Job Status Constants and State Machine
Provides a single source of truth for job status handling across all Lambda functions
"""

from enum import Enum
from typing import Dict, List, Optional

class BatchStatus(Enum):
    """AWS Batch job statuses"""
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    RUNNABLE = "RUNNABLE"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

class OptimoStatus(Enum):
    """Normalized Optimo job statuses for UI"""
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# Status mapping from AWS Batch to Optimo
STATUS_MAPPING: Dict[str, str] = {
    BatchStatus.SUBMITTED.value: OptimoStatus.QUEUED.value,
    BatchStatus.PENDING.value: OptimoStatus.QUEUED.value,
    BatchStatus.RUNNABLE.value: OptimoStatus.STARTING.value,
    BatchStatus.STARTING.value: OptimoStatus.STARTING.value,
    BatchStatus.RUNNING.value: OptimoStatus.RUNNING.value,
    BatchStatus.SUCCEEDED.value: OptimoStatus.COMPLETED.value,
    BatchStatus.FAILED.value: OptimoStatus.FAILED.value,
}

# States that indicate a job is still in progress
IN_PROGRESS_STATUSES: List[str] = [
    BatchStatus.SUBMITTED.value,
    BatchStatus.PENDING.value,
    BatchStatus.RUNNABLE.value,
    BatchStatus.STARTING.value,
    BatchStatus.RUNNING.value,
]

# States that indicate a job has finished (successfully or not)
TERMINAL_STATUSES: List[str] = [
    BatchStatus.SUCCEEDED.value,
    BatchStatus.FAILED.value,
]

# States that allow viewing results
RESULT_VIEWABLE_STATUSES: List[str] = [
    BatchStatus.SUCCEEDED.value,
    OptimoStatus.COMPLETED.value,
]

def normalize_status(batch_status: str) -> str:
    """
    Convert AWS Batch status to normalized Optimo status
    
    Args:
        batch_status: Raw AWS Batch status
        
    Returns:
        Normalized Optimo status for UI display
    """
    return STATUS_MAPPING.get(batch_status, batch_status.lower())

def is_terminal_status(status: str) -> bool:
    """Check if a status indicates the job has finished"""
    return status in TERMINAL_STATUSES or status in [OptimoStatus.COMPLETED.value, OptimoStatus.FAILED.value]

def is_in_progress(status: str) -> bool:
    """Check if a status indicates the job is still running"""
    return status in IN_PROGRESS_STATUSES or status in [OptimoStatus.QUEUED.value, OptimoStatus.STARTING.value, OptimoStatus.RUNNING.value]

def can_view_results(status: str) -> bool:
    """Check if results can be viewed for this status"""
    return status in RESULT_VIEWABLE_STATUSES

def get_display_message(status: str, progress: Optional[int] = None) -> str:
    """
    Get a user-friendly display message for a status
    
    Args:
        status: Job status (either Batch or Optimo format)
        progress: Optional progress percentage
        
    Returns:
        User-friendly status message
    """
    normalized = normalize_status(status)
    
    messages = {
        OptimoStatus.QUEUED.value: "Queued...",
        OptimoStatus.STARTING.value: "Starting...",
        OptimoStatus.RUNNING.value: f"Running... {progress or 0}%",
        OptimoStatus.COMPLETED.value: "Completed successfully",
        OptimoStatus.FAILED.value: "Failed",
    }
    
    return messages.get(normalized, status)

class JobStatusStateMachine:
    """
    State machine for job status transitions
    Ensures valid state transitions and provides hooks for side effects
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        OptimoStatus.QUEUED: [OptimoStatus.STARTING, OptimoStatus.FAILED],
        OptimoStatus.STARTING: [OptimoStatus.RUNNING, OptimoStatus.FAILED],
        OptimoStatus.RUNNING: [OptimoStatus.COMPLETED, OptimoStatus.FAILED],
        OptimoStatus.COMPLETED: [],  # Terminal state
        OptimoStatus.FAILED: [],  # Terminal state
    }
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid"""
        from_normalized = normalize_status(from_status)
        to_normalized = normalize_status(to_status)
        
        # Convert to enum for validation
        try:
            from_enum = OptimoStatus(from_normalized)
            to_enum = OptimoStatus(to_normalized)
        except ValueError:
            return False
        
        return to_enum in cls.VALID_TRANSITIONS.get(from_enum, [])
    
    @classmethod
    def get_next_states(cls, current_status: str) -> List[str]:
        """Get possible next states from current state"""
        normalized = normalize_status(current_status)
        try:
            current_enum = OptimoStatus(normalized)
            return [s.value for s in cls.VALID_TRANSITIONS.get(current_enum, [])]
        except ValueError:
            return []