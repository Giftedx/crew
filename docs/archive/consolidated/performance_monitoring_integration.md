
# Agent Performance Monitoring Integration

To integrate performance monitoring into your Discord bot, add these hooks:

## 1. In your command handler (after agent response):

```python
from src.ultimate_discord_intelligence_bot.agent_training.performance_monitor import AgentPerformanceMonitor

monitor = AgentPerformanceMonitor()

# Record the interaction
monitor.record_agent_interaction(
    agent_name=agent_name,
    task_type=task_type,
    tools_used=tools_used,
    tool_sequence=tool_sequence,
    response_quality=quality_score,  # You'll need to calculate this
    response_time=response_time,
    user_feedback=user_feedback_dict,
    error_occurred=error_occurred,
    error_details=error_details
)
```

## 2. Quality Assessment

Implement a simple quality scoring system:

```python
def assess_response_quality(response: str, expected_criteria: dict) -> float:
    quality_score = 0.0

    # Length appropriateness (0.2 weight)
    if 100 <= len(response) <= 2000:
        quality_score += 0.2

    # Contains fact-checking (0.3 weight)
    if any(phrase in response.lower() for phrase in ["verified", "fact-check", "source"]):
        quality_score += 0.3

    # Shows reasoning (0.3 weight)
    if any(phrase in response.lower() for phrase in ["because", "analysis", "evidence"]):
        quality_score += 0.3

    # No error indicators (0.2 weight)
    if not any(phrase in response.lower() for phrase in ["error", "failed", "unable"]):
        quality_score += 0.2

    return quality_score
```

## 3. Weekly Performance Reports

Add this to your monitoring script:

```python
def generate_weekly_reports():
    monitor = AgentPerformanceMonitor()

    for agent_name in ["enhanced_fact_checker", "content_manager", "cross_platform_intelligence_gatherer"]:
        report = monitor.generate_performance_report(agent_name, days=7)
        monitor.save_performance_report(report)

        # Log key metrics
        print(f"{agent_name}: Overall Score {report.overall_score:.2f}")
        print(f"  Recommendations: {len(report.recommendations)}")
        print(f"  Training Suggestions: {len(report.training_suggestions)}")
```
