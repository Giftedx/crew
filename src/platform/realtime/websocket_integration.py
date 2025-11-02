"""WebSocket integration service for connecting WebSocket updates with system components.

This module avoids importing optional heavy dependencies (like the `websockets`
package) at import time so that minimal test environments can import the
application without requiring optional extras. Runtime imports are performed
inside methods and guarded with try/except to degrade gracefully when the
WebSocket stack is unavailable.
"""
from __future__ import annotations
import logging
import time
from platform.core.step_result import StepResult
from typing import Any
from app.config.settings import ENABLE_WEBSOCKET_UPDATES
log = logging.getLogger(__name__)

class WebSocketIntegrationService:
    """Integration service that connects WebSocket updates with system components."""

    def __init__(self):
        """Initialize WebSocket integration service."""
        self.websocket_service: Any | None = None
        self.enabled = ENABLE_WEBSOCKET_UPDATES
        if self.enabled:
            try:
                from ultimate_discord_intelligence_bot.services.websocket_service import WebSocketService
                self.websocket_service = WebSocketService()
                log.info('WebSocket integration service initialized')
            except Exception as e:
                self.enabled = False
                self.websocket_service = None
                log.info('WebSocket integration disabled (missing optional dependency): %s', e)
        else:
            log.info('WebSocket integration service disabled via feature flag')

    async def start_service(self, host: str='localhost', port: int=8765) -> StepResult:
        """Start the WebSocket integration service."""
        if not self.enabled or not self.websocket_service:
            return StepResult.fail('WebSocket integration disabled')
        try:
            result = await self.websocket_service.start_server()
            if result.success:
                log.info(f'WebSocket integration service started on {host}:{port}')
                return result
            else:
                return result
        except Exception as e:
            log.error(f'Failed to start WebSocket integration service: {e}')
            return StepResult.fail(f'Failed to start WebSocket integration service: {e}')

    async def stop_service(self) -> StepResult:
        """Stop the WebSocket integration service."""
        if not self.websocket_service:
            return StepResult.fail('WebSocket service not initialized')
        try:
            result = await self.websocket_service.stop_server()
            log.info('WebSocket integration service stopped')
            return result
        except Exception as e:
            log.error(f'Failed to stop WebSocket integration service: {e}')
            return StepResult.fail(f'Failed to stop WebSocket integration service: {e}')

    async def notify_agent_status_change(self, agent_id: str, status: str, details: dict[str, Any], tenant_id: str='default', workspace_id: str='main') -> StepResult:
        """Notify clients about agent status changes."""
        if not self.websocket_service or not self.enabled:
            return StepResult.ok(data={'notifications_sent': 0})
        try:
            result = await self.websocket_service.send_agent_status_update(agent_id=agent_id, status=status, details=details, tenant_id=tenant_id, workspace_id=workspace_id)
            if result.success:
                log.debug(f'Agent status update sent for {agent_id}: {status}')
            return result
        except Exception as e:
            log.error(f'Failed to send agent status update: {e}')
            return StepResult.fail(f'Failed to send agent status update: {e}')

    async def notify_analysis_progress(self, analysis_id: str, progress: float, results: dict[str, Any], tenant_id: str='default', workspace_id: str='main') -> StepResult:
        """Notify clients about analysis progress updates."""
        if not self.websocket_service or not self.enabled:
            return StepResult.ok(data={'notifications_sent': 0})
        try:
            result = await self.websocket_service.send_analysis_update(analysis_id=analysis_id, progress=progress, results=results, tenant_id=tenant_id, workspace_id=workspace_id)
            if result.success:
                log.debug(f'Analysis progress update sent for {analysis_id}: {progress:.1%}')
            return result
        except Exception as e:
            log.error(f'Failed to send analysis progress update: {e}')
            return StepResult.fail(f'Failed to send analysis progress update: {e}')

    async def notify_stream_update(self, stream_id: str, content: str, metadata: dict[str, Any], tenant_id: str='default', workspace_id: str='main') -> StepResult:
        """Notify clients about live stream updates."""
        if not self.websocket_service or not self.enabled:
            return StepResult.ok(data={'notifications_sent': 0})
        try:
            result = await self.websocket_service.send_stream_update(stream_id=stream_id, content=content, metadata=metadata, tenant_id=tenant_id, workspace_id=workspace_id)
            if result.success:
                log.debug(f'Stream update sent for {stream_id}')
            return result
        except Exception as e:
            log.error(f'Failed to send stream update: {e}')
            return StepResult.fail(f'Failed to send stream update: {e}')

    async def notify_system_alert(self, alert_type: str, severity: str, message: str, details: dict[str, Any], tenant_id: str='default', workspace_id: str='main') -> StepResult:
        """Notify clients about system alerts."""
        if not self.websocket_service or not self.enabled:
            return StepResult.ok(data={'notifications_sent': 0})
        try:
            result = await self.websocket_service.send_system_alert(alert_type=alert_type, severity=severity, message_text=message, details=details, tenant_id=tenant_id, workspace_id=workspace_id)
            if result.success:
                log.info(f'System alert sent: {alert_type} - {severity}')
            return result
        except Exception as e:
            log.error(f'Failed to send system alert: {e}')
            return StepResult.fail(f'Failed to send system alert: {e}')

    async def notify_performance_metrics(self, metrics: dict[str, Any], tenant_id: str='default', workspace_id: str='main') -> StepResult:
        """Notify clients about performance metrics updates."""
        if not self.websocket_service or not self.enabled:
            return StepResult.ok(data={'notifications_sent': 0})
        try:
            result = await self.websocket_service.send_performance_metrics(metrics=metrics, tenant_id=tenant_id, workspace_id=workspace_id)
            if result.success:
                log.debug('Performance metrics update sent')
            return result
        except Exception as e:
            log.error(f'Failed to send performance metrics: {e}')
            return StepResult.fail(f'Failed to send performance metrics: {e}')

    def get_service_status(self) -> StepResult:
        """Get WebSocket integration service status."""
        if not self.websocket_service:
            return {'enabled': False, 'running': False, 'reason': 'WebSocket service not initialized'}
        stats = self.websocket_service.get_connection_stats()
        return {'enabled': self.enabled, 'running': stats['running'], 'total_connections': stats['total_connections'], 'host': stats['host'], 'port': stats['port']}

    async def broadcast_custom_message(self, message_type: str, data: dict[str, Any], tenant_id: str | None=None, workspace_id: str | None=None, channel: str | None=None) -> StepResult:
        """Broadcast custom message to connected clients."""
        if not self.websocket_service or not self.enabled:
            return StepResult.ok(data={'notifications_sent': 0})
        try:
            from ultimate_discord_intelligence_bot.services.websocket_service import MessageType as _MessageType
            from ultimate_discord_intelligence_bot.services.websocket_service import WebSocketMessage
            try:
                msg_type = _MessageType(message_type)
            except ValueError:
                msg_type = _MessageType.HEARTBEAT
            message = WebSocketMessage(message_type=msg_type, data=data, timestamp=time.time(), tenant_id=tenant_id or 'default', workspace_id=workspace_id or 'main')
            result = await self.websocket_service.broadcast_message(message=message, channel=channel, tenant_id=tenant_id, workspace_id=workspace_id)
            if result.success:
                log.debug(f'Custom message broadcasted: {message_type}')
            return result
        except Exception as e:
            log.error(f'Failed to broadcast custom message: {e}')
            return StepResult.fail(f'Failed to broadcast custom message: {e}')
_websocket_integration: WebSocketIntegrationService | None = None

def get_websocket_integration() -> StepResult:
    """Get the global WebSocket integration service instance."""
    global _websocket_integration
    if _websocket_integration is None:
        _websocket_integration = WebSocketIntegrationService()
    return _websocket_integration

async def start_websocket_service(host: str='localhost', port: int=8765) -> StepResult:
    """Start the global WebSocket integration service."""
    service = get_websocket_integration()
    return await service.start_service(host, port)

async def stop_websocket_service() -> StepResult:
    """Stop the global WebSocket integration service."""
    service = get_websocket_integration()
    return await service.stop_service()

async def notify_agent_status(agent_id: str, status: str, details: dict[str, Any], tenant_id: str='default', workspace_id: str='main') -> StepResult:
    """Notify about agent status change."""
    service = get_websocket_integration()
    return await service.notify_agent_status_change(agent_id, status, details, tenant_id, workspace_id)

async def notify_analysis_progress(analysis_id: str, progress: float, results: dict[str, Any], tenant_id: str='default', workspace_id: str='main') -> StepResult:
    """Notify about analysis progress."""
    service = get_websocket_integration()
    return await service.notify_analysis_progress(analysis_id, progress, results, tenant_id, workspace_id)

async def notify_stream_update(stream_id: str, content: str, metadata: dict[str, Any], tenant_id: str='default', workspace_id: str='main') -> StepResult:
    """Notify about stream update."""
    service = get_websocket_integration()
    return await service.notify_stream_update(stream_id, content, metadata, tenant_id, workspace_id)

async def notify_system_alert(alert_type: str, severity: str, message: str, details: dict[str, Any], tenant_id: str='default', workspace_id: str='main') -> StepResult:
    """Notify about system alert."""
    service = get_websocket_integration()
    return await service.notify_system_alert(alert_type, severity, message, details, tenant_id, workspace_id)