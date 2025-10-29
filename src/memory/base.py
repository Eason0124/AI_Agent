"""
Base Memory Interface
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models import UserProfile, BingoCard, FeedbackEvent, AgentAction


class MemoryStore(ABC):
    """Abstract base class for memory storage"""

    @abstractmethod
    async def save_user_profile(self, profile: UserProfile) -> bool:
        """Save or update user profile"""
        pass

    @abstractmethod
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve user profile"""
        pass

    @abstractmethod
    async def save_bingo_card(self, card: BingoCard) -> bool:
        """Save or update bingo card"""
        pass

    @abstractmethod
    async def get_active_card(self, user_id: str) -> Optional[BingoCard]:
        """Get user's active bingo card"""
        pass

    @abstractmethod
    async def get_card_history(
        self, user_id: str, limit: int = 10
    ) -> List[BingoCard]:
        """Get user's card history"""
        pass

    @abstractmethod
    async def save_feedback(self, feedback: FeedbackEvent) -> bool:
        """Save feedback event"""
        pass

    @abstractmethod
    async def get_feedback_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[FeedbackEvent]:
        """Get feedback history for user"""
        pass

    @abstractmethod
    async def save_action(self, action: AgentAction, user_id: str) -> bool:
        """Save agent action"""
        pass

    @abstractmethod
    async def get_action_history(
        self, user_id: str, limit: int = 50
    ) -> List[AgentAction]:
        """Get agent action history"""
        pass

    @abstractmethod
    async def update_card_tile(
        self, card_id: str, tile_id: int, completed: bool
    ) -> bool:
        """Update specific tile completion status"""
        pass

    @abstractmethod
    async def get_learning_stats(self, user_id: str) -> Dict[str, Any]:
        """Get aggregated learning statistics for a user"""
        pass
