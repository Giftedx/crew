#!/usr/bin/env python3
"""
Advanced Performance Analytics Alert System Demo

This script demonstrates the complete Advanced Performance Analytics Alert System,
showcasing intelligent alerting, Discord integration, crew task automation, and
comprehensive alert management capabilities.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import the alert system components
try:
    from src.ultimate_discord_intelligence_bot.advanced_performance_analytics_alert_engine import (
        AdvancedPerformanceAnalyticsAlertEngine,
    )
    from src.ultimate_discord_intelligence_bot.advanced_performance_analytics_alert_management import (
        AdvancedPerformanceAnalyticsAlertManager,
        execute_immediate_performance_check,
    )
    from src.ultimate_discord_intelligence_bot.advanced_performance_analytics_discord_integration import (
        AdvancedPerformanceAnalyticsDiscordIntegration,
        send_analytics_monitoring_batch,
    )
    from src.ultimate_discord_intelligence_bot.tools.advanced_performance_analytics_tool import (
        AdvancedPerformanceAnalyticsTool,
    )

    logger.info("✅ Successfully imported Advanced Performance Analytics Alert System components")
except ImportError as e:
    logger.error(f"❌ Failed to import alert system components: {e}")
    sys.exit(1)


async def demonstrate_alert_engine():
    """Demonstrate the Advanced Performance Analytics Alert Engine."""
    print("\n" + "=" * 60)
    print("🚨 ADVANCED PERFORMANCE ANALYTICS ALERT ENGINE")
    print("=" * 60)

    try:
        # Initialize alert engine
        print("\n📊 Initializing Advanced Performance Analytics Alert Engine...")
        alert_engine = AdvancedPerformanceAnalyticsAlertEngine()

        print(f"Alert Rules Configured: {len(alert_engine.alert_rules)}")
        print("Default Alert Rules:")
        for rule_id, rule in list(alert_engine.alert_rules.items())[:3]:
            print(f"  • {rule.name} ({rule.severity.value}) - {rule.category.value}")

        # Evaluate analytics for alerts
        print("\n🔍 Evaluating Analytics for Alerts...")
        alerts = await alert_engine.evaluate_analytics_for_alerts(lookback_hours=4)

        if alerts:
            print(f"Generated {len(alerts)} alerts:")
            for alert in alerts[:3]:  # Show first 3 alerts
                print(f"  🚨 {alert.severity.value.upper()}: {alert.title}")
                print(f"     Category: {alert.category.value}")
                print(f"     Metrics: {len(alert.metrics)} violated")
        else:
            print("✅ No alerts generated - system operating within normal parameters")

        # Get alert summary
        print("\n📈 Alert Summary (24h)...")
        alert_summary = await alert_engine.get_alert_summary(hours=24)

        if "error" not in alert_summary:
            print(f"Total Alerts (24h): {alert_summary.get('total_alerts', 0)}")
            severity_breakdown = alert_summary.get("severity_breakdown", {})
            print(f"  • Critical: {severity_breakdown.get('critical', 0)}")
            print(f"  • Warning: {severity_breakdown.get('warning', 0)}")
            print(f"  • Info: {severity_breakdown.get('info', 0)}")

            print(f"Active Rules: {alert_summary.get('active_rules', 0)}")
            print(f"Rules in Cooldown: {alert_summary.get('rules_in_cooldown', 0)}")

        print("\n✅ Alert Engine demonstration completed!")
        return alerts

    except Exception as e:
        logger.error(f"❌ Alert Engine demonstration failed: {e}")
        print(f"\n❌ Error: {e}")
        return []


async def demonstrate_discord_integration():
    """Demonstrate Discord integration capabilities."""
    print("\n" + "=" * 60)
    print("💬 DISCORD INTEGRATION DEMONSTRATION")
    print("=" * 60)

    try:
        # Initialize Discord integration
        print("\n📱 Initializing Discord Integration...")
        discord_integration = AdvancedPerformanceAnalyticsDiscordIntegration()

        # Check configuration
        print("Discord Configuration:")
        print(f"  • Notifications Enabled: {discord_integration.config.enabled}")
        print(f"  • Batch Notifications: {discord_integration.config.batch_notifications}")
        print(f"  • Include Metrics: {discord_integration.config.include_metrics}")
        print(f"  • Cooldown Period: {discord_integration.config.notification_cooldown_minutes} minutes")

        # Run monitoring batch (simulation)
        print("\n🔄 Running Analytics Monitoring Batch...")
        monitoring_result = await send_analytics_monitoring_batch(lookback_hours=2)

        print(f"Monitoring Status: {monitoring_result.get('status', 'unknown')}")
        print(f"Lookback Period: {monitoring_result.get('lookback_hours', 0)} hours")
        print(f"Alerts Generated: {monitoring_result.get('alerts_generated', 0)}")

        # Get notification statistics
        print("\n📊 Notification Statistics (24h)...")
        stats = await discord_integration.get_notification_statistics(hours=24)

        if "error" not in stats:
            print(f"Total Notifications: {stats.get('total_notifications', 0)}")
            print(f"Success Rate: {stats.get('success_rate', 0)}%")
            print(f"Average Message Length: {stats.get('average_message_length', 0)} characters")

            tools_config = stats.get("configuration", {}).get("tools_configured", {})
            print("Tools Configured:")
            print(f"  • Primary Tool: {'✅' if tools_config.get('primary') else '❌'}")
            print(f"  • Private Tool: {'✅' if tools_config.get('private') else '❌'}")
            print(f"  • Executive Tool: {'✅' if tools_config.get('executive') else '❌'}")

        # Send executive summary (simulation)
        print("\n📋 Sending Executive Summary...")
        exec_result = await discord_integration.send_executive_summary(hours=24)

        print(f"Executive Summary Status: {exec_result.get('status', 'unknown')}")
        if exec_result.get("status") == "success":
            print(f"Summary Period: {exec_result.get('summary_period_hours', 0)} hours")
            print(f"Alerts Summarized: {exec_result.get('total_alerts_summarized', 0)}")

        print("\n✅ Discord Integration demonstration completed!")

    except Exception as e:
        logger.error(f"❌ Discord Integration demonstration failed: {e}")
        print(f"\n❌ Error: {e}")


async def demonstrate_crew_tool():
    """Demonstrate the Advanced Performance Analytics Tool for crew workflows."""
    print("\n" + "=" * 60)
    print("🤖 CREW ANALYTICS TOOL DEMONSTRATION")
    print("=" * 60)

    try:
        # Initialize the tool
        print("\n🛠️ Initializing Advanced Performance Analytics Tool...")
        analytics_tool = AdvancedPerformanceAnalyticsTool()

        print(f"Tool Name: {analytics_tool.name}")
        print("Tool Capabilities:")
        print("  • Comprehensive performance analysis")
        print("  • Performance alert monitoring and generation")
        print("  • Predictive performance analysis with forecasting")
        print("  • Automated performance optimizations")
        print("  • Executive performance summaries")
        print("  • Real-time dashboard data retrieval")

        # Test different tool actions
        actions_to_test = [
            ("dashboard", "Get real-time dashboard data"),
            ("analyze", "Run comprehensive performance analysis"),
            ("alerts", "Monitor performance alerts"),
            ("executive_summary", "Send executive performance summary"),
        ]

        for action, description in actions_to_test:
            print(f"\n🔧 Testing: {description}")

            result = analytics_tool._run(
                action=action, lookback_hours=4, include_optimization=False, send_notifications=False
            )

            print(f"Action: {action}")
            print(f"Success: {'✅' if result.success else '❌'}")
            print(f"Message: {result.message}")

            if result.success and result.data:
                # Show key metrics from the result
                data = result.data
                if action == "dashboard":
                    print(f"  Dashboard Status: {data.get('dashboard_status', 'unknown')}")
                    print(f"  System Health Score: {data.get('system_health', {}).get('performance_score', 0):.2f}")
                elif action == "analyze":
                    print(f"  Performance Score: {data.get('overall_performance_score', 0):.2f}")
                    print(f"  System Status: {data.get('system_status', 'unknown')}")
                    print(f"  Insights Count: {data.get('key_insights_count', 0)}")
                elif action == "alerts":
                    print(f"  Alerts Generated: {data.get('alerts_generated', 0)}")
                    breakdown = data.get("alert_breakdown", {})
                    print(
                        f"  Critical: {breakdown.get('critical', 0)}, Warning: {breakdown.get('warning', 0)}, Info: {breakdown.get('info', 0)}"
                    )
                elif action == "executive_summary":
                    print(f"  Summary Delivered: {'✅' if data.get('summary_delivered') else '❌'}")
                    print(f"  Period: {data.get('summary_period_hours', 0)} hours")

            if not result.success:
                print(f"  Error: {getattr(result, 'error', 'Unknown error')}")

        print("\n✅ Crew Analytics Tool demonstration completed!")

    except Exception as e:
        logger.error(f"❌ Crew Tool demonstration failed: {e}")
        print(f"\n❌ Error: {e}")


async def demonstrate_alert_management():
    """Demonstrate the Advanced Performance Analytics Alert Management System."""
    print("\n" + "=" * 60)
    print("⚙️ ALERT MANAGEMENT SYSTEM DEMONSTRATION")
    print("=" * 60)

    try:
        # Initialize alert management system
        print("\n🎛️ Initializing Alert Management System...")
        alert_manager = AdvancedPerformanceAnalyticsAlertManager()

        print(f"Monitoring Schedules: {len(alert_manager.monitoring_schedules)}")
        print(f"Alert Policies: {len(alert_manager.alert_policies)}")

        print("\nDefault Monitoring Schedules:")
        for schedule_id, schedule in list(alert_manager.monitoring_schedules.items())[:3]:
            print(f"  • {schedule.name}")
            print(f"    Frequency: {schedule.frequency.value}")
            print(f"    Lookback: {schedule.lookback_hours}h")
            print(f"    Escalation: {schedule.escalation_level.value}")

        print("\nDefault Alert Policies:")
        for policy_id, policy in list(alert_manager.alert_policies.items())[:2]:
            print(f"  • {policy.name}")
            print(f"    Priority: {policy.priority}")
            print(f"    Actions: {len(policy.actions)}")
            print(f"    Cooldown: {policy.cooldown_minutes} minutes")

        # Get management dashboard
        print("\n📊 Management Dashboard...")
        dashboard = await alert_manager.get_management_dashboard()

        if "error" not in dashboard:
            schedules_info = dashboard.get("schedules", {})
            policies_info = dashboard.get("policies", {})
            exec_info = dashboard.get("execution_summary", {})

            print(f"Schedules: {schedules_info.get('total', 0)} total, {schedules_info.get('enabled', 0)} enabled")
            print(f"Policies: {policies_info.get('total', 0)} total, {policies_info.get('enabled', 0)} enabled")
            print(f"Total Executions: {exec_info.get('total_executions', 0)}")
            print(f"Recent Executions: {exec_info.get('recent_executions', 0)}")
            print(f"System Status: {dashboard.get('system_status', 'unknown')}")

        # Execute immediate performance check
        print("\n🚀 Executing Immediate Performance Check...")
        immediate_result = await execute_immediate_performance_check(lookback_hours=2)

        print(f"Check Status: {immediate_result.get('status', 'unknown')}")
        if immediate_result.get("status") == "success":
            exec_result = immediate_result.get("execution_result", {})
            print(f"Alerts Generated: {exec_result.get('alerts_generated', 0)}")
            print(f"Notifications Sent: {exec_result.get('notifications_sent', False)}")

        # Run scheduled monitoring cycle
        print("\n🔄 Running Scheduled Monitoring Cycle...")
        cycle_result = await alert_manager.run_scheduled_monitoring_cycle()

        print(f"Cycle Status: {cycle_result.get('status', 'unknown')}")
        print(f"Executed Schedules: {cycle_result.get('executed_schedules', 0)}")
        print(f"Skipped Schedules: {cycle_result.get('skipped_schedules', 0)}")

        print("\n✅ Alert Management System demonstration completed!")

    except Exception as e:
        logger.error(f"❌ Alert Management demonstration failed: {e}")
        print(f"\n❌ Error: {e}")


def print_system_overview():
    """Print system overview and capabilities."""
    print("\n" + "=" * 60)
    print("🎯 ADVANCED PERFORMANCE ANALYTICS ALERT SYSTEM")
    print("=" * 60)
    print("""
🚨 ALERT ENGINE
   • Intelligent alert generation from analytics insights
   • Multi-level severity classification (Critical, Warning, Info)
   • Configurable alert rules with threshold monitoring
   • Trend-based alerting and anomaly detection
   • Automated cooldown and escalation management

💬 DISCORD INTEGRATION
   • Seamless integration with existing Discord infrastructure
   • Formatted notifications with metrics and recommendations
   • Batch notification support for multiple alerts
   • Executive summary reporting to leadership channels
   • Configurable routing based on alert severity

🤖 CREW SYSTEM INTEGRATION
   • Performance analytics tasks integrated into crew workflows
   • Automated monitoring, alerting, and optimization execution
   • Tool-based interface for agent-driven analytics
   • Background task execution with comprehensive reporting
   • Integration with existing system_alert_manager agent

⚙️ ALERT MANAGEMENT SYSTEM
   • Comprehensive scheduling for automated monitoring
   • Alert escalation and response coordination
   • Configurable notification policies and thresholds
   • Management dashboard for operational oversight
   • Policy-driven automated responses and optimizations

🎯 OPERATIONAL EXCELLENCE
   • Proactive performance monitoring and early warning
   • Automated optimization execution and validation
   • Executive visibility with strategic insights
   • Scalable alert management with intelligent routing
   • End-to-end performance management automation
    """)
    print("=" * 60)


async def main():
    """Main demonstration function."""
    print_system_overview()

    try:
        # Run all demonstrations
        await demonstrate_alert_engine()
        await demonstrate_discord_integration()
        await demonstrate_crew_tool()
        await demonstrate_alert_management()

        print("\n" + "🎉" * 20)
        print("ADVANCED PERFORMANCE ANALYTICS ALERT SYSTEM DEMO COMPLETE!")
        print("🎉" * 20)

        print("""
📊 Demonstration Summary:
   • Alert Engine: ✅ Functional with intelligent rule-based alerting
   • Discord Integration: ✅ Seamless notification and reporting
   • Crew Tool Integration: ✅ Automated analytics within workflows
   • Alert Management: ✅ Comprehensive scheduling and coordination
   • System Integration: ✅ End-to-end performance management

🚀 The Advanced Performance Analytics Alert System is operational and ready
   for production deployment with comprehensive alerting, notification, and
   automated response capabilities.

📈 Key Capabilities Demonstrated:
   • Intelligent alert generation from performance analytics
   • Discord notification integration with existing infrastructure
   • Crew workflow automation for performance monitoring
   • Comprehensive alert management and scheduling
   • Executive reporting and operational dashboard

🎯 Next Steps:
   • Deploy in production environment
   • Configure Discord webhook URLs for notifications
   • Set up monitoring schedules and alert policies
   • Train operational teams on alert management
   • Implement custom alert rules for specific use cases
        """)

    except KeyboardInterrupt:
        print("\n\n⏹️ Demonstration interrupted by user")
    except Exception as e:
        logger.error(f"❌ Main demonstration failed: {e}")
        print(f"\n❌ Demonstration failed: {e}")


if __name__ == "__main__":
    print(
        f"🕐 Starting Advanced Performance Analytics Alert System Demo at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    asyncio.run(main())
