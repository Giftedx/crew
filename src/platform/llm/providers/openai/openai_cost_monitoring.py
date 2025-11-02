"""OpenAI cost monitoring and usage tracking service."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from app.config.settings import Settings

@dataclass
class UsageMetrics:
    """Usage metrics for OpenAI services."""
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class CostAlert:
    """Cost alert configuration."""
    threshold: float
    message: str
    triggered: bool = False
    last_triggered: datetime | None = None

class OpenAICostMonitoringService:
    """Service for monitoring OpenAI usage and costs."""

    def __init__(self):
        self.settings = Settings()
        self.metrics = UsageMetrics()
        self.daily_metrics: dict[str, UsageMetrics] = {}
        self.monthly_metrics: dict[str, UsageMetrics] = {}
        self.daily_cost = 0.0
        self.monthly_cost = 0.0
        self.cost_alerts: list[CostAlert] = []
        self.token_pricing = {'gpt-4o': {'input': 0.005, 'output': 0.015}, 'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006}, 'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002}, 'tts-1': {'input': 0.015, 'output': 0.0}, 'whisper-1': {'input': 0.006, 'output': 0.0}}
        self._setup_cost_alerts()

    def _setup_cost_alerts(self) -> None:
        """Setup cost alert thresholds."""
        self.cost_alerts = [CostAlert(threshold=10.0, message='Daily cost exceeded $10'), CostAlert(threshold=50.0, message='Daily cost exceeded $50'), CostAlert(threshold=100.0, message='Daily cost exceeded $100'), CostAlert(threshold=500.0, message='Monthly cost exceeded $500'), CostAlert(threshold=1000.0, message='Monthly cost exceeded $1000')]

    def calculate_token_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        if model not in self.token_pricing:
            return 0.0
        pricing = self.token_pricing[model]
        input_cost = input_tokens / 1000 * pricing['input']
        output_cost = output_tokens / 1000 * pricing['output']
        return input_cost + output_cost

    def calculate_audio_cost(self, model: str, duration_seconds: float) -> float:
        """Calculate cost for audio processing."""
        if model not in self.token_pricing:
            return 0.0
        pricing = self.token_pricing[model]
        duration_minutes = duration_seconds / 60
        return duration_minutes * pricing['input']

    def calculate_tts_cost(self, text_length: int) -> float:
        """Calculate cost for text-to-speech."""
        pricing = self.token_pricing['tts-1']
        return text_length / 1000 * pricing['input']

    async def record_request(self, model: str, input_tokens: int=0, output_tokens: int=0, response_time: float=0.0, success: bool=True, audio_duration: float=0.0, tts_length: int=0) -> None:
        """Record a request and update metrics."""
        try:
            token_cost = self.calculate_token_cost(model, input_tokens, output_tokens)
            audio_cost = self.calculate_audio_cost(model, audio_duration) if audio_duration > 0 else 0.0
            tts_cost = self.calculate_tts_cost(tts_length) if tts_length > 0 else 0.0
            total_cost = token_cost + audio_cost + tts_cost
            self.metrics.request_count += 1
            self.metrics.total_tokens += input_tokens + output_tokens
            self.metrics.total_cost += total_cost
            if success:
                self.metrics.success_count += 1
            else:
                self.metrics.error_count += 1
            if response_time > 0:
                self.metrics.average_response_time = (self.metrics.average_response_time * (self.metrics.request_count - 1) + response_time) / self.metrics.request_count
            today = datetime.utcnow().strftime('%Y-%m-%d')
            this_month = datetime.utcnow().strftime('%Y-%m')
            if today not in self.daily_metrics:
                self.daily_metrics[today] = UsageMetrics()
            if this_month not in self.monthly_metrics:
                self.monthly_metrics[this_month] = UsageMetrics()
            daily = self.daily_metrics[today]
            daily.request_count += 1
            daily.total_tokens += input_tokens + output_tokens
            daily.total_cost += total_cost
            daily.last_updated = datetime.utcnow()
            if success:
                daily.success_count += 1
            else:
                daily.error_count += 1
            monthly = self.monthly_metrics[this_month]
            monthly.request_count += 1
            monthly.total_tokens += input_tokens + output_tokens
            monthly.total_cost += total_cost
            monthly.last_updated = datetime.utcnow()
            if success:
                monthly.success_count += 1
            else:
                monthly.error_count += 1
            self.daily_cost += total_cost
            self.monthly_cost += total_cost
            await self._check_cost_alerts()
        except Exception as e:
            print(f'Error recording request metrics: {e}')

    async def _check_cost_alerts(self) -> None:
        """Check for cost alert thresholds."""
        try:
            for alert in self.cost_alerts:
                if not alert.triggered and self.daily_cost >= alert.threshold:
                    alert.triggered = True
                    alert.last_triggered = datetime.utcnow()
                    print(f'COST ALERT: {alert.message} (Current: ${self.daily_cost:.2f})')
                elif alert.triggered and self.daily_cost < alert.threshold * 0.8:
                    alert.triggered = False
        except Exception as e:
            print(f'Error checking cost alerts: {e}')

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current usage metrics."""
        return {'total_requests': self.metrics.request_count, 'successful_requests': self.metrics.success_count, 'failed_requests': self.metrics.error_count, 'total_tokens': self.metrics.total_tokens, 'total_cost': self.metrics.total_cost, 'daily_cost': self.daily_cost, 'monthly_cost': self.monthly_cost, 'average_response_time': self.metrics.average_response_time, 'last_updated': self.metrics.last_updated.isoformat()}

    def get_daily_metrics(self, date: str | None=None) -> dict[str, Any]:
        """Get daily metrics for a specific date."""
        if date is None:
            date = datetime.utcnow().strftime('%Y-%m-%d')
        if date not in self.daily_metrics:
            return {'error': f'No metrics found for date: {date}'}
        daily = self.daily_metrics[date]
        return {'date': date, 'requests': daily.request_count, 'successful': daily.success_count, 'failed': daily.error_count, 'tokens': daily.total_tokens, 'cost': daily.total_cost, 'last_updated': daily.last_updated.isoformat()}

    def get_monthly_metrics(self, month: str | None=None) -> dict[str, Any]:
        """Get monthly metrics for a specific month."""
        if month is None:
            month = datetime.utcnow().strftime('%Y-%m')
        if month not in self.monthly_metrics:
            return {'error': f'No metrics found for month: {month}'}
        monthly = self.monthly_metrics[month]
        return {'month': month, 'requests': monthly.request_count, 'successful': monthly.success_count, 'failed': monthly.error_count, 'tokens': monthly.total_tokens, 'cost': monthly.total_cost, 'last_updated': monthly.last_updated.isoformat()}

    def get_cost_summary(self) -> dict[str, Any]:
        """Get cost summary with projections."""
        try:
            days_with_data = len(self.daily_metrics)
            avg_daily_cost = self.monthly_cost / days_with_data if days_with_data > 0 else 0.0
            days_in_month = 30
            projected_monthly = avg_daily_cost * days_in_month
            return {'current_daily_cost': self.daily_cost, 'current_monthly_cost': self.monthly_cost, 'average_daily_cost': avg_daily_cost, 'projected_monthly_cost': projected_monthly, 'days_with_data': days_with_data, 'cost_alerts': [{'threshold': alert.threshold, 'message': alert.message, 'triggered': alert.triggered, 'last_triggered': alert.last_triggered.isoformat() if alert.last_triggered else None} for alert in self.cost_alerts]}
        except Exception as e:
            return {'error': f'Error calculating cost summary: {e!s}'}

    async def reset_daily_metrics(self) -> None:
        """Reset daily metrics (call at start of each day)."""
        self.daily_cost = 0.0
        for alert in self.cost_alerts:
            if 'daily' in alert.message.lower():
                alert.triggered = False

    async def reset_monthly_metrics(self) -> None:
        """Reset monthly metrics (call at start of each month)."""
        self.monthly_cost = 0.0
        for alert in self.cost_alerts:
            if 'monthly' in alert.message.lower():
                alert.triggered = False

    def export_metrics(self) -> dict[str, Any]:
        """Export all metrics for analysis."""
        return {'current_metrics': self.get_current_metrics(), 'daily_metrics': {date: self.get_daily_metrics(date) for date in self.daily_metrics}, 'monthly_metrics': {month: self.get_monthly_metrics(month) for month in self.monthly_metrics}, 'cost_summary': self.get_cost_summary(), 'export_timestamp': datetime.utcnow().isoformat()}