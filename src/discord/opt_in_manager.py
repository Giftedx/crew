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
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

class OptInManager:
    """Manages user opt-in status and preferences for Discord AI interactions."""

    def __init__(self, db_path: str='discord_opt_ins.db'):
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS discord_user_opt_ins (\n                        user_id TEXT PRIMARY KEY,\n                        username TEXT NOT NULL,\n                        guild_id TEXT NOT NULL,\n                        opted_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        interaction_count INTEGER DEFAULT 0,\n                        last_interaction TIMESTAMP,\n                        personality_preferences JSON,\n                        active BOOLEAN DEFAULT TRUE,\n                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n                    )\n                ')
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS discord_interactions (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        user_id TEXT NOT NULL,\n                        guild_id TEXT NOT NULL,\n                        message_id TEXT,\n                        interaction_type TEXT NOT NULL,\n                        content TEXT,\n                        bot_response TEXT,\n                        user_reactions JSON,\n                        engagement_score REAL,\n                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        FOREIGN KEY (user_id) REFERENCES discord_user_opt_ins (user_id)\n                    )\n                ')
                cursor.execute('\n                    CREATE INDEX IF NOT EXISTS idx_opt_ins_guild\n                    ON discord_user_opt_ins (guild_id)\n                ')
                cursor.execute('\n                    CREATE INDEX IF NOT EXISTS idx_opt_ins_active\n                    ON discord_user_opt_ins (active)\n                ')
                cursor.execute('\n                    CREATE INDEX IF NOT EXISTS idx_interactions_user_guild\n                    ON discord_interactions (user_id, guild_id)\n                ')
                cursor.execute('\n                    CREATE INDEX IF NOT EXISTS idx_interactions_timestamp\n                    ON discord_interactions (timestamp)\n                ')
                conn.commit()
        except Exception as e:
            logger.error(f'Failed to initialize opt-in database: {e}')
            raise

    async def opt_in_user(self, user_id: str, username: str, guild_id: str, personality_preferences: dict[str, Any] | None=None) -> StepResult[dict[str, Any]]:
        """Opt a user into AI interactions."""
        try:
            if personality_preferences is None:
                personality_preferences = self._get_default_preferences()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('\n                    SELECT active FROM discord_user_opt_ins\n                    WHERE user_id = ? AND guild_id = ?\n                ', (user_id, guild_id))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute('\n                        UPDATE discord_user_opt_ins\n                        SET username = ?, active = TRUE,\n                            personality_preferences = ?, updated_at = CURRENT_TIMESTAMP\n                        WHERE user_id = ? AND guild_id = ?\n                    ', (username, json.dumps(personality_preferences), user_id, guild_id))
                    action = 'updated'
                else:
                    cursor.execute('\n                        INSERT INTO discord_user_opt_ins\n                        (user_id, username, guild_id, personality_preferences)\n                        VALUES (?, ?, ?, ?)\n                    ', (user_id, username, guild_id, json.dumps(personality_preferences)))
                    action = 'created'
                conn.commit()
                return StepResult.ok(data={'action': action, 'user_id': user_id, 'username': username, 'guild_id': guild_id, 'personality_preferences': personality_preferences})
        except Exception as e:
            logger.error(f'Failed to opt in user {user_id}: {e}')
            return StepResult.fail(f'Failed to opt in user: {e!s}')

    async def opt_out_user(self, user_id: str, guild_id: str) -> StepResult[dict[str, Any]]:
        """Opt a user out of AI interactions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('\n                    UPDATE discord_user_opt_ins\n                    SET active = FALSE, updated_at = CURRENT_TIMESTAMP\n                    WHERE user_id = ? AND guild_id = ?\n                ', (user_id, guild_id))
                if cursor.rowcount == 0:
                    return StepResult.fail('User not found or already opted out')
                conn.commit()
                return StepResult.ok(data={'action': 'opted_out', 'user_id': user_id, 'guild_id': guild_id})
        except Exception as e:
            logger.error(f'Failed to opt out user {user_id}: {e}')
            return StepResult.fail(f'Failed to opt out user: {e!s}')

    async def get_user_status(self, user_id: str, guild_id: str) -> StepResult[dict[str, Any]]:
        """Get user's opt-in status and preferences."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('\n                    SELECT username, opted_in_at, interaction_count,\n                           last_interaction, personality_preferences, active\n                    FROM discord_user_opt_ins\n                    WHERE user_id = ? AND guild_id = ?\n                ', (user_id, guild_id))
                row = cursor.fetchone()
                if not row:
                    return StepResult.ok(data={'opted_in': False, 'user_id': user_id, 'guild_id': guild_id})
                username, opted_in_at, interaction_count, last_interaction, prefs_json, active = row
                personality_preferences = {}
                if prefs_json:
                    try:
                        personality_preferences = json.loads(prefs_json)
                    except json.JSONDecodeError:
                        logger.warning(f'Invalid JSON in personality_preferences for user {user_id}')
                return StepResult.ok(data={'opted_in': active, 'user_id': user_id, 'username': username, 'guild_id': guild_id, 'opted_in_at': opted_in_at, 'interaction_count': interaction_count, 'last_interaction': last_interaction, 'personality_preferences': personality_preferences})
        except Exception as e:
            logger.error(f'Failed to get user status for {user_id}: {e}')
            return StepResult.fail(f'Failed to get user status: {e!s}')

    async def update_user_preferences(self, user_id: str, guild_id: str, preferences: dict[str, Any]) -> StepResult[dict[str, Any]]:
        """Update user's personality preferences."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                validated_prefs = self._validate_preferences(preferences)
                cursor.execute('\n                    UPDATE discord_user_opt_ins\n                    SET personality_preferences = ?, updated_at = CURRENT_TIMESTAMP\n                    WHERE user_id = ? AND guild_id = ? AND active = TRUE\n                ', (json.dumps(validated_prefs), user_id, guild_id))
                if cursor.rowcount == 0:
                    return StepResult.fail('User not found or not opted in')
                conn.commit()
                return StepResult.ok(data={'action': 'preferences_updated', 'user_id': user_id, 'guild_id': guild_id, 'personality_preferences': validated_prefs})
        except Exception as e:
            logger.error(f'Failed to update preferences for user {user_id}: {e}')
            return StepResult.fail(f'Failed to update preferences: {e!s}')

    async def record_interaction(self, user_id: str, guild_id: str, message_id: str | None, interaction_type: str, content: str | None=None, bot_response: str | None=None, user_reactions: list[str] | None=None, engagement_score: float | None=None) -> StepResult[dict[str, Any]]:
        """Record an interaction between user and bot."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('\n                    INSERT INTO discord_interactions\n                    (user_id, guild_id, message_id, interaction_type, content,\n                     bot_response, user_reactions, engagement_score)\n                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n                ', (user_id, guild_id, message_id, interaction_type, content, bot_response, json.dumps(user_reactions or []), engagement_score))
                cursor.execute('\n                    UPDATE discord_user_opt_ins\n                    SET interaction_count = interaction_count + 1,\n                        last_interaction = CURRENT_TIMESTAMP,\n                        updated_at = CURRENT_TIMESTAMP\n                    WHERE user_id = ? AND guild_id = ?\n                ', (user_id, guild_id))
                conn.commit()
                return StepResult.ok(data={'action': 'interaction_recorded', 'user_id': user_id, 'guild_id': guild_id, 'interaction_type': interaction_type})
        except Exception as e:
            logger.error(f'Failed to record interaction for user {user_id}: {e}')
            return StepResult.fail(f'Failed to record interaction: {e!s}')

    async def get_user_stats(self, user_id: str, guild_id: str) -> StepResult[dict[str, Any]]:
        """Get comprehensive user interaction statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('\n                    SELECT username, interaction_count, last_interaction,\n                           personality_preferences, opted_in_at\n                    FROM discord_user_opt_ins\n                    WHERE user_id = ? AND guild_id = ?\n                ', (user_id, guild_id))
                user_row = cursor.fetchone()
                if not user_row:
                    return StepResult.fail('User not found')
                username, interaction_count, last_interaction, prefs_json, opted_in_at = user_row
                cursor.execute('\n                    SELECT interaction_type, engagement_score, timestamp\n                    FROM discord_interactions\n                    WHERE user_id = ? AND guild_id = ?\n                    ORDER BY timestamp DESC\n                    LIMIT 20\n                ', (user_id, guild_id))
                interactions = cursor.fetchall()
                total_interactions = len(interactions)
                avg_engagement = 0.0
                if interactions:
                    engagement_scores = [row[1] for row in interactions if row[1] is not None]
                    if engagement_scores:
                        avg_engagement = sum(engagement_scores) / len(engagement_scores)
                personality_preferences = {}
                if prefs_json:
                    with contextlib.suppress(json.JSONDecodeError):
                        personality_preferences = json.loads(prefs_json)
                return StepResult.ok(data={'user_id': user_id, 'username': username, 'guild_id': guild_id, 'opted_in_at': opted_in_at, 'interaction_count': interaction_count, 'last_interaction': last_interaction, 'total_recorded_interactions': total_interactions, 'average_engagement_score': avg_engagement, 'personality_preferences': personality_preferences, 'recent_interactions': [{'type': row[0], 'engagement_score': row[1], 'timestamp': row[2]} for row in interactions]})
        except Exception as e:
            logger.error(f'Failed to get user stats for {user_id}: {e}')
            return StepResult.fail(f'Failed to get user stats: {e!s}')

    async def get_guild_opt_in_stats(self, guild_id: str) -> StepResult[dict[str, Any]]:
        """Get opt-in statistics for a guild."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('\n                    SELECT COUNT(*) FROM discord_user_opt_ins\n                    WHERE guild_id = ?\n                ', (guild_id,))
                total_users = cursor.fetchone()[0]
                cursor.execute('\n                    SELECT COUNT(*) FROM discord_user_opt_ins\n                    WHERE guild_id = ? AND active = TRUE\n                ', (guild_id,))
                active_users = cursor.fetchone()[0]
                cursor.execute('\n                    SELECT COUNT(*) FROM discord_interactions\n                    WHERE guild_id = ?\n                ', (guild_id,))
                total_interactions = cursor.fetchone()[0]
                cursor.execute("\n                    SELECT COUNT(*) FROM discord_interactions\n                    WHERE guild_id = ? AND timestamp > datetime('now', '-7 days')\n                ", (guild_id,))
                recent_interactions = cursor.fetchone()[0]
                return StepResult.ok(data={'guild_id': guild_id, 'total_users': total_users, 'active_users': active_users, 'total_interactions': total_interactions, 'recent_interactions_7d': recent_interactions, 'opt_in_rate': active_users / total_users if total_users > 0 else 0.0})
        except Exception as e:
            logger.error(f'Failed to get guild stats for {guild_id}: {e}')
            return StepResult.fail(f'Failed to get guild stats: {e!s}')

    async def list_opted_in_users(self, guild_id: str) -> StepResult[list[dict[str, Any]]]:
        """List all opted-in users for a guild."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('\n                    SELECT user_id, username, interaction_count,\n                           last_interaction, opted_in_at\n                    FROM discord_user_opt_ins\n                    WHERE guild_id = ? AND active = TRUE\n                    ORDER BY last_interaction DESC, interaction_count DESC\n                ', (guild_id,))
                users = []
                for row in cursor.fetchall():
                    user_id, username, interaction_count, last_interaction, opted_in_at = row
                    users.append({'user_id': user_id, 'username': username, 'interaction_count': interaction_count, 'last_interaction': last_interaction, 'opted_in_at': opted_in_at})
                return StepResult.ok(data=users)
        except Exception as e:
            logger.error(f'Failed to list opted-in users for guild {guild_id}: {e}')
            return StepResult.fail(f'Failed to list opted-in users: {e!s}')

    def _get_default_preferences(self) -> dict[str, Any]:
        """Get default personality preferences."""
        return {'humor': 0.5, 'formality': 0.5, 'enthusiasm': 0.7, 'knowledge_confidence': 0.8, 'debate_tolerance': 0.6, 'response_style': 'balanced', 'topics_of_interest': [], 'avoid_topics': []}

    def _validate_preferences(self, preferences: dict[str, Any]) -> dict[str, Any]:
        """Validate and sanitize personality preferences."""
        validated = {}
        numeric_prefs = ['humor', 'formality', 'enthusiasm', 'knowledge_confidence', 'debate_tolerance']
        for pref in numeric_prefs:
            if pref in preferences:
                value = float(preferences[pref])
                validated[pref] = max(0.0, min(1.0, value))
        if 'response_style' in preferences:
            style = str(preferences['response_style']).lower()
            if style in ['concise', 'detailed', 'balanced']:
                validated['response_style'] = style
            else:
                validated['response_style'] = 'balanced'
        if 'topics_of_interest' in preferences:
            topics = preferences['topics_of_interest']
            if isinstance(topics, list):
                validated['topics_of_interest'] = [str(topic) for topic in topics]
            else:
                validated['topics_of_interest'] = []
        if 'avoid_topics' in preferences:
            topics = preferences['avoid_topics']
            if isinstance(topics, list):
                validated['avoid_topics'] = [str(topic) for topic in topics]
            else:
                validated['avoid_topics'] = []
        return validated