"""
Basic Usage Example for Bingo Card Engagement Agent

This example demonstrates:
1. Creating a user profile
2. Generating a bingo card
3. Processing feedback
4. Checking for reminders
"""
import asyncio
import logging
from datetime import datetime
from src.models import (
    UserProfile,
    EngagementState,
    BehavioralArchetype,
    TripHistory,
    BingoHistory,
    TransportMode,
    FeedbackEvent,
)
from src.memory import SQLiteMemoryStore
from src.graph import BingoAgentGraph

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_sample_user(memory_store: SQLiteMemoryStore, user_id: str):
    """Create a sample user profile"""
    logger.info(f"Creating sample user: {user_id}")

    # Create user profile
    user_profile = UserProfile(
        user_id=user_id,
        current_engagement_state=EngagementState.STATE_3_PRE_ACTIVE,
        behavioral_archetype=BehavioralArchetype.DRIVER_HEAVY,
        trip_history=TripHistory(
            primary_modes=[TransportMode.DRIVING],
            trip_frequency=20,
            common_travel_times=["AM_Commuter", "PM_Commuter"],
            mode_distribution={
                TransportMode.DRIVING: 18,
                TransportMode.TRANSIT: 2,
            }
        ),
        bingo_history=BingoHistory(
            cards_offered=0,
            cards_participated=0,
            cards_completed=0,
        )
    )

    # Save to memory
    await memory_store.save_user_profile(user_profile)
    logger.info(f"User profile created for {user_id}")

    return user_profile


async def example_1_generate_card():
    """Example 1: Generate a bingo card for a new user"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Generate Bingo Card for New User")
    print("="*60 + "\n")

    # Initialize memory store and agent
    memory_store = SQLiteMemoryStore()
    await memory_store.initialize()
    agent = BingoAgentGraph(memory_store)

    # Create user
    user_id = "user_001"
    await create_sample_user(memory_store, user_id)

    # Generate card
    logger.info("Requesting card generation...")
    result = await agent.generate_card_for_user(user_id)

    # Display results
    if result.card_generation_response and result.card_generation_response.success:
        card = result.card_generation_response.card
        print(f"\n✓ Card Generated Successfully!")
        print(f"  Card ID: {card.card_id}")
        print(f"  Dimension: {card.dimension.value}")
        print(f"  Tile Profile: {card.tile_profile.value}")
        print(f"  Duration: {card.duration_days} days")
        print(f"  Expires: {card.expires_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Number of Tiles: {len(card.tiles)}")
        print(f"\n  Sample Tiles:")
        for i, tile in enumerate(card.tiles[:3]):
            print(f"    {i+1}. {tile.description} (difficulty: {tile.difficulty_score})")
        print(f"    ... and {len(card.tiles) - 3} more tiles")
    else:
        print(f"\n✗ Card Generation Failed")
        print(f"  Reason: {result.card_generation_response.reason}")

    print(f"\nActions Taken: {len(result.historical_actions)}")
    for action in result.historical_actions:
        print(f"  - {action.action_type}: {action.details}")


async def example_2_process_feedback():
    """Example 2: Process user feedback and see learning in action"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Process Feedback and Learning")
    print("="*60 + "\n")

    memory_store = SQLiteMemoryStore()
    await memory_store.initialize()
    agent = BingoAgentGraph(memory_store)

    user_id = "user_002"
    await create_sample_user(memory_store, user_id)

    # Generate initial card
    result1 = await agent.generate_card_for_user(user_id)
    card_id = result1.current_card.card_id

    print(f"Initial card generated: {card_id}")

    # Simulate user starting the card
    feedback1 = FeedbackEvent(
        user_id=user_id,
        card_id=card_id,
        event_type="card_started",
        metadata={"source": "app_click"}
    )
    await memory_store.save_feedback(feedback1)
    print(f"✓ Feedback recorded: Card started")

    # Simulate user completing the card
    feedback2 = FeedbackEvent(
        user_id=user_id,
        card_id=card_id,
        event_type="card_completed",
        metadata={"completion_time_hours": 48, "first_completion": True}
    )
    await memory_store.save_feedback(feedback2)
    print(f"✓ Feedback recorded: Card completed")

    # Process feedback
    result2 = await agent.process_user_feedback(user_id)

    print(f"\nFeedback Processing Results:")
    print(f"  State transition detected: {result2.needs_user_state_update}")
    print(f"  Total reward earned: {feedback1.reward_score + feedback2.reward_score}")

    # Check updated user profile
    updated_profile = await memory_store.get_user_profile(user_id)
    print(f"\nUpdated User State:")
    print(f"  Engagement State: {updated_profile.current_engagement_state.value}")
    print(f"  Cards Participated: {updated_profile.bingo_history.cards_participated}")
    print(f"  Cards Completed: {updated_profile.bingo_history.cards_completed}")
    print(f"  Completion Rate: {updated_profile.bingo_history.completion_rate:.2%}")


async def example_3_reminder_logic():
    """Example 3: Demonstrate reminder logic"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Reminder Logic")
    print("="*60 + "\n")

    memory_store = SQLiteMemoryStore()
    await memory_store.initialize()
    agent = BingoAgentGraph(memory_store)

    user_id = "user_003"
    await create_sample_user(memory_store, user_id)

    # Generate card
    result1 = await agent.generate_card_for_user(user_id)
    card = result1.current_card

    # Start card but don't complete
    feedback = FeedbackEvent(
        user_id=user_id,
        card_id=card.card_id,
        event_type="card_started",
    )
    await memory_store.save_feedback(feedback)

    # Update card to simulate partial progress
    card.started = True
    card.started_at = datetime.now()
    # Complete some tiles
    for i in range(2):
        card.tiles[i].completed = True
        card.tiles[i].completed_at = datetime.now()

    await memory_store.save_bingo_card(card)

    print(f"Card Status:")
    print(f"  Progress: {card.progress_percentage:.0f}%")
    print(f"  Time Remaining: {card.time_remaining_hours:.0f} hours")
    print(f"  Is Stalled: {card.is_stalled}")

    # Check reminder
    result2 = await agent.check_reminder_for_user(user_id)

    if result2.reminder_decision:
        decision = result2.reminder_decision
        print(f"\nReminder Decision:")
        print(f"  Action: {decision.action.value}")
        print(f"  Reason: {decision.reason}")

        if decision.message_template:
            print(f"  Template: {decision.message_template.value}")
            print(f"  Message: {decision.message_text}")


async def example_4_learning_insights():
    """Example 4: Show learning insights"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Learning Insights")
    print("="*60 + "\n")

    memory_store = SQLiteMemoryStore()
    await memory_store.initialize()

    from src.utils import FeedbackLearner

    user_id = "user_004"
    await create_sample_user(memory_store, user_id)

    # Simulate multiple cards and feedback
    for i in range(5):
        agent = BingoAgentGraph(memory_store)
        result = await agent.generate_card_for_user(user_id)

        if result.current_card:
            # Simulate completion
            feedback = FeedbackEvent(
                user_id=user_id,
                card_id=result.current_card.card_id,
                event_type="card_completed" if i < 4 else "card_started",
                metadata={"iteration": i}
            )
            await memory_store.save_feedback(feedback)

            # Update card status
            card = result.current_card
            card.completed = (i < 4)
            await memory_store.save_bingo_card(card)

    # Get insights
    learner = FeedbackLearner(memory_store)
    insights = await learner.get_user_insights(user_id)

    print("User Insights:")
    print(f"  Engagement State: {insights['engagement_state']}")
    print(f"  Total Reward: {insights['total_reward']:.0f}")
    print(f"  Cards Completed: {insights['cards_completed']}")
    print(f"  Completion Rate: {insights['completion_rate']:.2%}")
    print(f"  Participation Rate: {insights['participation_rate']:.2%}")

    # Check churn risk
    user_profile = await memory_store.get_user_profile(user_id)
    churn_risk = await learner.detect_churn_risk(user_profile)
    print(f"\nChurn Risk Assessment:")
    print(f"  Risk Score: {churn_risk:.2f}")
    print(f"  Status: {'⚠ HIGH RISK' if churn_risk > 0.7 else '✓ LOW RISK'}")


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("BINGO CARD ENGAGEMENT AGENT - EXAMPLES")
    print("="*60)

    await example_1_generate_card()
    await example_2_process_feedback()
    await example_3_reminder_logic()
    await example_4_learning_insights()

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
