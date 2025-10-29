"""
User State Models for Bingo Card Engagement Agent
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class EngagementState(str, Enum):
    """User engagement states"""
    STATE_3_PRE_ACTIVE = "State_3_Pre_Active"
    STATE_4_ACTIVE = "State_4_Active"
    STATE_5_ENGAGED = "State_5_Engaged"


class TransportMode(str, Enum):
    """Transport modes"""
    DRIVING = "driving"
    TRANSIT = "transit"
    WALKING = "walking"
    BIKING = "biking"
    CARPOOL = "carpool"


class BehavioralArchetype(str, Enum):
    """User behavioral archetypes"""
    DRIVER_HEAVY = "Driver_Heavy"
    OCCASIONAL_TRANSIT = "Occasional_Transit"
    MULTIMODAL_ACTIVE = "Multimodal_Active"
    BIKER_WALKER = "Biker_Walker"


class TripHistory(BaseModel):
    """User's trip history over last 30 days"""
    primary_modes: List[TransportMode] = Field(default_factory=list)
    trip_frequency: int = Field(default=0, description="Total trips in last 30 days")
    common_travel_times: List[str] = Field(
        default_factory=list,
        description="e.g., ['AM_Commuter', 'Weekend_Traveler']"
    )
    mode_distribution: Dict[TransportMode, int] = Field(
        default_factory=dict,
        description="Count of trips per mode"
    )


class BingoHistory(BaseModel):
    """User's bingo card history"""
    cards_offered: int = Field(default=0)
    cards_participated: int = Field(default=0)
    cards_completed: int = Field(default=0)
    last_card_completed_date: Optional[datetime] = None
    common_uncompleted_tiles: List[str] = Field(default_factory=list)

    @property
    def participation_rate(self) -> float:
        """Calculate participation rate"""
        if self.cards_offered == 0:
            return 0.0
        return self.cards_participated / self.cards_offered

    @property
    def completion_rate(self) -> float:
        """Calculate completion rate"""
        if self.cards_participated == 0:
            return 0.0
        return self.cards_completed / self.cards_participated


class UserProfile(BaseModel):
    """Complete user profile for agent decision-making"""
    user_id: str
    current_engagement_state: EngagementState
    behavioral_archetype: BehavioralArchetype
    trip_history: TripHistory = Field(default_factory=TripHistory)
    bingo_history: BingoHistory = Field(default_factory=BingoHistory)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True
