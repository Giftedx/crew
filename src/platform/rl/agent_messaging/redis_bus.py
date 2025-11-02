"""Redis-backed agent message bus for ALL-to-all communication.

Enables unrestricted cross-agent messaging for collaborative intelligence,
replacing in-memory SharedContext with persistent pub/sub.
"""
from __future__ import annotations
import asyncio
import contextlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import uuid4
from platform.observability.metrics import get_metrics
if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    """Types of agent messages."""
    INSIGHT = 'insight'
    EVIDENCE = 'evidence'
    NOTE = 'note'
    REQUEST_INSIGHT = 'request_insight'
    REQUEST_REVIEW = 'request_review'
    PROPOSE_CONSENSUS = 'propose_consensus'
    CHALLENGE_CLAIM = 'challenge_claim'
    SUPPORT_CLAIM = 'support_claim'
    VOTE = 'vote'
    ANSWER = 'answer'
    WARNING = 'warning'
    STATUS = 'status'

class MessagePriority(str, Enum):
    """Priority levels for message delivery."""
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'

@dataclass
class AgentMessage:
    """Agent-to-agent message."""
    type: MessageType
    content: str
    sender_agent_id: str | None = None
    target_agent_id: str | None = None
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['type'] = self.type.value if isinstance(self.type, MessageType) else str(self.type)
        data['priority'] = self.priority.value if isinstance(self.priority, MessagePriority) else str(self.priority)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMessage:
        """Deserialize from dict."""
        data = dict(data)
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'type' in data and isinstance(data['type'], str):
            data['type'] = MessageType(data['type'])
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = MessagePriority(data['priority'])
        return cls(**data)

class AgentMessageBus:
    """Redis-backed pub/sub message bus for agent collaboration.

    Supports:
    - ALL-to-all messaging (any agent can message any other)
    - Targeted messages (specific agent_id)
    - Broadcast messages (all agents in tenant)
    - Cross-tenant global broadcasts (for meta-learning)
    - Message TTL and persistence
    """

    def __init__(self, *, redis_url: str | None=None, redis_db: int=2, message_ttl: int=3600, enable_global_broadcast: bool=True):
        """Initialize Redis message bus.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379).
            redis_db: Redis database index for agent messages (default: 2).
            message_ttl: Message time-to-live in seconds (default: 3600 = 1 hour).
            enable_global_broadcast: Allow cross-tenant global broadcasts.
        """
        from platform.config.configuration import get_config
        config = get_config()
        self.redis_url = redis_url or getattr(config, 'agent_bus_redis_url', 'redis://redis:6379')
        self.redis_db = redis_db
        self.message_ttl = message_ttl
        self.enable_global_broadcast = enable_global_broadcast
        self._redis_client: Any = None
        self._pubsub: Any = None
        self._subscribers: dict[str, list[Callable[[AgentMessage], Coroutine[Any, Any, None]]]] = {}
        self._listener_task: asyncio.Task[None] | None = None
        self._metrics = get_metrics()

    async def connect(self) -> None:
        """Initialize Redis connection."""
        try:
            import redis.asyncio as redis
            self._redis_client = redis.from_url(self.redis_url, db=self.redis_db, decode_responses=True)
            self._pubsub = self._redis_client.pubsub()
            await self._redis_client.ping()
            logger.info(f'Connected to Redis message bus at {self.redis_url} (DB {self.redis_db})')
        except Exception as e:
            logger.error(f'Failed to connect to Redis message bus: {e}')
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._listener_task and (not self._listener_task.done()):
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task
        if self._pubsub:
            await self._pubsub.close()
        if self._redis_client:
            await self._redis_client.close()
        logger.info('Disconnected from Redis message bus')

    def _get_channel_name(self, tenant_id: str, agent_id: str | None=None) -> str:
        """Get Redis channel name for agent or broadcast.

        Args:
            tenant_id: Tenant identifier.
            agent_id: Specific agent ID (None = broadcast channel).

        Returns:
            Channel name (e.g., "agent_messages:tenant1:agent_xyz" or "agent_messages:tenant1:broadcast").
        """
        if agent_id is None:
            return f'agent_messages:{tenant_id}:broadcast'
        return f'agent_messages:{tenant_id}:{agent_id}'

    async def publish(self, message: AgentMessage, *, tenant_id: str='default') -> bool:
        """Publish a message to the bus.

        Args:
            message: AgentMessage to publish.
            tenant_id: Tenant context for the message.

        Returns:
            True if message was published successfully.
        """
        if self._redis_client is None:
            logger.warning('Redis client not connected - message not published')
            return False
        try:
            if message.target_agent_id:
                channel = self._get_channel_name(tenant_id, message.target_agent_id)
            else:
                channel = self._get_channel_name(tenant_id, None)
            message_json = json.dumps(message.to_dict())
            await self._redis_client.publish(channel, message_json)
            list_key = f'{channel}:history'
            await self._redis_client.lpush(list_key, message_json)
            await self._redis_client.expire(list_key, self.message_ttl)
            if self.enable_global_broadcast and message.priority == MessagePriority.URGENT:
                global_channel = 'agent_messages:__global__:broadcast'
                await self._redis_client.publish(global_channel, message_json)
            self._metrics.counter('agent_messages_published_total', labels={'type': message.type.value, 'priority': message.priority.value, 'targeted': str(message.target_agent_id is not None).lower()}).inc()
            logger.debug(f'Published {message.type} message from {message.sender_agent_id} to {channel} (ID: {message.message_id})')
            return True
        except Exception as e:
            logger.exception(f'Failed to publish message: {e}')
            self._metrics.counter('agent_messages_errors_total', labels={'operation': 'publish'}).inc()
            return False

    async def subscribe(self, agent_id: str, callback: Callable[[AgentMessage], Coroutine[Any, Any, None]], *, tenant_id: str='default', subscribe_to_broadcast: bool=True) -> None:
        """Subscribe an agent to receive messages.

        Args:
            agent_id: Agent identifier to subscribe.
            callback: Async callback function to handle received messages.
            tenant_id: Tenant context.
            subscribe_to_broadcast: Also subscribe to broadcast channel.
        """
        if self._redis_client is None or self._pubsub is None:
            raise RuntimeError('Redis client not connected - call connect() first')
        agent_channel = self._get_channel_name(tenant_id, agent_id)
        await self._pubsub.subscribe(agent_channel)
        if subscribe_to_broadcast:
            broadcast_channel = self._get_channel_name(tenant_id, None)
            await self._pubsub.subscribe(broadcast_channel)
        if self.enable_global_broadcast:
            global_channel = 'agent_messages:__global__:broadcast'
            await self._pubsub.subscribe(global_channel)
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = []
        self._subscribers[agent_id].append(callback)
        if self._listener_task is None or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._message_listener())
        logger.info(f'Agent {agent_id} subscribed to {agent_channel}')

    async def unsubscribe(self, agent_id: str, *, tenant_id: str='default') -> None:
        """Unsubscribe an agent from the bus.

        Args:
            agent_id: Agent identifier to unsubscribe.
            tenant_id: Tenant context.
        """
        if self._pubsub is None:
            return
        agent_channel = self._get_channel_name(tenant_id, agent_id)
        await self._pubsub.unsubscribe(agent_channel)
        broadcast_channel = self._get_channel_name(tenant_id, None)
        await self._pubsub.unsubscribe(broadcast_channel)
        if agent_id in self._subscribers:
            del self._subscribers[agent_id]
        logger.info(f'Agent {agent_id} unsubscribed from {agent_channel}')

    async def _message_listener(self) -> None:
        """Background task listening for messages and dispatching to callbacks."""
        if self._pubsub is None:
            return
        try:
            logger.info('Message listener started')
            async for redis_message in self._pubsub.listen():
                if redis_message['type'] != 'message':
                    continue
                channel = redis_message['channel']
                data = redis_message['data']
                try:
                    message_dict = json.loads(data)
                    message = AgentMessage.from_dict(message_dict)
                    parts = channel.split(':')
                    if len(parts) >= 3:
                        target_id = parts[2]
                        if target_id == 'broadcast' or target_id == '__global__':
                            for callbacks in self._subscribers.values():
                                for callback in callbacks:
                                    task = asyncio.create_task(callback(message))
                                    task.add_done_callback(lambda t: None)
                        elif target_id in self._subscribers:
                            for callback in self._subscribers[target_id]:
                                task = asyncio.create_task(callback(message))
                                task.add_done_callback(lambda t: None)
                    self._metrics.counter('agent_messages_received_total', labels={'type': message.type.value}).inc()
                except Exception as e:
                    logger.exception(f'Error processing message from {channel}: {e}')
                    self._metrics.counter('agent_messages_errors_total', labels={'operation': 'receive'}).inc()
        except asyncio.CancelledError:
            logger.info('Message listener cancelled')
        except Exception as e:
            logger.exception(f'Message listener crashed: {e}')

    async def get_message_history(self, agent_id: str | None=None, *, tenant_id: str='default', limit: int=100) -> list[AgentMessage]:
        """Retrieve message history for an agent or broadcast.

        Args:
            agent_id: Agent ID to get history for (None = broadcast history).
            tenant_id: Tenant context.
            limit: Maximum number of messages to retrieve.

        Returns:
            List of AgentMessage objects (newest first).
        """
        if self._redis_client is None:
            return []
        channel = self._get_channel_name(tenant_id, agent_id)
        list_key = f'{channel}:history'
        try:
            messages_json = await self._redis_client.lrange(list_key, 0, limit - 1)
            messages = []
            for msg_json in messages_json:
                try:
                    message_dict = json.loads(msg_json)
                    messages.append(AgentMessage.from_dict(message_dict))
                except Exception as e:
                    logger.warning(f'Failed to deserialize message: {e}')
            return messages
        except Exception as e:
            logger.exception(f'Failed to retrieve message history: {e}')
            return []
__all__ = ['AgentMessage', 'AgentMessageBus', 'MessagePriority', 'MessageType']