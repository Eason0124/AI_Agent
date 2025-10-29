"""
Card Generator Node for LangGraph
Implements the card generation logic
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List
from ..models import (
    BingoAgentState,
    BingoCard,
    BingoTile,
    CardDimension,
    CardGenerationResponse,
    TileProfile,
    DeliveryTime,
    TransportMode,
    EngagementState,
    AgentAction,
)
from ..memory import MemoryStore
from ..utils.feedback_learner import FeedbackLearner

logger = logging.getLogger(__name__)


class CardGenerator:
    """Generates bingo cards based on user profile and learning"""

    def __init__(self, memory_store: MemoryStore):
        self.memory = memory_store
        self.learner = FeedbackLearner(memory_store)

    async def generate_tiles(
        self,
        profile: TileProfile,
        dimension: CardDimension,
        user_state: BingoAgentState,
    ) -> List[BingoTile]:
        """
        Generate tiles based on profile and user context
        """
        num_tiles = 9 if dimension == CardDimension.SMALL else 25
        tiles = []

        user_profile = user_state.user_profile
        primary_modes = user_profile.trip_history.primary_modes

        # Define tile templates based on profile
        if profile == TileProfile.EASY_WINS:
            # 80% primary mode + 20% easy tasks
            primary_count = int(num_tiles * 0.8)
            easy_count = num_tiles - primary_count

            # Primary mode tiles
            for i in range(primary_count):
                mode = primary_modes[i % len(primary_modes)] if primary_modes else TransportMode.DRIVING
                tiles.append(
                    BingoTile(
                        tile_id=i,
                        description=f"Complete 1 {mode.value} trip",
                        transport_mode=mode,
                        is_nudge=False,
                        difficulty_score=1.0,
                    )
                )

            # Easy tasks
            easy_tasks = [
                "Check your rewards balance",
                "Log 1 trip",
                "View your trip history",
                "Update your profile",
            ]
            for i in range(easy_count):
                tiles.append(
                    BingoTile(
                        tile_id=primary_count + i,
                        description=easy_tasks[i % len(easy_tasks)],
                        transport_mode=None,
                        is_nudge=False,
                        difficulty_score=0.5,
                    )
                )

        elif profile == TileProfile.GENTLE_NUDGE:
            # 60% primary + 40% nudge
            primary_count = int(num_tiles * 0.6)
            nudge_count = num_tiles - primary_count

            # Primary mode tiles
            for i in range(primary_count):
                mode = primary_modes[i % len(primary_modes)] if primary_modes else TransportMode.DRIVING
                tiles.append(
                    BingoTile(
                        tile_id=i,
                        description=f"Complete {i % 3 + 1} {mode.value} trips",
                        transport_mode=mode,
                        is_nudge=False,
                        difficulty_score=1.5,
                    )
                )

            # Nudge tiles (alternative modes)
            nudge_modes = [
                m for m in [TransportMode.TRANSIT, TransportMode.WALKING, TransportMode.BIKING]
                if m not in primary_modes
            ]
            for i in range(nudge_count):
                mode = nudge_modes[i % len(nudge_modes)] if nudge_modes else TransportMode.TRANSIT
                tiles.append(
                    BingoTile(
                        tile_id=primary_count + i,
                        description=f"Try {mode.value} once",
                        transport_mode=mode,
                        is_nudge=True,
                        difficulty_score=2.5,
                    )
                )

        elif profile == TileProfile.MODE_EXPLORER:
            # 50/50 split
            half = num_tiles // 2

            for i in range(half):
                mode = primary_modes[i % len(primary_modes)] if primary_modes else TransportMode.DRIVING
                tiles.append(
                    BingoTile(
                        tile_id=i,
                        description=f"Complete {i % 2 + 2} {mode.value} trips",
                        transport_mode=mode,
                        is_nudge=False,
                        difficulty_score=2.0,
                    )
                )

            all_modes = [TransportMode.DRIVING, TransportMode.TRANSIT, TransportMode.WALKING, TransportMode.BIKING]
            for i in range(num_tiles - half):
                mode = all_modes[i % len(all_modes)]
                tiles.append(
                    BingoTile(
                        tile_id=half + i,
                        description=f"Use {mode.value} for 1 mile",
                        transport_mode=mode,
                        is_nudge=True,
                        difficulty_score=2.5,
                    )
                )

        elif profile == TileProfile.CHALLENGE:
            # Difficult themed card (e.g., "All Green")
            green_modes = [TransportMode.WALKING, TransportMode.BIKING, TransportMode.TRANSIT]
            for i in range(num_tiles):
                mode = green_modes[i % len(green_modes)]
                tiles.append(
                    BingoTile(
                        tile_id=i,
                        description=f"Complete {i % 3 + 2} {mode.value} trips",
                        transport_mode=mode,
                        is_nudge=True,
                        difficulty_score=4.0,
                    )
                )

        return tiles

    async def should_generate_card(self, user_state: BingoAgentState) -> tuple[bool, str]:
        """
        Determine if a new card should be generated
        Returns (should_generate, reason)
        """
        user_profile = user_state.user_profile

        # Check if user already has an active card
        active_card = await self.memory.get_active_card(user_profile.user_id)
        if active_card:
            return False, "User already has an active card"

        # Check timing constraints
        card_history = await self.memory.get_card_history(user_profile.user_id, limit=1)
        if card_history:
            last_card = card_history[0]

            if last_card.completed and last_card.completed_at:
                days_since_completion = (datetime.now() - last_card.completed_at).days
                if days_since_completion < 7:
                    return False, f"Only {days_since_completion} days since last completion (min: 7)"

            elif not last_card.completed:
                days_since_offer = (datetime.now() - last_card.created_at).days
                if days_since_offer < 14:
                    return False, f"Only {days_since_offer} days since last offer (min: 14)"

        return True, "Eligible for new card"

    def determine_delivery_time(self, user_state: BingoAgentState) -> DeliveryTime:
        """Determine optimal delivery time based on user patterns"""
        user_profile = user_state.user_profile
        travel_times = user_profile.trip_history.common_travel_times

        if "AM_Commuter" in travel_times:
            return DeliveryTime.WEEKDAY_MORNING
        elif "PM_Commuter" in travel_times:
            return DeliveryTime.WEEKDAY_EVENING
        elif "Weekend_Traveler" in travel_times:
            return DeliveryTime.WEEKEND_MORNING

        return DeliveryTime.WEEKDAY_MORNING  # Default

    async def generate_card_node(self, state: BingoAgentState) -> BingoAgentState:
        """
        LangGraph node function for card generation
        """
        logger.info(f"Generating card for user: {state.user_id}")

        try:
            # Check if should generate
            should_generate, reason = await self.should_generate_card(state)

            if not should_generate:
                state.card_generation_response = CardGenerationResponse(
                    card=None,
                    success=False,
                    reason=reason,
                    should_deliver=False,
                )
                state.add_action(
                    AgentAction(
                        action_type="card_generation_skipped",
                        details={"reason": reason},
                        success=True,
                    )
                )
                return state

            # Use learner to determine optimal configuration
            tile_profile = await self.learner.get_best_profile_for_user(
                state.user_profile
            )
            dimension = await self.learner.get_optimal_card_dimension(
                state.user_profile
            )
            delivery_time = self.determine_delivery_time(state)

            # Determine duration
            if state.user_profile.current_engagement_state == EngagementState.STATE_3_PRE_ACTIVE:
                duration_days = 7
            elif dimension == CardDimension.LARGE:
                duration_days = 14
            else:
                duration_days = 7

            # Generate tiles
            tiles = await self.generate_tiles(tile_profile, dimension, state)

            # Create card
            card = BingoCard(
                card_id=f"card_{uuid.uuid4().hex[:12]}",
                user_id=state.user_id,
                dimension=dimension,
                duration_days=duration_days,
                tile_profile=tile_profile,
                tiles=tiles,
                expires_at=datetime.now() + timedelta(days=duration_days),
            )

            # Save card
            save_success = await self.memory.save_bingo_card(card)

            if save_success:
                state.card_generation_response = CardGenerationResponse(
                    card=card,
                    success=True,
                    reason="Card generated successfully",
                    should_deliver=True,
                    delivery_time=delivery_time,
                )

                state.current_card = card

                state.add_action(
                    AgentAction(
                        action_type="card_generated",
                        details={
                            "card_id": card.card_id,
                            "dimension": dimension.value,
                            "tile_profile": tile_profile.value,
                            "delivery_time": delivery_time.value,
                        },
                        success=True,
                    )
                )

                logger.info(
                    f"Card generated successfully: {card.card_id} "
                    f"(profile: {tile_profile.value}, dimension: {dimension.value})"
                )
            else:
                state.card_generation_response = CardGenerationResponse(
                    card=None,
                    success=False,
                    reason="Failed to save card to database",
                    should_deliver=False,
                )

                state.add_error("Failed to save generated card")

        except Exception as e:
            logger.error(f"Error in card generation: {e}", exc_info=True)
            state.card_generation_response = CardGenerationResponse(
                card=None,
                success=False,
                reason=f"Error: {str(e)}",
                should_deliver=False,
            )
            state.add_error(str(e))

        return state
