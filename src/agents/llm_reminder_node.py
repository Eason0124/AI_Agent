"""
LLM-Enhanced Reminder Node
Uses GPT-4o-mini to generate personalized and engaging reminder messages
"""
import os
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .reminder_node import ReminderNode
from ..models import (
    BingoAgentState,
    MessageTemplate,
)
from ..memory import MemoryStore

logger = logging.getLogger(__name__)


class LLMReminderNode(ReminderNode):
    """
    Enhanced reminder node that uses LLM to create personalized messages
    """

    def __init__(self, memory_store: MemoryStore, llm: ChatOpenAI = None):
        super().__init__(memory_store)

        # Initialize LLM
        if llm is None:
            api_key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("LLM_MODEL", "gpt-4o-mini")
            temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=api_key,
            )
        else:
            self.llm = llm

        logger.info(f"LLM Reminder Node initialized with model: {self.llm.model_name}")

    async def generate_personalized_message(
        self,
        template: MessageTemplate,
        card_progress: float,
        time_remaining: float,
        user_state: BingoAgentState,
    ) -> str:
        """
        Generate personalized reminder message using LLM
        """
        user_profile = user_state.user_profile
        card = user_state.current_card

        # Map template to message intent
        intent_map = {
            MessageTemplate.ENCOURAGEMENT: "encouraging and supportive",
            MessageTemplate.URGENCY: "urgent but not pushy",
            MessageTemplate.STATUS: "informative and positive",
            MessageTemplate.STALLED: "gentle reminder without pressure",
        }

        intent = intent_map.get(template, "friendly and helpful")

        # Prepare context
        tiles_completed = len(card.tiles_completed) if card else 0
        total_tiles = len(card.tiles) if card else 9

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly AI assistant for a transportation app with gamification features.
Your job is to send helpful, encouraging, and personalized reminder messages to users about their Bingo cards.

Guidelines:
- Be warm and encouraging, never pushy or demanding
- Use emojis sparingly (max 1-2) to add personality
- Keep messages short (under 100 characters is ideal, max 150)
- Focus on the user's achievement and progress
- Make the user feel good about their journey
- Use actionable language that motivates without pressuring"""),
            ("user", """Create a {intent} reminder message for a user's Bingo card.

User Context:
- Engagement State: {engagement_state}
- Card Progress: {card_progress:.0f}% ({tiles_completed}/{total_tiles} tiles)
- Time Remaining: {time_remaining:.0f} hours
- Completion History: {completion_rate:.0%} success rate
- Primary Modes: {primary_modes}

Message Type: {template}

Create a short, personalized message (under 150 characters) that will motivate the user to complete their Bingo card.
Just return the message text, nothing else.""")
        ])

        chain = prompt | self.llm

        try:
            response = await chain.ainvoke({
                "intent": intent,
                "engagement_state": user_profile.current_engagement_state.value,
                "card_progress": card_progress,
                "tiles_completed": tiles_completed,
                "total_tiles": total_tiles,
                "time_remaining": time_remaining,
                "completion_rate": user_profile.bingo_history.completion_rate,
                "primary_modes": ", ".join([m.value for m in user_profile.trip_history.primary_modes])
                if user_profile.trip_history.primary_modes else "various modes",
                "template": template.value,
            })

            message = response.content.strip()

            # Remove quotes if present
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
            if message.startswith("'") and message.endswith("'"):
                message = message[1:-1]

            logger.info(f"Generated personalized reminder: {message[:50]}...")
            return message

        except Exception as e:
            logger.error(f"Error generating personalized message with LLM: {e}")
            # Fallback to standard message
            return super().generate_message(template, card_progress, time_remaining)

    def generate_message(
        self, template: MessageTemplate, card_progress: float, time_remaining: float
    ) -> str:
        """
        Override to use standard message (for non-async contexts)
        This is a synchronous fallback
        """
        return super().generate_message(template, card_progress, time_remaining)

    async def evaluate_reminder_node(self, state: BingoAgentState) -> BingoAgentState:
        """
        Override parent method to use LLM-generated messages
        """
        logger.info(f"Evaluating reminder with LLM for user: {state.user_id}")

        try:
            # Get active card
            active_card = await self.memory.get_active_card(state.user_id)

            if not active_card:
                from ..models import ReminderDecision, ReminderAction
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
                from ..models import ReminderDecision, ReminderAction
                state.reminder_decision = ReminderDecision(
                    action=ReminderAction.DO_NOTHING,
                    reason="Learner recommends no reminder (low effectiveness)",
                )
                return state

            # Apply reminder policy (same as parent)
            progress = active_card.progress_percentage
            time_remaining = active_card.time_remaining_hours
            is_stalled = active_card.is_stalled

            from ..models import ReminderDecision, ReminderAction
            decision = None

            # Determine which template to use (same logic as parent)
            selected_template = None

            if is_stalled and progress == 0:
                selected_template = MessageTemplate.STALLED
                reason = "Card stalled with no progress"
            elif progress > 70 and time_remaining < 72:
                selected_template = MessageTemplate.ENCOURAGEMENT
                reason = f"High progress ({progress:.0f}%) with limited time ({time_remaining:.0f}h)"
            elif progress < 50 and time_remaining < 24:
                selected_template = MessageTemplate.URGENCY
                reason = f"Low progress ({progress:.0f}%) and expiring soon ({time_remaining:.0f}h)"
            else:
                # No reminder needed
                decision = ReminderDecision(
                    action=ReminderAction.DO_NOTHING,
                    reason=f"No trigger met (progress: {progress:.0f}%, time: {time_remaining:.0f}h)",
                )

            # Generate personalized message if we need to send reminder
            if selected_template and not decision:
                personalized_message = await self.generate_personalized_message(
                    selected_template,
                    progress,
                    time_remaining,
                    state,
                )

                decision = ReminderDecision(
                    action=ReminderAction.SEND_REMINDER,
                    message_template=selected_template,
                    message_text=personalized_message,
                    reason=reason,
                    scheduled_for=datetime.now(),
                )

            state.reminder_decision = decision

            # Log action
            from ..models import AgentAction
            if decision.action == ReminderAction.SEND_REMINDER:
                state.add_action(
                    AgentAction(
                        action_type="reminder_sent_with_llm",
                        details={
                            "card_id": active_card.card_id,
                            "template": decision.message_template.value,
                            "reason": decision.reason,
                            "message_length": len(decision.message_text),
                        },
                        success=True,
                    )
                )
                state.should_send_reminder = True
                logger.info(
                    f"LLM reminder scheduled for user {state.user_id}: {decision.message_text[:50]}..."
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
            logger.error(f"Error in LLM reminder evaluation: {e}", exc_info=True)
            # Fallback to standard reminder evaluation
            logger.info("Falling back to standard reminder evaluation")
            return await super().evaluate_reminder_node(state)

        return state
