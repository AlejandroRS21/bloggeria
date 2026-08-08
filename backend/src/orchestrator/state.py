"""
State management for the orchestrator.

Tracks workflow progress, agent results, and error states.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
import json


class PhaseStatus(Enum):
    """Status of a workflow phase."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Result of a single phase execution."""
    phase_name: str
    status: PhaseStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # seconds
    agent_name: Optional[str] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'phase_name': self.phase_name,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'agent_name': self.agent_name,
            'error': self.error,
            'retry_count': self.retry_count,
        }


@dataclass
class WorkflowState:
    """Complete state of the workflow execution."""
    
    # Input parameters
    topic: str
    blogger_urls: List[str]
    
    # Execution tracking
    workflow_id: str
    language: str = "auto"  # "auto" | "es" | "en" (REQ-4/5)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    
    # Phase tracking
    phases: Dict[str, PhaseResult] = field(default_factory=dict)
    current_phase: Optional[str] = None
    
    # Phase outputs
    style_profile: Optional[Dict[str, Any]] = None
    keywords: List[str] = field(default_factory=list)
    draft_content: str = ""
    critique_feedback: Optional[str] = None
    final_content: str = ""
    html_structure: Optional[Dict[str, Any]] = None
    image_prompts: List[Dict[str, str]] = field(default_factory=list)
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            'workflow_id': self.workflow_id,
            'topic': self.topic,
            'blogger_urls': self.blogger_urls,
            'language': self.language,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration': self.total_duration,
            'current_phase': self.current_phase,
            'phases': {name: phase.to_dict() for name, phase in self.phases.items()},
            'keywords': self.keywords,
            'final_content': self.final_content[:200] + '...' if len(self.final_content) > 200 else self.final_content,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert state to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class StateManager:
    """Manages workflow state and persistence."""
    
    def __init__(self, state: WorkflowState):
        self.state = state
    
    def start_phase(self, phase_name: str, agent_name: Optional[str] = None) -> None:
        """Mark a phase as started."""
        self.state.current_phase = phase_name
        self.state.phases[phase_name] = PhaseResult(
            phase_name=phase_name,
            status=PhaseStatus.RUNNING,
            start_time=datetime.now(),
            agent_name=agent_name,
        )
    
    def complete_phase(
        self,
        phase_name: str,
        output: Any = None,
        warning: Optional[str] = None
    ) -> None:
        """Mark a phase as completed."""
        if phase_name not in self.state.phases:
            raise ValueError(f"Phase {phase_name} not started")
        
        phase = self.state.phases[phase_name]
        phase.status = PhaseStatus.COMPLETED
        phase.end_time = datetime.now()
        phase.duration = (phase.end_time - phase.start_time).total_seconds()
        phase.output = output
        
        if warning:
            self.state.warnings.append(f"[{phase_name}] {warning}")
    
    def fail_phase(self, phase_name: str, error: str, retry: bool = False) -> None:
        """Mark a phase as failed."""
        if phase_name not in self.state.phases:
            raise ValueError(f"Phase {phase_name} not started")
        
        phase = self.state.phases[phase_name]
        
        if retry:
            phase.retry_count += 1
            phase.status = PhaseStatus.RUNNING  # Reset to running for retry
        else:
            phase.status = PhaseStatus.FAILED
            phase.end_time = datetime.now()
            phase.duration = (phase.end_time - phase.start_time).total_seconds()
        
        phase.error = error
        self.state.errors.append(f"[{phase_name}] {error}")
    
    def skip_phase(self, phase_name: str, reason: str) -> None:
        """Mark a phase as skipped."""
        self.state.phases[phase_name] = PhaseResult(
            phase_name=phase_name,
            status=PhaseStatus.SKIPPED,
            error=reason,
        )
        self.state.warnings.append(f"[{phase_name}] Skipped: {reason}")
    
    def finalize(self) -> None:
        """Finalize workflow state."""
        self.state.end_time = datetime.now()
        self.state.total_duration = (
            self.state.end_time - self.state.start_time
        ).total_seconds()
        self.state.current_phase = None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        completed = sum(
            1 for p in self.state.phases.values()
            if p.status == PhaseStatus.COMPLETED
        )
        failed = sum(
            1 for p in self.state.phases.values()
            if p.status == PhaseStatus.FAILED
        )
        total = len(self.state.phases)
        
        return {
            'workflow_id': self.state.workflow_id,
            'topic': self.state.topic,
            'status': 'failed' if failed > 0 else 'completed',
            'phases_completed': completed,
            'phases_failed': failed,
            'total_phases': total,
            'duration': self.state.total_duration,
            'errors': len(self.state.errors),
            'warnings': len(self.state.warnings),
        }
    
    def save_to_file(self, filepath: str) -> None:
        """Save state to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.state.to_json())
