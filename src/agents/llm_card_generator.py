"""
LLM-Enhanced Card Generator for Bingo Cards
Uses GPT-4o-mini to generate personalized and engaging tile descriptions
"""
import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from .card_generator import CardGenerator
from ..models import (
    BingoAgentState,
    BingoCard,
    BingoTile,
    TileProfile,
    CardDimension,
    TransportMode,
)
from ..memory import MemoryStore

logger = logging.getLogger(__name__)


class TileDescriptions(BaseModel):
    """Parsed output from LLM"""
    tiles: List[Dict[str, Any]] = Field(description="List of tile descriptions")


class LLMCardGenerator(CardGenerator):
    """
    Enhanced card generator that uses LLM to create personalized tile descriptions
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

        logger.info(f"LLM Card Generator initialized with model: {self.llm.model_name}")

    async def generate_personalized_tiles(
        self,
        profile: TileProfile,
        dimension: CardDimension,
        user_state: BingoAgentState,
    ) -> List[BingoTile]:
        """
        Generate tiles using LLM for personalized descriptions
        """
        num_tiles = 9 if dimension == CardDimension.SMALL else 25
        user_profile = user_state.user_profile

        # Prepare context for LLM
        primary_modes = [mode.value if hasattr(mode, 'value') else mode for mode in user_profile.trip_history.primary_modes]
        travel_times = user_profile.trip_history.common_travel_times

        # Define tile distribution based on profile
        tile_strategy = self._get_tile_strategy(profile, num_tiles)

        # Create prompt for LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a gamification expert designing engaging Bingo card challenges for a transportation app.
Your goal is to create fun, achievable, and motivating tasks that encourage users to explore different transportation modes.

Guidelines:
- Make tasks specific and actionable
- Use encouraging and positive language
- Consider the user's current habits and gently nudge them toward new behaviors
- Keep descriptions concise (under 50 characters)
- Make tasks feel like fun achievements, not chores"""),
            ("user", """Create {num_tiles} Bingo tile tasks for a user with the following profile:

User Profile:
- Engagement State: {engagement_state}
- Behavioral Archetype: {behavioral_archetype}
- Primary Transportation Modes: {primary_modes}
- Common Travel Times: {travel_times}
- Completion Rate: {completion_rate:.0%}

Tile Strategy:
- Profile: {tile_profile}
- Distribution: {tile_strategy}

Create exactly {num_tiles} tasks following this distribution. Each task should include:
1. A clear, engaging description (under 50 chars)
2. The transportation mode it involves (if applicable): {available_modes}
3. Whether it's a "nudge" task (trying something new) or regular task
4. Difficulty level (1.0 = very easy, 5.0 = very hard)

Format each task as JSON:
{{
    "description": "Complete 2 walking trips",
    "transport_mode": "walking",
    "is_nudge": false,
    "difficulty_score": 1.5
}}

Return a JSON array of exactly {num_tiles} tasks.""")
        ])

        # Prepare LLM input
        chain = prompt | self.llm

        try:
            response = await chain.ainvoke({
                "num_tiles": num_tiles,
                "engagement_state": user_profile.current_engagement_state if isinstance(user_profile.current_engagement_state, str) else user_profile.current_engagement_state.value,
                "behavioral_archetype": user_profile.behavioral_archetype if isinstance(user_profile.behavioral_archetype, str) else user_profile.behavioral_archetype.value,
                "primary_modes": ", ".join(primary_modes) if primary_modes else "driving",
                "travel_times": ", ".join(travel_times) if travel_times else "weekday commuter",
                "completion_rate": user_profile.bingo_history.completion_rate,
                "tile_profile": profile.value if hasattr(profile, 'value') else profile,
                "tile_strategy": tile_strategy,
                "available_modes": ", ".join([m.value for m in TransportMode]),
            })

            # Parse LLM response
            tiles = self._parse_llm_response(response.content, num_tiles)

            logger.info(f"Generated {len(tiles)} personalized tiles using LLM")
            return tiles

        except Exception as e:
            logger.error(f"Error generating tiles with LLM: {e}")
            logger.info("Falling back to standard tile generation")
            # Fallback to parent class method
            return await super().generate_tiles(profile, dimension, user_state)

    def _get_tile_strategy(self, profile: TileProfile, num_tiles: int) -> str:
        """Get tile distribution strategy description"""
        strategies = {
            TileProfile.EASY_WINS: f"{int(num_tiles * 0.8)} primary mode tasks + {int(num_tiles * 0.2)} easy app tasks",
            TileProfile.GENTLE_NUDGE: f"{int(num_tiles * 0.6)} primary mode tasks + {int(num_tiles * 0.4)} new mode nudges",
            TileProfile.MODE_EXPLORER: f"{int(num_tiles * 0.5)} familiar tasks + {int(num_tiles * 0.5)} exploration tasks",
            TileProfile.CHALLENGE: f"{num_tiles} challenging multi-modal or themed tasks",
        }
        return strategies.get(profile, f"{num_tiles} balanced tasks")

    def _parse_llm_response(self, response_text: str, expected_count: int) -> List[BingoTile]:
        """
        Parse LLM response into BingoTile objects
        """
        import json
        import re

        tiles = []

        try:
            # Try to extract JSON array from response
            # Look for JSON array pattern
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                json_str = json_match.group(0)
                tile_data = json.loads(json_str)
            else:
                # Try parsing entire response
                tile_data = json.loads(response_text)

            # Convert to BingoTile objects
            for i, item in enumerate(tile_data[:expected_count]):
                # Handle transport_mode
                transport_mode = None
                if "transport_mode" in item and item["transport_mode"]:
                    try:
                        transport_mode = TransportMode(item["transport_mode"].lower())
                    except ValueError:
                        transport_mode = None

                tile = BingoTile(
                    tile_id=i,
                    description=item.get("description", f"Complete task {i+1}"),
                    transport_mode=transport_mode,
                    is_nudge=item.get("is_nudge", False),
                    difficulty_score=float(item.get("difficulty_score", 2.0)),
                    completed=False,
                )
                tiles.append(tile)

            # If we got fewer tiles than expected, pad with simple ones
            while len(tiles) < expected_count:
                tiles.append(BingoTile(
                    tile_id=len(tiles),
                    description=f"Complete any trip",
                    transport_mode=None,
                    is_nudge=False,
                    difficulty_score=1.0,
                ))

        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            # Return empty list, will trigger fallback
            return []

        return tiles[:expected_count]

    async def generate_tiles(
        self,
        profile: TileProfile,
        dimension: CardDimension,
        user_state: BingoAgentState,
    ) -> List[BingoTile]:
        """
        Override parent method to use LLM-generated tiles
        """
        try:
            tiles = await self.generate_personalized_tiles(profile, dimension, user_state)
            if tiles:
                return tiles
        except Exception as e:
            logger.error(f"LLM tile generation failed: {e}")

        # Fallback to standard generation
        logger.info("Using standard tile generation")
        return await super().generate_tiles(profile, dimension, user_state)
