"""
State Loader Node for LangGraph
Loads user profile and current context
"""
import logging
from ..models import BingoAgentState, AgentAction
from ..memory import MemoryStore

logger = logging.getLogger(__name__)


class StateLoader:
    """Loads user state and context for decision making"""

    def __init__(self, memory_store: MemoryStore):
        self.memory = memory_store

    async def load_user_state_node(self, state: BingoAgentState) -> BingoAgentState:
        """
        LangGraph node function to load user profile and active card
        """
        logger.info(f"Loading state for user: {state.user_id}")

        try:
            # Load user profile
            user_profile = await self.memory.get_user_profile(state.user_id)

            if not user_profile:
                error_msg = f"User profile not found for {state.user_id}"
                logger.error(error_msg)
                state.add_error(error_msg)
                return state

            state.user_profile = user_profile

            # Load active card if exists
            active_card = await self.memory.get_active_card(state.user_id)
            if active_card:
                state.current_card = active_card
                logger.info(f"Active card found: {active_card.card_id}")

            # Load recent feedback for context
            recent_feedback = await self.memory.get_feedback_history(
                state.user_id
            )
            state.recent_feedback = recent_feedback[-10:]  # Last 10 events

            # Load recent actions
            recent_actions = await self.memory.get_action_history(
                state.user_id, limit=20
            )
            state.historical_actions = recent_actions

            state.add_action(
                AgentAction(
                    action_type="state_loaded",
                    details={
                        "engagement_state": user_profile.current_engagement_state if isinstance(user_profile.current_engagement_state, str) else user_profile.current_engagement_state.value,
                        "has_active_card": active_card is not None,
                        "recent_feedback_count": len(state.recent_feedback),
                    },
                    success=True,
                )
            )

            logger.info(
                f"State loaded successfully for user {state.user_id} "
                f"(state: {user_profile.current_engagement_state if isinstance(user_profile.current_engagement_state, str) else user_profile.current_engagement_state.value})"
            )

        except Exception as e:
            logger.error(f"Error loading state: {e}", exc_info=True)
            state.add_error(str(e))

        return state
