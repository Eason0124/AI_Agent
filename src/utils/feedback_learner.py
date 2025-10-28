"""
Feedback Learning System
Uses historical feedback to optimize agent decisions
"""
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from ..models import (
    FeedbackEvent,
    UserProfile,
    BingoCard,
    TileProfile,
    EngagementState,
    CardDimension,
)
from ..memory import MemoryStore

logger = logging.getLogger(__name__)


class FeedbackLearner:
    """
    Learns from user feedback to improve agent decisions
    Implements a simple reward-based learning mechanism
    """

    def __init__(self, memory_store: MemoryStore):
        self.memory = memory_store
        self.profile_performance: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "attempts": 0,
                "completions": 0,
                "total_reward": 0.0,
                "avg_reward": 0.0,
            }
        )

    async def calculate_reward(self, event: FeedbackEvent) -> float:
        """
        Calculate reward score based on event type
        Follows the reward mechanism from spec:
        - +100: Card completed
        - +50: Target nudge tile completed
        - +10: Card started
        - -1: Card offered but not started
        - +1000: User state transition
        """
        reward_map = {
            "card_completed": 100.0,
            "target_nudge_tile_completed": 50.0,
            "card_started": 10.0,
            "card_ignored": -1.0,
            "user_state_transition": 1000.0,
        }

        base_reward = reward_map.get(event.event_type, 0.0)

        # Add context-based adjustments
        if event.metadata.get("early_completion"):
            base_reward *= 1.2  # Bonus for early completion

        if event.metadata.get("first_completion"):
            base_reward *= 1.5  # Bonus for first card completion

        return base_reward

    async def record_feedback(self, feedback: FeedbackEvent) -> bool:
        """Record feedback and update learning statistics"""
        # Calculate reward if not already set
        if feedback.reward_score == 0.0:
            feedback.reward_score = await self.calculate_reward(feedback)

        # Save to memory
        success = await self.memory.save_feedback(feedback)

        if success:
            logger.info(
                f"Recorded feedback for user {feedback.user_id}: "
                f"{feedback.event_type} (reward: {feedback.reward_score})"
            )

        return success

    async def get_best_profile_for_user(
        self, user_profile: UserProfile
    ) -> TileProfile:
        """
        Determine the best tile profile based on user state and historical performance
        """
        state = user_profile.current_engagement_state
        archetype = user_profile.behavioral_archetype

        # Get feedback history
        feedback_history = await self.memory.get_feedback_history(
            user_profile.user_id
        )

        # State 3: Pre-Active - Always prioritize easy wins
        if state == EngagementState.STATE_3_PRE_ACTIVE:
            return TileProfile.EASY_WINS

        # State 5: Engaged - Offer challenges
        if state == EngagementState.STATE_5_ENGAGED:
            # Check if user has been succeeding with challenges
            recent_completions = [
                f for f in feedback_history[-10:]
                if f.event_type == "card_completed"
            ]
            if len(recent_completions) >= 3:
                return TileProfile.CHALLENGE
            else:
                return TileProfile.MODE_EXPLORER

        # State 4: Active - Use learning data
        if state == EngagementState.STATE_4_ACTIVE:
            # Calculate performance for each profile
            card_history = await self.memory.get_card_history(
                user_profile.user_id, limit=10
            )

            profile_stats = defaultdict(lambda: {"attempts": 0, "completions": 0})

            for card in card_history:
                profile_stats[card.tile_profile]["attempts"] += 1
                if card.completed:
                    profile_stats[card.tile_profile]["completions"] += 1

            # Find best performing profile
            best_profile = TileProfile.GENTLE_NUDGE  # Default
            best_rate = 0.0

            for profile, stats in profile_stats.items():
                if stats["attempts"] > 0:
                    rate = stats["completions"] / stats["attempts"]
                    if rate > best_rate:
                        best_rate = rate
                        best_profile = TileProfile(profile)

            # If no history, use archetype-based defaults
            if not profile_stats:
                if archetype in [
                    "Driver_Heavy",
                    "Occasional_Transit",
                ]:
                    return TileProfile.GENTLE_NUDGE
                else:
                    return TileProfile.MODE_EXPLORER

            return best_profile

        return TileProfile.GENTLE_NUDGE

    async def get_optimal_card_dimension(
        self, user_profile: UserProfile
    ) -> CardDimension:
        """Determine optimal card dimension based on user performance"""
        feedback_history = await self.memory.get_feedback_history(
            user_profile.user_id
        )

        # Check recent completion rate
        recent_cards = await self.memory.get_card_history(
            user_profile.user_id, limit=5
        )

        if not recent_cards:
            return CardDimension.SMALL  # Start with small for new users

        completion_rate = (
            sum(1 for c in recent_cards if c.completed) / len(recent_cards)
        )

        # State 3: Always small
        if user_profile.current_engagement_state == EngagementState.STATE_3_PRE_ACTIVE:
            return CardDimension.SMALL

        # State 5: Can handle large if performing well
        if user_profile.current_engagement_state == EngagementState.STATE_5_ENGAGED:
            if completion_rate > 0.7:
                return CardDimension.LARGE
            return CardDimension.SMALL

        # State 4: Adaptive
        if completion_rate > 0.8:
            # User is doing very well, can try larger cards
            return CardDimension.LARGE
        else:
            return CardDimension.SMALL

    async def should_send_reminder(
        self, user_profile: UserProfile, card: BingoCard
    ) -> bool:
        """
        Determine if reminder should be sent based on learning
        Considers user's historical response to reminders
        """
        # Get recent feedback
        feedback_history = await self.memory.get_feedback_history(
            user_profile.user_id
        )

        # Check if user typically responds to reminders
        reminder_responses = [
            f for f in feedback_history
            if f.metadata.get("after_reminder", False)
        ]

        if len(reminder_responses) > 5:
            # Calculate effectiveness
            positive_responses = sum(
                1 for r in reminder_responses
                if r.event_type in ["card_started", "card_completed", "tile_completed"]
            )
            effectiveness = positive_responses / len(reminder_responses)

            # If reminders have low effectiveness (<30%), reduce frequency
            if effectiveness < 0.3:
                return False

        return True

    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get analytical insights about user behavior
        Useful for debugging and understanding user patterns
        """
        user_profile = await self.memory.get_user_profile(user_id)
        if not user_profile:
            return {}

        feedback_history = await self.memory.get_feedback_history(user_id)
        card_history = await self.memory.get_card_history(user_id)
        stats = await self.memory.get_learning_stats(user_id)

        # Calculate trends
        recent_30d = [
            f for f in feedback_history
            if f.timestamp > datetime.now() - timedelta(days=30)
        ]

        insights = {
            "user_id": user_id,
            "engagement_state": user_profile.current_engagement_state if isinstance(user_profile.current_engagement_state, str) else user_profile.current_engagement_state.value,
            "behavioral_archetype": user_profile.behavioral_archetype if isinstance(user_profile.behavioral_archetype, str) else user_profile.behavioral_archetype.value,
            "total_reward": stats.get("total_reward", 0),
            "cards_completed": stats.get("completed_cards", 0),
            "completion_rate": (
                stats["completed_cards"] / stats["total_cards"]
                if stats.get("total_cards", 0) > 0
                else 0
            ),
            "participation_rate": (
                stats["started_cards"] / stats["total_cards"]
                if stats.get("total_cards", 0) > 0
                else 0
            ),
            "recent_activity_30d": len(recent_30d),
            "average_reward_per_event": (
                sum(f.reward_score for f in recent_30d) / len(recent_30d)
                if recent_30d
                else 0
            ),
        }

        return insights

    async def detect_churn_risk(self, user_profile: UserProfile) -> float:
        """
        Detect churn risk (0.0 = low risk, 1.0 = high risk)
        Based on recent activity patterns
        """
        feedback_history = await self.memory.get_feedback_history(
            user_profile.user_id
        )

        # Check activity in last 14 days
        recent_activity = [
            f for f in feedback_history
            if f.timestamp > datetime.now() - timedelta(days=14)
        ]

        if not recent_activity:
            return 0.9  # High churn risk if no recent activity

        # Check for declining pattern
        last_7d = [
            f for f in feedback_history
            if f.timestamp > datetime.now() - timedelta(days=7)
        ]
        prev_7d = [
            f for f in feedback_history
            if datetime.now() - timedelta(days=14) < f.timestamp <= datetime.now() - timedelta(days=7)
        ]

        if len(prev_7d) > 0:
            activity_ratio = len(last_7d) / len(prev_7d)
            if activity_ratio < 0.5:
                return 0.7  # Declining activity

        # Check card completion trend
        recent_cards = await self.memory.get_card_history(
            user_profile.user_id, limit=3
        )
        incomplete_count = sum(1 for c in recent_cards if not c.completed)

        if incomplete_count == len(recent_cards) and len(recent_cards) >= 2:
            return 0.8  # Multiple incomplete cards

        return 0.2  # Low risk
