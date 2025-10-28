"""
Reminder Node for LangGraph
Implements reminder/nudge logic
"""
import logging
from datetime import datetime
from ..models import (
    BingoAgentState,
    ReminderDecision,
    ReminderAction,
    MessageTemplate,
    AgentAction,
)
from ..memory import MemoryStore
from ..utils.feedback_learner import FeedbackLearner

logger = logging.getLogger(__name__)


class ReminderNode:
    """Evaluates and sends reminders for active cards"""

    def __init__(self, memory_store: MemoryStore):
        self.memory = memory_store
        self.learner = FeedbackLearner(memory_store)

    def generate_message(
        self, template: MessageTemplate, card_progress: float, time_remaining: float
    ) -> str:
        """Generate message text from template"""
        messages = {
            MessageTemplate.ENCOURAGEMENT: (
                f"You're almost there! Just a few more tiles to complete your Bingo card. "
                f"You're at {card_progress:.0f}% completion!"
            ),
            MessageTemplate.URGENCY: (
                f"Your Bingo card expires in {time_remaining:.0f} hours! "
                f"Don't miss out on your reward. Complete it now!"
            ),
            MessageTemplate.STATUS: (
                f"You've completed {card_progress:.0f}% of your Bingo card. "
                f"Keep it up and earn your reward!"
            ),
            MessageTemplate.STALLED: (
                "Just a reminder that your Bingo card is waiting. "
                "Can you complete one more tile today?"
            ),
        }
        return messages.get(template, "Check out your Bingo card!")

    async def evaluate_reminder_node(self, state: BingoAgentState) -> BingoAgentState:
        """
        LangGraph node function for reminder evaluation
        Implements the reminder policy from the spec
        """
        logger.info(f"Evaluating reminder for user: {state.user_id}")

        try:
            # Get active card
            active_card = await self.memory.get_active_card(state.user_id)

            if not active_card:
                state.reminder_decision = ReminderDecision(
                    action=ReminderAction.DO_NOTHING,
                    reason="No active card found",
                )
                return state

            state.current_card = active_card

            # Check if learner says we should send reminder
            should_send = await self.learner.should_send_reminder(
                state.user_profile, active_card
            )

            if not should_send:
                state.reminder_decision = ReminderDecision(
                    action=ReminderAction.DO_NOTHING,
                    reason="Learner recommends no reminder (low effectiveness)",
                )
                return state

            # Apply reminder policy
            progress = active_card.progress_percentage
            time_remaining = active_card.time_remaining_hours
            is_stalled = active_card.is_stalled

            decision = None

            # Rule 1: Stalled card (no progress in 48h)
            if is_stalled and progress == 0:
                decision = ReminderDecision(
                    action=ReminderAction.SEND_REMINDER,
                    message_template=MessageTemplate.STALLED,
                    message_text=self.generate_message(
                        MessageTemplate.STALLED, progress, time_remaining
                    ),
                    reason="Card stalled with no progress",
                    scheduled_for=datetime.now(),
                )

            # Rule 2: High progress, low time remaining (encouragement)
            elif progress > 70 and time_remaining < 72:
                decision = ReminderDecision(
                    action=ReminderAction.SEND_REMINDER,
                    message_template=MessageTemplate.ENCOURAGEMENT,
                    message_text=self.generate_message(
                        MessageTemplate.ENCOURAGEMENT, progress, time_remaining
                    ),
                    reason=f"High progress ({progress:.0f}%) with limited time ({time_remaining:.0f}h)",
                    scheduled_for=datetime.now(),
                )

            # Rule 3: Low progress, expiring soon (urgency)
            elif progress < 50 and time_remaining < 24:
                decision = ReminderDecision(
                    action=ReminderAction.SEND_REMINDER,
                    message_template=MessageTemplate.URGENCY,
                    message_text=self.generate_message(
                        MessageTemplate.URGENCY, progress, time_remaining
                    ),
                    reason=f"Low progress ({progress:.0f}%) and expiring soon ({time_remaining:.0f}h)",
                    scheduled_for=datetime.now(),
                )

            # Default: No reminder to avoid fatigue
            else:
                decision = ReminderDecision(
                    action=ReminderAction.DO_NOTHING,
                    reason=f"No trigger met (progress: {progress:.0f}%, time: {time_remaining:.0f}h)",
                )

            state.reminder_decision = decision

            # Log action
            if decision.action == ReminderAction.SEND_REMINDER:
                state.add_action(
                    AgentAction(
                        action_type="reminder_sent",
                        details={
                            "card_id": active_card.card_id,
                            "template": decision.message_template.value,
                            "reason": decision.reason,
                        },
                        success=True,
                    )
                )
                state.should_send_reminder = True
                logger.info(
                    f"Reminder scheduled for user {state.user_id}: {decision.reason}"
                )
            else:
                state.add_action(
                    AgentAction(
                        action_type="reminder_skipped",
                        details={"reason": decision.reason},
                        success=True,
                    )
                )
                logger.info(f"Reminder skipped for user {state.user_id}: {decision.reason}")

        except Exception as e:
            logger.error(f"Error in reminder evaluation: {e}", exc_info=True)
            state.reminder_decision = ReminderDecision(
                action=ReminderAction.DO_NOTHING,
                reason=f"Error: {str(e)}",
            )
            state.add_error(str(e))

        return state
