"""
Reminder and Notification Models
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ReminderAction(str, Enum):
    """Reminder action types"""
    SEND_REMINDER = "Send_Reminder"
    DO_NOTHING = "Do_Nothing"


class MessageTemplate(str, Enum):
    """Message templates for reminders"""
    ENCOURAGEMENT = "Template_Encouragement"
    URGENCY = "Template_Urgency"
    STATUS = "Template_Status"
    STALLED = "Template_Stalled"


class ReminderDecision(BaseModel):
    """Decision on whether to send a reminder"""
    action: ReminderAction
    message_template: Optional[MessageTemplate] = None
    message_text: Optional[str] = None
    reason: str = Field(description="Why this decision was made")
    scheduled_for: Optional[datetime] = None


class ReminderRequest(BaseModel):
    """Request to evaluate reminder for a user"""
    user_id: str
    card_id: str
    force_check: bool = Field(default=False)


class ReminderResponse(BaseModel):
    """Response from reminder evaluation"""
    decision: ReminderDecision
    success: bool
    error: Optional[str] = None
