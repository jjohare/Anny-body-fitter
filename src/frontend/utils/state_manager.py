"""
State manager for maintaining application state across interactions
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class SessionState:
    """Represents the state of a fitting session"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)

    # Input data
    photos: List[str] = field(default_factory=list)
    subject_name: Optional[str] = None
    subject_dob: Optional[str] = None
    subject_gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    measurements: Dict[str, float] = field(default_factory=dict)

    # Processing state
    status: str = "initialized"  # initialized, processing, completed, error
    current_step: Optional[str] = None
    progress: float = 0.0

    # Results
    fitted_model_path: Optional[str] = None
    fitted_measurements: Dict[str, float] = field(default_factory=dict)
    optimization_history: List[Dict] = field(default_factory=list)

    # Metadata
    processing_options: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class StateManager:
    """Manages application state across Gradio interactions"""

    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        self.current_session_id: Optional[str] = None

    def create_session(self, session_id: Optional[str] = None) -> SessionState:
        """
        Create a new session

        Args:
            session_id: Optional session ID (generated if not provided)

        Returns:
            New SessionState object
        """
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session = SessionState(session_id=session_id)
        self.sessions[session_id] = session
        self.current_session_id = session_id

        return session

    def get_session(self, session_id: Optional[str] = None) -> Optional[SessionState]:
        """
        Get a session by ID

        Args:
            session_id: Session ID (uses current if not provided)

        Returns:
            SessionState object or None if not found
        """
        if session_id is None:
            session_id = self.current_session_id

        return self.sessions.get(session_id)

    def update_session(
        self,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Optional[SessionState]:
        """
        Update session state

        Args:
            session_id: Session ID (uses current if not provided)
            **kwargs: Fields to update

        Returns:
            Updated SessionState object or None if not found
        """
        session = self.get_session(session_id)
        if session is None:
            return None

        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        return session

    def clear_session(self, session_id: Optional[str] = None):
        """
        Clear a session

        Args:
            session_id: Session ID (uses current if not provided)
        """
        if session_id is None:
            session_id = self.current_session_id

        if session_id in self.sessions:
            del self.sessions[session_id]

        if session_id == self.current_session_id:
            self.current_session_id = None

    def save_session(self, session_id: Optional[str] = None, filepath: Optional[str] = None):
        """
        Save session to file

        Args:
            session_id: Session ID (uses current if not provided)
            filepath: Output file path (auto-generated if not provided)
        """
        session = self.get_session(session_id)
        if session is None:
            return

        if filepath is None:
            os.makedirs("sessions", exist_ok=True)
            filepath = f"sessions/{session.session_id}.json"

        # Convert to dict for JSON serialization
        session_dict = {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "photos": session.photos,
            "subject_name": session.subject_name,
            "subject_dob": session.subject_dob,
            "subject_gender": session.subject_gender,
            "height": session.height,
            "weight": session.weight,
            "measurements": session.measurements,
            "status": session.status,
            "current_step": session.current_step,
            "progress": session.progress,
            "fitted_model_path": session.fitted_model_path,
            "fitted_measurements": session.fitted_measurements,
            "optimization_history": session.optimization_history,
            "processing_options": session.processing_options,
            "errors": session.errors
        }

        with open(filepath, 'w') as f:
            json.dump(session_dict, f, indent=2)

    def load_session(self, filepath: str) -> Optional[SessionState]:
        """
        Load session from file

        Args:
            filepath: Path to session file

        Returns:
            Loaded SessionState object or None if error
        """
        try:
            with open(filepath, 'r') as f:
                session_dict = json.load(f)

            session = SessionState(
                session_id=session_dict["session_id"],
                created_at=datetime.fromisoformat(session_dict["created_at"]),
                photos=session_dict.get("photos", []),
                subject_name=session_dict.get("subject_name"),
                subject_dob=session_dict.get("subject_dob"),
                subject_gender=session_dict.get("subject_gender"),
                height=session_dict.get("height"),
                weight=session_dict.get("weight"),
                measurements=session_dict.get("measurements", {}),
                status=session_dict.get("status", "initialized"),
                current_step=session_dict.get("current_step"),
                progress=session_dict.get("progress", 0.0),
                fitted_model_path=session_dict.get("fitted_model_path"),
                fitted_measurements=session_dict.get("fitted_measurements", {}),
                optimization_history=session_dict.get("optimization_history", []),
                processing_options=session_dict.get("processing_options", {}),
                errors=session_dict.get("errors", [])
            )

            self.sessions[session.session_id] = session
            self.current_session_id = session.session_id

            return session

        except Exception as e:
            print(f"Error loading session: {e}")
            return None
