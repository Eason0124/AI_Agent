"""
API Integration Example

This shows how to integrate the Bingo Agent with a web API
Using FastAPI as an example
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

# Note: You'll need to install fastapi and uvicorn
# pip install fastapi uvicorn

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

logger = logging.getLogger(__name__)


class BingoAgentAPI:
    """
    API wrapper for Bingo Card Engagement Agent
    This can be used with FastAPI, Flask, or any other web framework
    """

    def __init__(self, db_path: str = "./bingo_agent.db"):
        self.memory_store = SQLiteMemoryStore(db_path)
        self.agent = BingoAgentGraph(self.memory_store)
        self._initialized = False

    async def initialize(self):
        """Initialize the agent and database"""
        if not self._initialized:
            await self.memory_store.initialize()
            self._initialized = True
            logger.info("Bingo Agent API initialized")

    async def create_user(
        self,
        user_id: str,
        engagement_state: str = "State_3_Pre_Active",
        behavioral_archetype: str = "Driver_Heavy",
        trip_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create or update a user profile"""
        await self.initialize()

        try:
            trip_history = TripHistory(**(trip_data or {}))

            user_profile = UserProfile(
                user_id=user_id,
                current_engagement_state=EngagementState(engagement_state),
                behavioral_archetype=BehavioralArchetype(behavioral_archetype),
                trip_history=trip_history,
                bingo_history=BingoHistory(),
            )

            success = await self.memory_store.save_user_profile(user_profile)

            return {
                "success": success,
                "user_id": user_id,
                "message": "User profile created/updated successfully"
            }

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_card(self, user_id: str) -> Dict[str, Any]:
        """Generate a new bingo card for user"""
        await self.initialize()

        try:
            result = await self.agent.generate_card_for_user(user_id)

            if result.card_generation_response and result.card_generation_response.success:
                card = result.card_generation_response.card
                return {
                    "success": True,
                    "card": {
                        "card_id": card.card_id,
                        "dimension": card.dimension.value,
                        "tile_profile": card.tile_profile.value,
                        "duration_days": card.duration_days,
                        "expires_at": card.expires_at.isoformat(),
                        "tiles": [
                            {
                                "tile_id": t.tile_id,
                                "description": t.description,
                                "transport_mode": t.transport_mode.value if t.transport_mode else None,
                                "is_nudge": t.is_nudge,
                                "difficulty_score": t.difficulty_score,
                                "completed": t.completed,
                            }
                            for t in card.tiles
                        ]
                    },
                    "delivery_time": result.card_generation_response.delivery_time.value
                    if result.card_generation_response.delivery_time else None,
                }
            else:
                return {
                    "success": False,
                    "reason": result.card_generation_response.reason,
                }

        except Exception as e:
            logger.error(f"Error generating card: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def submit_feedback(
        self,
        user_id: str,
        event_type: str,
        card_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Submit user feedback event"""
        await self.initialize()

        try:
            feedback = FeedbackEvent(
                user_id=user_id,
                card_id=card_id,
                event_type=event_type,
                metadata=metadata or {},
            )

            # Save feedback
            await self.memory_store.save_feedback(feedback)

            # Process feedback to update learning
            result = await self.agent.process_user_feedback(user_id)

            return {
                "success": True,
                "feedback_recorded": True,
                "state_transition": result.needs_user_state_update,
                "actions": [
                    {
                        "type": action.action_type,
                        "details": action.details
                    }
                    for action in result.historical_actions
                ]
            }

        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def check_reminder(self, user_id: str) -> Dict[str, Any]:
        """Check if reminder should be sent"""
        await self.initialize()

        try:
            result = await self.agent.check_reminder_for_user(user_id)

            if result.reminder_decision:
                decision = result.reminder_decision
                return {
                    "success": True,
                    "should_send": decision.action.value == "Send_Reminder",
                    "reason": decision.reason,
                    "message_template": decision.message_template.value
                    if decision.message_template else None,
                    "message_text": decision.message_text,
                }
            else:
                return {
                    "success": False,
                    "reason": "No reminder decision made"
                }

        except Exception as e:
            logger.error(f"Error checking reminder: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get learning insights for a user"""
        await self.initialize()

        try:
            from src.utils import FeedbackLearner
            learner = FeedbackLearner(self.memory_store)

            insights = await learner.get_user_insights(user_id)
            user_profile = await self.memory_store.get_user_profile(user_id)

            if user_profile:
                churn_risk = await learner.detect_churn_risk(user_profile)
                insights["churn_risk"] = churn_risk

            return {
                "success": True,
                "insights": insights
            }

        except Exception as e:
            logger.error(f"Error getting insights: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Example FastAPI Integration
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Bingo Card Engagement Agent API")
agent_api = BingoAgentAPI()


class UserCreate(BaseModel):
    user_id: str
    engagement_state: str = "State_3_Pre_Active"
    behavioral_archetype: str = "Driver_Heavy"


class FeedbackSubmit(BaseModel):
    user_id: str
    event_type: str
    card_id: str = None
    metadata: dict = {}


@app.on_event("startup")
async def startup():
    await agent_api.initialize()


@app.post("/users/create")
async def create_user(user: UserCreate):
    result = await agent_api.create_user(
        user_id=user.user_id,
        engagement_state=user.engagement_state,
        behavioral_archetype=user.behavioral_archetype
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.post("/cards/generate/{user_id}")
async def generate_card(user_id: str):
    result = await agent_api.generate_card(user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("reason"))
    return result


@app.post("/feedback/submit")
async def submit_feedback(feedback: FeedbackSubmit):
    result = await agent_api.submit_feedback(
        user_id=feedback.user_id,
        event_type=feedback.event_type,
        card_id=feedback.card_id,
        metadata=feedback.metadata
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.get("/reminders/check/{user_id}")
async def check_reminder(user_id: str):
    result = await agent_api.check_reminder(user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.get("/insights/{user_id}")
async def get_insights(user_id: str):
    result = await agent_api.get_user_insights(user_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""


# CLI Test
async def test_api():
    """Test the API wrapper"""
    print("Testing Bingo Agent API...")

    api = BingoAgentAPI()
    await api.initialize()

    # Create user
    print("\n1. Creating user...")
    result = await api.create_user(
        user_id="test_user_001",
        engagement_state="State_3_Pre_Active",
        behavioral_archetype="Driver_Heavy",
        trip_data={
            "primary_modes": ["driving"],
            "trip_frequency": 15,
            "common_travel_times": ["AM_Commuter"],
        }
    )
    print(f"   Result: {result}")

    # Generate card
    print("\n2. Generating card...")
    result = await api.generate_card("test_user_001")
    print(f"   Success: {result['success']}")
    if result['success']:
        print(f"   Card ID: {result['card']['card_id']}")
        print(f"   Tiles: {len(result['card']['tiles'])}")

    # Submit feedback
    print("\n3. Submitting feedback...")
    result = await api.submit_feedback(
        user_id="test_user_001",
        event_type="card_started",
        card_id=result['card']['card_id'] if result['success'] else None,
        metadata={"source": "mobile_app"}
    )
    print(f"   Result: {result}")

    # Check reminder
    print("\n4. Checking reminder...")
    result = await api.check_reminder("test_user_001")
    print(f"   Should send: {result.get('should_send')}")
    print(f"   Reason: {result.get('reason')}")

    # Get insights
    print("\n5. Getting insights...")
    result = await api.get_user_insights("test_user_001")
    print(f"   Result: {result}")


if __name__ == "__main__":
    asyncio.run(test_api())
