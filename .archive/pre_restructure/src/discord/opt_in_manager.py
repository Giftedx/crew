"""
User opt-in management system for Discord bot interactions.

This module handles user subscriptions to AI interactions, preferences,
and interaction history tracking.
"""

from __future__ import annotations

import contextlib
import json
import logging
import sqlite3
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class OptInManager:
    """Manages user opt-in status and preferences for Discord AI interactions."""

    def __init__(self, db_path: str = "discord_opt_ins.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create main opt-ins table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS discord_user_opt_ins (
                        user_id TEXT PRIMARY KEY,
                        username TEXT NOT NULL,
                        guild_id TEXT NOT NULL,
                        opted_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        interaction_count INTEGER DEFAULT 0,
                        last_interaction TIMESTAMP,
                        personality_preferences JSON,
                        active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create interaction history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS discord_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        guild_id TEXT NOT NULL,
                        message_id TEXT,
                        interaction_type TEXT NOT NULL,
                        content TEXT,
                        bot_response TEXT,
                        user_reactions JSON,
                        engagement_score REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES discord_user_opt_ins (user_id)
                    )
                """)

                # Create indexes for performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_opt_ins_guild
                    ON discord_user_opt_ins (guild_id)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_opt_ins_active
                    ON discord_user_opt_ins (active)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_interactions_user_guild
                    ON discord_interactions (user_id, guild_id)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_interactions_timestamp
                    ON discord_interactions (timestamp)
                """)

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to initialize opt-in database: {e}")
            raise

    async def opt_in_user(
        self, user_id: str, username: str, guild_id: str, personality_preferences: dict[str, Any] | None = None
    ) -> StepResult[dict[str, Any]]:
        """Opt a user into AI interactions."""
        try:
            if personality_preferences is None:
                personality_preferences = self._get_default_preferences()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if user already exists
                cursor.execute(
                    """
                    SELECT active FROM discord_user_opt_ins
                    WHERE user_id = ? AND guild_id = ?
                """,
                    (user_id, guild_id),
                )

                existing = cursor.fetchone()

                if existing:
                    # Update existing user
                    cursor.execute(
                        """
                        UPDATE discord_user_opt_ins
                        SET username = ?, active = TRUE,
                            personality_preferences = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND guild_id = ?
                    """,
                        (username, json.dumps(personality_preferences), user_id, guild_id),
                    )

                    action = "updated"
                else:
                    # Insert new user
                    cursor.execute(
                        """
                        INSERT INTO discord_user_opt_ins
                        (user_id, username, guild_id, personality_preferences)
                        VALUES (?, ?, ?, ?)
                    """,
                        (user_id, username, guild_id, json.dumps(personality_preferences)),
                    )

                    action = "created"

                conn.commit()

                return StepResult.ok(
                    data={
                        "action": action,
                        "user_id": user_id,
                        "username": username,
                        "guild_id": guild_id,
                        "personality_preferences": personality_preferences,
                    }
                )

        except Exception as e:
            logger.error(f"Failed to opt in user {user_id}: {e}")
            return StepResult.fail(f"Failed to opt in user: {e!s}")

    async def opt_out_user(self, user_id: str, guild_id: str) -> StepResult[dict[str, Any]]:
        """Opt a user out of AI interactions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE discord_user_opt_ins
                    SET active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND guild_id = ?
                """,
                    (user_id, guild_id),
                )

                if cursor.rowcount == 0:
                    return StepResult.fail("User not found or already opted out")

                conn.commit()

                return StepResult.ok(data={"action": "opted_out", "user_id": user_id, "guild_id": guild_id})

        except Exception as e:
            logger.error(f"Failed to opt out user {user_id}: {e}")
            return StepResult.fail(f"Failed to opt out user: {e!s}")

    async def get_user_status(self, user_id: str, guild_id: str) -> StepResult[dict[str, Any]]:
        """Get user's opt-in status and preferences."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT username, opted_in_at, interaction_count,
                           last_interaction, personality_preferences, active
                    FROM discord_user_opt_ins
                    WHERE user_id = ? AND guild_id = ?
                """,
                    (user_id, guild_id),
                )

                row = cursor.fetchone()

                if not row:
                    return StepResult.ok(data={"opted_in": False, "user_id": user_id, "guild_id": guild_id})

                username, opted_in_at, interaction_count, last_interaction, prefs_json, active = row

                personality_preferences = {}
                if prefs_json:
                    try:
                        personality_preferences = json.loads(prefs_json)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in personality_preferences for user {user_id}")

                return StepResult.ok(
                    data={
                        "opted_in": active,
                        "user_id": user_id,
                        "username": username,
                        "guild_id": guild_id,
                        "opted_in_at": opted_in_at,
                        "interaction_count": interaction_count,
                        "last_interaction": last_interaction,
                        "personality_preferences": personality_preferences,
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get user status for {user_id}: {e}")
            return StepResult.fail(f"Failed to get user status: {e!s}")

    async def update_user_preferences(
        self, user_id: str, guild_id: str, preferences: dict[str, Any]
    ) -> StepResult[dict[str, Any]]:
        """Update user's personality preferences."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Validate preferences
                validated_prefs = self._validate_preferences(preferences)

                cursor.execute(
                    """
                    UPDATE discord_user_opt_ins
                    SET personality_preferences = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND guild_id = ? AND active = TRUE
                """,
                    (json.dumps(validated_prefs), user_id, guild_id),
                )

                if cursor.rowcount == 0:
                    return StepResult.fail("User not found or not opted in")

                conn.commit()

                return StepResult.ok(
                    data={
                        "action": "preferences_updated",
                        "user_id": user_id,
                        "guild_id": guild_id,
                        "personality_preferences": validated_prefs,
                    }
                )

        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")
            return StepResult.fail(f"Failed to update preferences: {e!s}")

    async def record_interaction(
        self,
        user_id: str,
        guild_id: str,
        message_id: str | None,
        interaction_type: str,
        content: str | None = None,
        bot_response: str | None = None,
        user_reactions: list[str] | None = None,
        engagement_score: float | None = None,
    ) -> StepResult[dict[str, Any]]:
        """Record an interaction between user and bot."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Insert interaction record
                cursor.execute(
                    """
                    INSERT INTO discord_interactions
                    (user_id, guild_id, message_id, interaction_type, content,
                     bot_response, user_reactions, engagement_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_id,
                        guild_id,
                        message_id,
                        interaction_type,
                        content,
                        bot_response,
                        json.dumps(user_reactions or []),
                        engagement_score,
                    ),
                )

                # Update interaction count and last interaction time
                cursor.execute(
                    """
                    UPDATE discord_user_opt_ins
                    SET interaction_count = interaction_count + 1,
                        last_interaction = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND guild_id = ?
                """,
                    (user_id, guild_id),
                )

                conn.commit()

                return StepResult.ok(
                    data={
                        "action": "interaction_recorded",
                        "user_id": user_id,
                        "guild_id": guild_id,
                        "interaction_type": interaction_type,
                    }
                )

        except Exception as e:
            logger.error(f"Failed to record interaction for user {user_id}: {e}")
            return StepResult.fail(f"Failed to record interaction: {e!s}")

    async def get_user_stats(self, user_id: str, guild_id: str) -> StepResult[dict[str, Any]]:
        """Get comprehensive user interaction statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get basic user info
                cursor.execute(
                    """
                    SELECT username, interaction_count, last_interaction,
                           personality_preferences, opted_in_at
                    FROM discord_user_opt_ins
                    WHERE user_id = ? AND guild_id = ?
                """,
                    (user_id, guild_id),
                )

                user_row = cursor.fetchone()

                if not user_row:
                    return StepResult.fail("User not found")

                username, interaction_count, last_interaction, prefs_json, opted_in_at = user_row

                # Get interaction history
                cursor.execute(
                    """
                    SELECT interaction_type, engagement_score, timestamp
                    FROM discord_interactions
                    WHERE user_id = ? AND guild_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 20
                """,
                    (user_id, guild_id),
                )

                interactions = cursor.fetchall()

                # Calculate statistics
                total_interactions = len(interactions)
                avg_engagement = 0.0
                if interactions:
                    engagement_scores = [row[1] for row in interactions if row[1] is not None]
                    if engagement_scores:
                        avg_engagement = sum(engagement_scores) / len(engagement_scores)

                # Parse personality preferences
                personality_preferences = {}
                if prefs_json:
                    with contextlib.suppress(json.JSONDecodeError):
                        personality_preferences = json.loads(prefs_json)

                return StepResult.ok(
                    data={
                        "user_id": user_id,
                        "username": username,
                        "guild_id": guild_id,
                        "opted_in_at": opted_in_at,
                        "interaction_count": interaction_count,
                        "last_interaction": last_interaction,
                        "total_recorded_interactions": total_interactions,
                        "average_engagement_score": avg_engagement,
                        "personality_preferences": personality_preferences,
                        "recent_interactions": [
                            {"type": row[0], "engagement_score": row[1], "timestamp": row[2]} for row in interactions
                        ],
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get user stats for {user_id}: {e}")
            return StepResult.fail(f"Failed to get user stats: {e!s}")

    async def get_guild_opt_in_stats(self, guild_id: str) -> StepResult[dict[str, Any]]:
        """Get opt-in statistics for a guild."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get total users
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM discord_user_opt_ins
                    WHERE guild_id = ?
                """,
                    (guild_id,),
                )
                total_users = cursor.fetchone()[0]

                # Get active users
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM discord_user_opt_ins
                    WHERE guild_id = ? AND active = TRUE
                """,
                    (guild_id,),
                )
                active_users = cursor.fetchone()[0]

                # Get total interactions
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM discord_interactions
                    WHERE guild_id = ?
                """,
                    (guild_id,),
                )
                total_interactions = cursor.fetchone()[0]

                # Get recent activity (last 7 days)
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM discord_interactions
                    WHERE guild_id = ? AND timestamp > datetime('now', '-7 days')
                """,
                    (guild_id,),
                )
                recent_interactions = cursor.fetchone()[0]

                return StepResult.ok(
                    data={
                        "guild_id": guild_id,
                        "total_users": total_users,
                        "active_users": active_users,
                        "total_interactions": total_interactions,
                        "recent_interactions_7d": recent_interactions,
                        "opt_in_rate": active_users / total_users if total_users > 0 else 0.0,
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get guild stats for {guild_id}: {e}")
            return StepResult.fail(f"Failed to get guild stats: {e!s}")

    async def list_opted_in_users(self, guild_id: str) -> StepResult[list[dict[str, Any]]]:
        """List all opted-in users for a guild."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT user_id, username, interaction_count,
                           last_interaction, opted_in_at
                    FROM discord_user_opt_ins
                    WHERE guild_id = ? AND active = TRUE
                    ORDER BY last_interaction DESC, interaction_count DESC
                """,
                    (guild_id,),
                )

                users = []
                for row in cursor.fetchall():
                    user_id, username, interaction_count, last_interaction, opted_in_at = row
                    users.append(
                        {
                            "user_id": user_id,
                            "username": username,
                            "interaction_count": interaction_count,
                            "last_interaction": last_interaction,
                            "opted_in_at": opted_in_at,
                        }
                    )

                return StepResult.ok(data=users)

        except Exception as e:
            logger.error(f"Failed to list opted-in users for guild {guild_id}: {e}")
            return StepResult.fail(f"Failed to list opted-in users: {e!s}")

    def _get_default_preferences(self) -> dict[str, Any]:
        """Get default personality preferences."""
        return {
            "humor": 0.5,
            "formality": 0.5,
            "enthusiasm": 0.7,
            "knowledge_confidence": 0.8,
            "debate_tolerance": 0.6,
            "response_style": "balanced",  # "concise", "detailed", "balanced"
            "topics_of_interest": [],
            "avoid_topics": [],
        }

    def _validate_preferences(self, preferences: dict[str, Any]) -> dict[str, Any]:
        """Validate and sanitize personality preferences."""
        validated = {}

        # Numeric preferences (0.0 to 1.0)
        numeric_prefs = ["humor", "formality", "enthusiasm", "knowledge_confidence", "debate_tolerance"]

        for pref in numeric_prefs:
            if pref in preferences:
                value = float(preferences[pref])
                validated[pref] = max(0.0, min(1.0, value))

        # String preferences
        if "response_style" in preferences:
            style = str(preferences["response_style"]).lower()
            if style in ["concise", "detailed", "balanced"]:
                validated["response_style"] = style
            else:
                validated["response_style"] = "balanced"

        # List preferences
        if "topics_of_interest" in preferences:
            topics = preferences["topics_of_interest"]
            if isinstance(topics, list):
                validated["topics_of_interest"] = [str(topic) for topic in topics]
            else:
                validated["topics_of_interest"] = []

        if "avoid_topics" in preferences:
            topics = preferences["avoid_topics"]
            if isinstance(topics, list):
                validated["avoid_topics"] = [str(topic) for topic in topics]
            else:
                validated["avoid_topics"] = []

        return validated
