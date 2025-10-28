"""
SQLite-based Memory Store Implementation
"""
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import aiosqlite
from .base import MemoryStore
from ..models import (
    UserProfile,
    BingoCard,
    FeedbackEvent,
    AgentAction,
    BingoTile,
    EngagementState,
    BehavioralArchetype,
)

logger = logging.getLogger(__name__)


class SQLiteMemoryStore(MemoryStore):
    """SQLite implementation of memory store"""

    def __init__(self, db_path: str = "./bingo_agent.db"):
        self.db_path = db_path
        self._initialized = False

    async def initialize(self):
        """Initialize database schema"""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            # User profiles table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    engagement_state TEXT NOT NULL,
                    behavioral_archetype TEXT NOT NULL,
                    trip_history TEXT NOT NULL,
                    bingo_history TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)

            # Bingo cards table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bingo_cards (
                    card_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    dimension TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    tile_profile TEXT NOT NULL,
                    tiles TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    started BOOLEAN DEFAULT FALSE,
                    started_at TIMESTAMP,
                    completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """)

            # Feedback events table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS feedback_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    card_id TEXT,
                    event_type TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    metadata TEXT,
                    reward_score REAL DEFAULT 0.0,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """)

            # Agent actions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    details TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """)

            # Create indexes
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_cards_user ON bingo_cards(user_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback_events(user_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_actions_user ON agent_actions(user_id)"
            )

            await db.commit()

        self._initialized = True
        logger.info("Database initialized successfully")

    async def save_user_profile(self, profile: UserProfile) -> bool:
        """Save or update user profile"""
        await self.initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO user_profiles
                    (user_id, engagement_state, behavioral_archetype,
                     trip_history, bingo_history, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        profile.user_id,
                        profile.current_engagement_state.value,
                        profile.behavioral_archetype.value,
                        profile.trip_history.model_dump_json(),
                        profile.bingo_history.model_dump_json(),
                        profile.created_at.isoformat(),
                        datetime.now().isoformat(),
                    ),
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving user profile: {e}")
            return False

    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve user profile"""
        await self.initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return UserProfile(
                            user_id=row["user_id"],
                            current_engagement_state=EngagementState(
                                row["engagement_state"]
                            ),
                            behavioral_archetype=BehavioralArchetype(
                                row["behavioral_archetype"]
                            ),
                            trip_history=json.loads(row["trip_history"]),
                            bingo_history=json.loads(row["bingo_history"]),
                            created_at=datetime.fromisoformat(row["created_at"]),
                            updated_at=datetime.fromisoformat(row["updated_at"]),
                        )
            return None
        except Exception as e:
            logger.error(f"Error retrieving user profile: {e}")
            return None

    async def save_bingo_card(self, card: BingoCard) -> bool:
        """Save or update bingo card"""
        await self.initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO bingo_cards
                    (card_id, user_id, dimension, duration_days, tile_profile,
                     tiles, created_at, expires_at, started, started_at,
                     completed, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        card.card_id,
                        card.user_id,
                        card.dimension.value,
                        card.duration_days,
                        card.tile_profile.value,
                        json.dumps([t.model_dump() for t in card.tiles]),
                        card.created_at.isoformat(),
                        card.expires_at.isoformat(),
                        card.started,
                        card.started_at.isoformat() if card.started_at else None,
                        card.completed,
                        card.completed_at.isoformat() if card.completed_at else None,
                    ),
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving bingo card: {e}")
            return False

    async def get_active_card(self, user_id: str) -> Optional[BingoCard]:
        """Get user's active bingo card"""
        await self.initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """
                    SELECT * FROM bingo_cards
                    WHERE user_id = ? AND completed = FALSE
                    AND expires_at > ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (user_id, datetime.now().isoformat()),
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return self._row_to_card(row)
            return None
        except Exception as e:
            logger.error(f"Error retrieving active card: {e}")
            return None

    async def get_card_history(
        self, user_id: str, limit: int = 10
    ) -> List[BingoCard]:
        """Get user's card history"""
        await self.initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """
                    SELECT * FROM bingo_cards
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [self._row_to_card(row) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving card history: {e}")
            return []

    async def save_feedback(self, feedback: FeedbackEvent) -> bool:
        """Save feedback event"""
        await self.initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO feedback_events
                    (user_id, card_id, event_type, timestamp, metadata, reward_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feedback.user_id,
                        feedback.card_id,
                        feedback.event_type,
                        feedback.timestamp.isoformat(),
                        json.dumps(feedback.metadata),
                        feedback.reward_score,
                    ),
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            return False

    async def get_feedback_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[FeedbackEvent]:
        """Get feedback history for user"""
        await self.initialize()

        query = "SELECT * FROM feedback_events WHERE user_id = ?"
        params = [user_id]

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY timestamp DESC"

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [
                        FeedbackEvent(
                            user_id=row["user_id"],
                            card_id=row["card_id"],
                            event_type=row["event_type"],
                            timestamp=datetime.fromisoformat(row["timestamp"]),
                            metadata=json.loads(row["metadata"]),
                            reward_score=row["reward_score"],
                        )
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"Error retrieving feedback history: {e}")
            return []

    async def save_action(self, action: AgentAction, user_id: str) -> bool:
        """Save agent action"""
        await self.initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO agent_actions
                    (user_id, action_type, timestamp, details, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        action.action_type,
                        action.timestamp.isoformat(),
                        json.dumps(action.details),
                        action.success,
                        action.error_message,
                    ),
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving action: {e}")
            return False

    async def get_action_history(
        self, user_id: str, limit: int = 50
    ) -> List[AgentAction]:
        """Get agent action history"""
        await self.initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """
                    SELECT * FROM agent_actions
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [
                        AgentAction(
                            action_type=row["action_type"],
                            timestamp=datetime.fromisoformat(row["timestamp"]),
                            details=json.loads(row["details"]),
                            success=bool(row["success"]),
                            error_message=row["error_message"],
                        )
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"Error retrieving action history: {e}")
            return []

    async def update_card_tile(
        self, card_id: str, tile_id: int, completed: bool
    ) -> bool:
        """Update specific tile completion status"""
        await self.initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT tiles FROM bingo_cards WHERE card_id = ?", (card_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        tiles = json.loads(row["tiles"])
                        for tile in tiles:
                            if tile["tile_id"] == tile_id:
                                tile["completed"] = completed
                                if completed:
                                    tile["completed_at"] = datetime.now().isoformat()
                                break

                        await db.execute(
                            "UPDATE bingo_cards SET tiles = ? WHERE card_id = ?",
                            (json.dumps(tiles), card_id),
                        )
                        await db.commit()
                        return True
            return False
        except Exception as e:
            logger.error(f"Error updating card tile: {e}")
            return False

    async def get_learning_stats(self, user_id: str) -> Dict[str, Any]:
        """Get aggregated learning statistics for a user"""
        await self.initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get total reward score
                async with db.execute(
                    """
                    SELECT SUM(reward_score) as total_reward
                    FROM feedback_events
                    WHERE user_id = ?
                    """,
                    (user_id,),
                ) as cursor:
                    row = await cursor.fetchone()
                    total_reward = row[0] if row[0] else 0.0

                # Get completion stats
                async with db.execute(
                    """
                    SELECT
                        COUNT(*) as total_cards,
                        SUM(CASE WHEN completed THEN 1 ELSE 0 END) as completed_cards,
                        SUM(CASE WHEN started THEN 1 ELSE 0 END) as started_cards
                    FROM bingo_cards
                    WHERE user_id = ?
                    """,
                    (user_id,),
                ) as cursor:
                    row = await cursor.fetchone()
                    stats = {
                        "total_reward": total_reward,
                        "total_cards": row[0] if row else 0,
                        "completed_cards": row[1] if row else 0,
                        "started_cards": row[2] if row else 0,
                    }

                return stats
        except Exception as e:
            logger.error(f"Error retrieving learning stats: {e}")
            return {}

    def _row_to_card(self, row: aiosqlite.Row) -> BingoCard:
        """Convert database row to BingoCard object"""
        tiles_data = json.loads(row["tiles"])
        tiles = [BingoTile(**tile) for tile in tiles_data]

        return BingoCard(
            card_id=row["card_id"],
            user_id=row["user_id"],
            dimension=row["dimension"],
            duration_days=row["duration_days"],
            tile_profile=row["tile_profile"],
            tiles=tiles,
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            started=bool(row["started"]),
            started_at=datetime.fromisoformat(row["started_at"])
            if row["started_at"]
            else None,
            completed=bool(row["completed"]),
            completed_at=datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None,
        )
