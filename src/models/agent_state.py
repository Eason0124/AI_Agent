"""
LangGraph Agent State Models
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from .user_state import UserProfile
from .bingo_card import BingoCard, CardGenerationResponse
from .reminder import ReminderDecision


class AgentAction(BaseModel):
    """Represents an action taken by the agent"""
    action_type: str  # "card_generation", "reminder_sent", "state_updated"
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


class FeedbackEvent(BaseModel):
    """User feedback event for learning"""
    user_id: str
    card_id: Optional[str] = None
    event_type: str  # "card_started", "card_completed", "tile_completed", "card_ignored"
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    reward_score: float = Field(default=0.0, description="Reward score for this event")


class BingoAgentState(BaseModel):
    """
    Main state for LangGraph workflow
    This state is passed between nodes and maintains the context
    """
    # Input
    user_id: str
    action_type: str  # "generate_card", "check_reminder", "process_feedback"

    # User Context
    user_profile: Optional[UserProfile] = None
    current_card: Optional[BingoCard] = None

    # Decision Outputs
    card_generation_response: Optional[CardGenerationResponse] = None
    reminder_decision: Optional[ReminderDecision] = None

    # Memory & Learning
    historical_actions: List[AgentAction] = Field(default_factory=list)
    recent_feedback: List[FeedbackEvent] = Field(default_factory=list)

    # Metadata
    session_id: str = Field(default_factory=lambda: f"session_{datetime.now().timestamp()}")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Flags for control flow
    should_generate_card: bool = False
    should_send_reminder: bool = False
    needs_user_state_update: bool = False

    # Error handling
    errors: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def add_action(self, action: AgentAction):
        """Add action to history"""
        self.historical_actions.append(action)
        self.updated_at = datetime.now()

    def add_feedback(self, feedback: FeedbackEvent):
        """Add feedback event"""
        self.recent_feedback.append(feedback)
        self.updated_at = datetime.now()

    def add_error(self, error: str):
        """Add error message"""
        self.errors.append(error)
        self.updated_at = datetime.now()
