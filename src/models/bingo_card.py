"""
Bingo Card Models
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from .user_state import TransportMode


class CardDimension(str, Enum):
    """Bingo card dimensions"""
    SMALL = "3x3"
    LARGE = "5x5"


class CardDuration(int, Enum):
    """Card duration in days"""
    WEEK = 7
    TWO_WEEKS = 14


class TileProfile(str, Enum):
    """Tile configuration profiles"""
    EASY_WINS = "Profile_Easy_Wins"  # 80% primary mode + 20% easy tasks
    GENTLE_NUDGE = "Profile_Gentle_Nudge"  # 60% primary + 40% nudge
    MODE_EXPLORER = "Profile_Mode_Explorer"  # 50/50 split
    CHALLENGE = "Profile_Challenge"  # Difficult themed card


class DeliveryTime(str, Enum):
    """When to deliver the card"""
    WEEKDAY_MORNING = "Weekday_Morning"
    WEEKDAY_EVENING = "Weekday_Evening"
    WEEKEND_MORNING = "Weekend_Morning"


class BingoTile(BaseModel):
    """Individual bingo tile"""
    tile_id: int
    description: str
    transport_mode: Optional[TransportMode] = None
    is_nudge: bool = Field(default=False, description="Is this a nudge tile?")
    difficulty_score: float = Field(default=1.0, ge=0.0, le=5.0)
    completed: bool = False
    completed_at: Optional[datetime] = None


class BingoCard(BaseModel):
    """Complete bingo card"""
    card_id: str
    user_id: str
    dimension: CardDimension
    duration_days: int
    tile_profile: TileProfile
    tiles: List[BingoTile]
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    started: bool = False
    started_at: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None

    @property
    def tiles_completed(self) -> List[int]:
        """Get list of completed tile IDs"""
        return [tile.tile_id for tile in self.tiles if tile.completed]

    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage"""
        if not self.tiles:
            return 0.0
        completed_count = sum(1 for tile in self.tiles if tile.completed)
        return (completed_count / len(self.tiles)) * 100

    @property
    def time_remaining_hours(self) -> float:
        """Get remaining time in hours"""
        now = datetime.now()
        if now >= self.expires_at:
            return 0.0
        delta = self.expires_at - now
        return delta.total_seconds() / 3600

    @property
    def is_stalled(self) -> bool:
        """Check if card has stalled (no progress in 72h)"""
        if not self.started or not self.started_at:
            return False

        # Find most recent completion
        completed_tiles = [t for t in self.tiles if t.completed and t.completed_at]
        if completed_tiles:
            most_recent = max(completed_tiles, key=lambda t: t.completed_at)
            hours_since_progress = (datetime.now() - most_recent.completed_at).total_seconds() / 3600
        else:
            hours_since_progress = (datetime.now() - self.started_at).total_seconds() / 3600

        return hours_since_progress > 72


class CardGenerationRequest(BaseModel):
    """Request to generate a new card"""
    user_id: str
    force_generation: bool = Field(
        default=False,
        description="Force generation even if timing constraints not met"
    )


class CardGenerationResponse(BaseModel):
    """Response from card generation"""
    card: Optional[BingoCard] = None
    success: bool
    reason: Optional[str] = None
    should_deliver: bool = True
    delivery_time: Optional[DeliveryTime] = None
