"""
LangGraph Workflow for Bingo Card Engagement Agent
Main graph that orchestrates the agent's decision-making process
"""
import logging
from typing import Literal
from langgraph.graph import StateGraph, END
from ..models import BingoAgentState
from ..memory import MemoryStore, SQLiteMemoryStore
from ..agents.state_loader import StateLoader
from ..agents.card_generator import CardGenerator
from ..agents.reminder_node import ReminderNode
from ..agents.feedback_processor import FeedbackProcessor

logger = logging.getLogger(__name__)


class BingoAgentGraph:
    """
    Main LangGraph workflow for Bingo Card Engagement Agent

    This graph implements the following workflow:
    1. Load user state (profile, active card, history)
    2. Route to appropriate action based on action_type
    3. Execute action (generate card, check reminder, or process feedback)
    4. Save actions to memory
    5. Return final state
    """

    def __init__(self, memory_store: MemoryStore = None):
        self.memory = memory_store or SQLiteMemoryStore()

        # Initialize node handlers
        self.state_loader = StateLoader(self.memory)
        self.card_generator = CardGenerator(self.memory)
        self.reminder_node = ReminderNode(self.memory)
        self.feedback_processor = FeedbackProcessor(self.memory)

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""

        # Create state graph
        workflow = StateGraph(BingoAgentState)

        # Add nodes
        workflow.add_node("load_state", self.state_loader.load_user_state_node)
        workflow.add_node("generate_card", self.card_generator.generate_card_node)
        workflow.add_node("evaluate_reminder", self.reminder_node.evaluate_reminder_node)
        workflow.add_node("process_feedback", self.feedback_processor.process_feedback_node)
        workflow.add_node("save_actions", self._save_actions_node)

        # Set entry point
        workflow.set_entry_point("load_state")

        # Add conditional routing after state load
        workflow.add_conditional_edges(
            "load_state",
            self._route_action,
            {
                "generate_card": "generate_card",
                "check_reminder": "evaluate_reminder",
                "process_feedback": "process_feedback",
                "end": "save_actions",
            },
        )

        # All action nodes go to save_actions
        workflow.add_edge("generate_card", "save_actions")
        workflow.add_edge("evaluate_reminder", "save_actions")
        workflow.add_edge("process_feedback", "save_actions")

        # save_actions goes to END
        workflow.add_edge("save_actions", END)

        return workflow.compile()

    def _route_action(
        self, state: BingoAgentState
    ) -> Literal["generate_card", "check_reminder", "process_feedback", "end"]:
        """
        Routing function to determine which action to take
        Based on the action_type in the state
        """
        if state.errors:
            logger.warning(f"Errors detected in state, ending workflow: {state.errors}")
            return "end"

        action_type = state.action_type.lower()

        if "generate" in action_type or "card" in action_type:
            logger.info("Routing to card generation")
            return "generate_card"
        elif "remind" in action_type or "check" in action_type:
            logger.info("Routing to reminder evaluation")
            return "check_reminder"
        elif "feedback" in action_type or "process" in action_type:
            logger.info("Routing to feedback processing")
            return "process_feedback"
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return "end"

    async def _save_actions_node(self, state: BingoAgentState) -> BingoAgentState:
        """
        Node to save all actions to memory
        This ensures persistence of agent decisions
        """
        logger.info(f"Saving {len(state.historical_actions)} actions to memory")

        try:
            for action in state.historical_actions:
                await self.memory.save_action(action, state.user_id)

            logger.info("Actions saved successfully")

        except Exception as e:
            logger.error(f"Error saving actions: {e}", exc_info=True)
            state.add_error(str(e))

        return state

    async def run(
        self, user_id: str, action_type: str
    ) -> BingoAgentState:
        """
        Run the agent workflow

        Args:
            user_id: User ID to process
            action_type: Type of action ("generate_card", "check_reminder", "process_feedback")

        Returns:
            Final BingoAgentState after workflow execution
        """
        logger.info(f"Starting agent workflow for user {user_id}, action: {action_type}")

        # Initialize state
        initial_state = BingoAgentState(
            user_id=user_id,
            action_type=action_type,
        )

        # Run graph
        try:
            result = await self.graph.ainvoke(initial_state)
            # LangGraph returns dict, convert back to BingoAgentState
            if isinstance(result, dict):
                final_state = BingoAgentState(**result)
            else:
                final_state = result
            logger.info(f"Workflow completed for user {user_id}")
            return final_state

        except Exception as e:
            logger.error(f"Error in workflow execution: {e}", exc_info=True)
            initial_state.add_error(str(e))
            return initial_state

    async def generate_card_for_user(self, user_id: str) -> BingoAgentState:
        """Convenience method to generate a card"""
        return await self.run(user_id, "generate_card")

    async def check_reminder_for_user(self, user_id: str) -> BingoAgentState:
        """Convenience method to check reminder"""
        return await self.run(user_id, "check_reminder")

    async def process_user_feedback(self, user_id: str) -> BingoAgentState:
        """Convenience method to process feedback"""
        return await self.run(user_id, "process_feedback")

    def visualize(self, output_path: str = "agent_graph.png"):
        """
        Visualize the graph structure (requires graphviz)
        """
        try:
            from langgraph.graph import Graph
            # Note: This may require additional dependencies
            # You can use mermaid or other tools to visualize
            logger.info(f"Graph visualization not yet implemented")
        except ImportError:
            logger.warning("Graph visualization requires additional dependencies")
