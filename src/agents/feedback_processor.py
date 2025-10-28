"""
Feedback Processor Node for LangGraph
Processes user feedback and updates learning
"""
import logging
from ..models import (
    BingoAgentState,
    FeedbackEvent,
    AgentAction,
    EngagementState,
)
from ..memory import MemoryStore
from ..utils.feedback_learner import FeedbackLearner

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """Processes feedback events and updates user state"""

    def __init__(self, memory_store: MemoryStore):
        self.memory = memory_store
        self.learner = FeedbackLearner(memory_store)

    async def detect_state_transition(
        self, user_id: str, event: FeedbackEvent
    ) -> bool:
        """
        Detect if user should transition to next engagement state
        Returns True if transition occurred
        """
        user_profile = await self.memory.get_user_profile(user_id)
        if not user_profile:
            return False

        current_state = user_profile.current_engagement_state
        should_transition = False
        new_state = None

        # State 3 -> State 4: First card completion
        if (
            current_state == EngagementState.STATE_3_PRE_ACTIVE
            and event.event_type == "card_completed"
        ):
            new_state = EngagementState.STATE_4_ACTIVE
            should_transition = True

        # State 4 -> State 5: Multiple completions + high engagement
        elif current_state == EngagementState.STATE_4_ACTIVE:
            bingo_history = user_profile.bingo_history
            if bingo_history.cards_completed >= 5 and bingo_history.completion_rate > 0.7:
                new_state = EngagementState.STATE_5_ENGAGED
                should_transition = True

        if should_transition and new_state:
            user_profile.current_engagement_state = new_state
            await self.memory.save_user_profile(user_profile)

            # Record state transition feedback
            transition_event = FeedbackEvent(
                user_id=user_id,
                event_type="user_state_transition",
                metadata={
                    "from_state": current_state.value,
                    "to_state": new_state.value,
                },
                reward_score=1000.0,  # High reward for state transition
            )
            await self.memory.save_feedback(transition_event)

            logger.info(
                f"User {user_id} transitioned: {current_state.value} -> {new_state.value}"
            )

            return True

        return False

    async def update_bingo_history(self, user_id: str, event: FeedbackEvent):
        """Update user's bingo history based on event"""
        user_profile = await self.memory.get_user_profile(user_id)
        if not user_profile:
            return

        bingo_history = user_profile.bingo_history

        if event.event_type == "card_started":
            bingo_history.cards_participated += 1

        elif event.event_type == "card_completed":
            bingo_history.cards_completed += 1
            bingo_history.last_card_completed_date = event.timestamp

        elif event.event_type == "card_ignored":
            bingo_history.cards_offered += 1

        # Save updated profile
        await self.memory.save_user_profile(user_profile)

    async def process_feedback_node(self, state: BingoAgentState) -> BingoAgentState:
        """
        LangGraph node function for processing feedback
        """
        logger.info(f"Processing feedback for user: {state.user_id}")

        try:
            # Process each recent feedback event
            for feedback in state.recent_feedback:
                if not feedback.reward_score:
                    # Calculate and record reward
                    await self.learner.record_feedback(feedback)

                # Update bingo history
                await self.update_bingo_history(state.user_id, feedback)

                # Check for state transition
                transitioned = await self.detect_state_transition(
                    state.user_id, feedback
                )

                if transitioned:
                    state.needs_user_state_update = True
                    state.add_action(
                        AgentAction(
                            action_type="state_transition_detected",
                            details={
                                "event_type": feedback.event_type,
                                "card_id": feedback.card_id,
                            },
                            success=True,
                        )
                    )

            # Get updated insights
            insights = await self.learner.get_user_insights(state.user_id)
            churn_risk = await self.learner.detect_churn_risk(state.user_profile)

            state.add_action(
                AgentAction(
                    action_type="feedback_processed",
                    details={
                        "feedback_count": len(state.recent_feedback),
                        "total_reward": insights.get("total_reward", 0),
                        "churn_risk": churn_risk,
                    },
                    success=True,
                )
            )

            logger.info(
                f"Feedback processed for user {state.user_id}. "
                f"Churn risk: {churn_risk:.2f}"
            )

        except Exception as e:
            logger.error(f"Error processing feedback: {e}", exc_info=True)
            state.add_error(str(e))

        return state
