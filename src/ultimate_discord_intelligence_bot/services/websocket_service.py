"""WebSocket service for real-time client communication and live updates."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from websockets.server import WebSocketServerProtocol

from ultimate_discord_intelligence_bot.settings import ENABLE_WEBSOCKET_UPDATES
from ultimate_discord_intelligence_bot.step_result import StepResult

log = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""

    AGENT_STATUS = "agent_status"
    ANALYSIS_UPDATE = "analysis_update"
    STREAM_UPDATE = "stream_update"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_METRICS = "performance_metrics"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""

    message_type: MessageType
    data: Dict[str, Any]
    timestamp: float
    tenant_id: Optional[str] = None
    workspace_id: Optional[str] = None
    message_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "message_type": self.message_type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "message_id": self.message_id,
        }


@dataclass
class ClientConnection:
    """Client connection information."""

    websocket: WebSocketServerProtocol
    client_id: str
    tenant_id: str
    workspace_id: str
    subscribed_channels: Set[str]
    connected_at: float
    last_heartbeat: float


class WebSocketService:
    """WebSocket service for real-time client communication and live updates."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize WebSocket service.

        Args:
            host: Host to bind the WebSocket server to
            port: Port to bind the WebSocket server to
        """
        self.host = host
        self.port = port
        self.clients: Dict[str, ClientConnection] = {}
        self.server: Optional[websockets.WebSocketServer] = None
        self.running = False
        self.heartbeat_interval = 30.0  # seconds
        self.max_connections = 1000

        log.info(f"WebSocket service initialized on {host}:{port}")

    async def start_server(self) -> StepResult:
        """Start the WebSocket server."""
        if not ENABLE_WEBSOCKET_UPDATES:
            return StepResult.fail("WebSocket updates disabled via feature flag")

        try:
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port,
                max_size=1024 * 1024,  # 1MB max message size
                ping_interval=20,
                ping_timeout=10,
            )
            self.running = True

            # Start background tasks
            asyncio.create_task(self._heartbeat_task())
            asyncio.create_task(self._cleanup_task())

            log.info(f"WebSocket server started on {self.host}:{self.port}")
            return StepResult.ok(
                data={"host": self.host, "port": self.port, "status": "running"}
            )

        except Exception as e:
            log.error(f"Failed to start WebSocket server: {e}")
            return StepResult.fail(f"Failed to start WebSocket server: {e}")

    async def stop_server(self) -> StepResult:
        """Stop the WebSocket server."""
        try:
            self.running = False

            # Close all client connections
            for client_id, connection in list(self.clients.items()):
                try:
                    await connection.websocket.close()
                except Exception:
                    pass

            self.clients.clear()

            if self.server:
                self.server.close()
                await self.server.wait_closed()

            log.info("WebSocket server stopped")
            return StepResult.ok(data={"status": "stopped"})

        except Exception as e:
            log.error(f"Error stopping WebSocket server: {e}")
            return StepResult.fail(f"Error stopping WebSocket server: {e}")

    async def _handle_client(
        self, websocket: WebSocketServerProtocol, path: str
    ) -> None:
        """Handle new client connection."""
        client_id = f"client_{int(time.time() * 1000)}_{id(websocket)}"

        try:
            # Extract tenant and workspace from path or query parameters
            tenant_id = "default"
            workspace_id = "main"

            if path.startswith("/ws/"):
                parts = path.split("/")
                if len(parts) >= 4:
                    tenant_id = parts[2]
                    workspace_id = parts[3]

            connection = ClientConnection(
                websocket=websocket,
                client_id=client_id,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                subscribed_channels=set(),
                connected_at=time.time(),
                last_heartbeat=time.time(),
            )

            self.clients[client_id] = connection

            log.info(
                f"Client {client_id} connected (tenant: {tenant_id}, workspace: {workspace_id})"
            )

            # Send welcome message
            welcome_msg = WebSocketMessage(
                message_type=MessageType.HEARTBEAT,
                data={
                    "message": "Connected to WebSocket service",
                    "client_id": client_id,
                },
                timestamp=time.time(),
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )
            await self._send_to_client(client_id, welcome_msg)

            # Handle client messages
            async for message in websocket:
                try:
                    await self._handle_client_message(client_id, message)
                except Exception as e:
                    log.warning(f"Error handling message from {client_id}: {e}")

        except ConnectionClosed:
            log.info(f"Client {client_id} disconnected")
        except WebSocketException as e:
            log.warning(f"WebSocket error for client {client_id}: {e}")
        except Exception as e:
            log.error(f"Unexpected error handling client {client_id}: {e}")
        finally:
            # Clean up client connection
            if client_id in self.clients:
                del self.clients[client_id]

    async def _handle_client_message(self, client_id: str, message: str) -> None:
        """Handle message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")

            if message_type == "subscribe":
                channels = data.get("channels", [])
                await self._handle_subscribe(client_id, channels)

            elif message_type == "unsubscribe":
                channels = data.get("channels", [])
                await self._handle_unsubscribe(client_id, channels)

            elif message_type == "ping":
                await self._handle_ping(client_id)

            else:
                log.warning(f"Unknown message type from {client_id}: {message_type}")

        except json.JSONDecodeError:
            log.warning(f"Invalid JSON from client {client_id}: {message}")
        except Exception as e:
            log.error(f"Error handling message from {client_id}: {e}")

    async def _handle_subscribe(self, client_id: str, channels: List[str]) -> None:
        """Handle client subscription to channels."""
        if client_id not in self.clients:
            return

        connection = self.clients[client_id]
        connection.subscribed_channels.update(channels)

        log.info(f"Client {client_id} subscribed to channels: {channels}")

        # Send confirmation
        response = WebSocketMessage(
            message_type=MessageType.HEARTBEAT,
            data={
                "message": f"Subscribed to {channels}",
                "subscribed_channels": list(connection.subscribed_channels),
            },
            timestamp=time.time(),
            tenant_id=connection.tenant_id,
            workspace_id=connection.workspace_id,
        )
        await self._send_to_client(client_id, response)

    async def _handle_unsubscribe(self, client_id: str, channels: List[str]) -> None:
        """Handle client unsubscription from channels."""
        if client_id not in self.clients:
            return

        connection = self.clients[client_id]
        connection.subscribed_channels.difference_update(channels)

        log.info(f"Client {client_id} unsubscribed from channels: {channels}")

        # Send confirmation
        response = WebSocketMessage(
            message_type=MessageType.HEARTBEAT,
            data={
                "message": f"Unsubscribed from {channels}",
                "subscribed_channels": list(connection.subscribed_channels),
            },
            timestamp=time.time(),
            tenant_id=connection.tenant_id,
            workspace_id=connection.workspace_id,
        )
        await self._send_to_client(client_id, response)

    async def _handle_ping(self, client_id: str) -> None:
        """Handle client ping."""
        if client_id not in self.clients:
            return

        connection = self.clients[client_id]
        connection.last_heartbeat = time.time()

        response = WebSocketMessage(
            message_type=MessageType.HEARTBEAT,
            data={"message": "pong", "timestamp": time.time()},
            timestamp=time.time(),
            tenant_id=connection.tenant_id,
            workspace_id=connection.workspace_id,
        )
        await self._send_to_client(client_id, response)

    async def _send_to_client(self, client_id: str, message: WebSocketMessage) -> None:
        """Send message to specific client."""
        if client_id not in self.clients:
            return

        connection = self.clients[client_id]
        try:
            await connection.websocket.send(json.dumps(message.to_dict()))
        except ConnectionClosed:
            # Remove disconnected client
            if client_id in self.clients:
                del self.clients[client_id]
        except Exception as e:
            log.warning(f"Failed to send message to {client_id}: {e}")

    async def broadcast_message(
        self,
        message: WebSocketMessage,
        channel: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Broadcast message to all connected clients or filtered subset."""
        if not self.running:
            return StepResult.fail("WebSocket server not running")

        try:
            sent_count = 0

            for client_id, connection in list(self.clients.items()):
                # Apply filters
                if tenant_id and connection.tenant_id != tenant_id:
                    continue
                if workspace_id and connection.workspace_id != workspace_id:
                    continue
                if channel and channel not in connection.subscribed_channels:
                    continue

                try:
                    await self._send_to_client(client_id, message)
                    sent_count += 1
                except Exception as e:
                    log.warning(f"Failed to send broadcast to {client_id}: {e}")

            log.debug(f"Broadcasted message to {sent_count} clients")
            return StepResult.ok(data={"sent_count": sent_count})

        except Exception as e:
            log.error(f"Error broadcasting message: {e}")
            return StepResult.fail(f"Error broadcasting message: {e}")

    async def send_agent_status_update(
        self,
        agent_id: str,
        status: str,
        details: Dict[str, Any],
        tenant_id: str = "default",
        workspace_id: str = "main",
    ) -> StepResult:
        """Send agent status update to subscribed clients."""
        message = WebSocketMessage(
            message_type=MessageType.AGENT_STATUS,
            data={
                "agent_id": agent_id,
                "status": status,
                "details": details,
            },
            timestamp=time.time(),
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )

        return await self.broadcast_message(
            message,
            channel="agent_status",
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )

    async def send_analysis_update(
        self,
        analysis_id: str,
        progress: float,
        results: Dict[str, Any],
        tenant_id: str = "default",
        workspace_id: str = "main",
    ) -> StepResult:
        """Send analysis progress update to subscribed clients."""
        message = WebSocketMessage(
            message_type=MessageType.ANALYSIS_UPDATE,
            data={
                "analysis_id": analysis_id,
                "progress": progress,
                "results": results,
            },
            timestamp=time.time(),
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )

        return await self.broadcast_message(
            message, channel="analysis", tenant_id=tenant_id, workspace_id=workspace_id
        )

    async def send_stream_update(
        self,
        stream_id: str,
        content: str,
        metadata: Dict[str, Any],
        tenant_id: str = "default",
        workspace_id: str = "main",
    ) -> StepResult:
        """Send live stream update to subscribed clients."""
        message = WebSocketMessage(
            message_type=MessageType.STREAM_UPDATE,
            data={
                "stream_id": stream_id,
                "content": content,
                "metadata": metadata,
            },
            timestamp=time.time(),
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )

        return await self.broadcast_message(
            message, channel="stream", tenant_id=tenant_id, workspace_id=workspace_id
        )

    async def send_system_alert(
        self,
        alert_type: str,
        severity: str,
        message_text: str,
        details: Dict[str, Any],
        tenant_id: str = "default",
        workspace_id: str = "main",
    ) -> StepResult:
        """Send system alert to subscribed clients."""
        message = WebSocketMessage(
            message_type=MessageType.SYSTEM_ALERT,
            data={
                "alert_type": alert_type,
                "severity": severity,
                "message": message_text,
                "details": details,
            },
            timestamp=time.time(),
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )

        return await self.broadcast_message(
            message, channel="alerts", tenant_id=tenant_id, workspace_id=workspace_id
        )

    async def send_performance_metrics(
        self,
        metrics: Dict[str, Any],
        tenant_id: str = "default",
        workspace_id: str = "main",
    ) -> StepResult:
        """Send performance metrics to subscribed clients."""
        message = WebSocketMessage(
            message_type=MessageType.PERFORMANCE_METRICS,
            data={"metrics": metrics},
            timestamp=time.time(),
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )

        return await self.broadcast_message(
            message, channel="metrics", tenant_id=tenant_id, workspace_id=workspace_id
        )

    async def _heartbeat_task(self) -> None:
        """Background task to send heartbeats to clients."""
        while self.running:
            try:
                current_time = time.time()

                for client_id, connection in list(self.clients.items()):
                    try:
                        # Send heartbeat
                        heartbeat = WebSocketMessage(
                            message_type=MessageType.HEARTBEAT,
                            data={"timestamp": current_time},
                            timestamp=current_time,
                            tenant_id=connection.tenant_id,
                            workspace_id=connection.workspace_id,
                        )
                        await self._send_to_client(client_id, heartbeat)

                    except Exception as e:
                        log.warning(f"Error sending heartbeat to {client_id}: {e}")

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                log.error(f"Error in heartbeat task: {e}")
                await asyncio.sleep(self.heartbeat_interval)

    async def _cleanup_task(self) -> None:
        """Background task to clean up stale connections."""
        while self.running:
            try:
                current_time = time.time()
                stale_clients = []

                for client_id, connection in self.clients.items():
                    # Remove clients that haven't sent heartbeat in 2 minutes
                    if current_time - connection.last_heartbeat > 120:
                        stale_clients.append(client_id)

                for client_id in stale_clients:
                    if client_id in self.clients:
                        connection = self.clients[client_id]
                        try:
                            await connection.websocket.close()
                        except Exception:
                            pass
                        del self.clients[client_id]
                        log.info(f"Removed stale client {client_id}")

                await asyncio.sleep(60)  # Cleanup every minute

            except Exception as e:
                log.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics."""
        current_time = time.time()

        stats = {
            "total_connections": len(self.clients),
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "clients": [],
        }

        for client_id, connection in self.clients.items():
            stats["clients"].append(
                {
                    "client_id": client_id,
                    "tenant_id": connection.tenant_id,
                    "workspace_id": connection.workspace_id,
                    "subscribed_channels": list(connection.subscribed_channels),
                    "connected_at": connection.connected_at,
                    "last_heartbeat": connection.last_heartbeat,
                    "uptime_seconds": current_time - connection.connected_at,
                }
            )

        return stats
