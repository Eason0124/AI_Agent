"""
LLM-Enhanced Bingo Agent Graph
Uses GPT-4o-mini for personalized content generation
"""
import logging
from langchain_openai import ChatOpenAI
from .bingo_agent_graph import BingoAgentGraph
from ..memory import MemoryStore, SQLiteMemoryStore
from ..agents.state_loader import StateLoader
from ..agents.llm_card_generator import LLMCardGenerator
from ..agents.llm_reminder_node import LLMReminderNode
from ..agents.feedback_processor import FeedbackProcessor

logger = logging.getLogger(__name__)


class LLMBingoAgentGraph(BingoAgentGraph):
    """
    Enhanced Bingo Agent that uses LLM for personalized content generation

    This agent uses GPT-4o-mini to:
    - Generate engaging and personalized Bingo tile descriptions
    - Create motivating reminder messages tailored to each user
    - Adapt language and tone based on user's engagement state

    All LLM features have fallbacks to ensure reliability.
    """

    def __init__(self, memory_store: MemoryStore = None, llm: ChatOpenAI = None):
        # Don't call parent __init__ yet, we'll customize node initialization
        self.memory = memory_store or SQLiteMemoryStore()

        # Initialize LLM (use provided or create from env)
        self.llm = llm

        # Initialize node handlers with LLM support
        self.state_loader = StateLoader(self.memory)
        self.card_generator = LLMCardGenerator(self.memory, llm=self.llm)
        self.reminder_node = LLMReminderNode(self.memory, llm=self.llm)
        self.feedback_processor = FeedbackProcessor(self.memory)

        # Build graph (using parent's method but with our LLM-enhanced nodes)
        self.graph = self._build_graph()

        logger.info(
            f"LLM Bingo Agent initialized with "
            f"model: {self.card_generator.llm.model_name}"
        )

    def get_llm_info(self) -> dict:
        """Get information about the LLM being used"""
        return {
            "model": self.card_generator.llm.model_name,
            "temperature": self.card_generator.llm.temperature,
            "features": [
                "Personalized tile descriptions",
                "Engaging reminder messages",
                "Context-aware content generation",
            ]
        }
