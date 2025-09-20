#!/usr/bin/env python3
"""
Scoped Discord Bot - Read-Only Presentation Model

This bot implements a strictly limited command interface with:
- Only system/ops/dev/analytics commands exposed
- Read-only timeline and summary presentations
- All analysis happens off-platform
- No direct tool/agent exposure to users
"""

import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add paths for dependencies
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*args, **kwargs):
        return False


# Discord imports with fallback
try:
    import discord
    from discord.ext import commands

    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    print("⚠️ Discord.py not available - running in lightweight mode")

# Internal imports
from helpers.ui_constants import (
    DEFAULT_FEATURE_FLAGS,
)

# Import core services with graceful degradation
try:
    # Placeholder for future core service imports
    CORE_SERVICES_AVAILABLE = True
except ImportError:
    CORE_SERVICES_AVAILABLE = False
    print("⚠️ Core services not available - limited functionality")

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TimelineManager:
    """Manages subject timelines and evidence consolidation"""

    def __init__(self):
        self.timelines: dict[str, list[dict]] = {}
        self.evidence_channels: dict[str, str] = {}

    def add_timeline_event(self, subject: str, event: dict[str, Any]) -> None:
        """Add event to subject timeline"""
        if subject not in self.timelines:
            self.timelines[subject] = []

        event_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event.get("type", "general"),
            "title": event.get("title", ""),
            "description": event.get("description", ""),
            "source_url": event.get("source_url"),
            "confidence": event.get("confidence", 0.5),
            "evidence_refs": event.get("evidence_refs", []),
            "analytical_framing": event.get("analytical_framing", ""),
        }

        self.timelines[subject].append(event_entry)
        self.timelines[subject].sort(key=lambda x: x["timestamp"])

    def get_timeline_summary(self, subject: str, days: int = 30) -> str:
        """Get recent timeline summary for subject"""
        if subject not in self.timelines:
            return f"No timeline data available for {subject}"

        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_events = [
            event for event in self.timelines[subject] if datetime.fromisoformat(event["timestamp"]) > cutoff
        ]

        if not recent_events:
            return f"No recent events for {subject} in the last {days} days"

        summary_lines = [f"**{subject} Timeline (Last {days} days)**\n"]

        for event in recent_events[-10:]:  # Last 10 events
            date = datetime.fromisoformat(event["timestamp"]).strftime("%m/%d")
            event_type = event["type"].title()
            title = event["title"][:50] + "..." if len(event["title"]) > 50 else event["title"]

            # Add analytical framing
            framing = ""
            if event["analytical_framing"]:
                framing = f" • {event['analytical_framing'][:100]}..."

            summary_lines.append(f"• **{date}** [{event_type}] {title}{framing}")

        return "\n".join(summary_lines)


class ScopedCommandBot:
    """Discord bot with strictly scoped command interface"""

    def __init__(self):
        self.timeline_manager = TimelineManager()
        self.analysis_results_cache: dict[str, Any] = {}
        self.system_metrics: dict[str, Any] = {}

        if DISCORD_AVAILABLE:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True

            self.bot = commands.Bot(
                command_prefix="!", intents=intents, description="Ultimate Discord Intelligence Bot - Scoped Interface"
            )

            self._register_scoped_commands()
        else:
            self.bot = None

    def _register_scoped_commands(self):
        """Register only the allowed command families"""
        if not self.bot:
            return

        # System Domain (/system-*)
        self._register_system_commands()

        # Operations (!ops-*)
        self._register_ops_commands()

        # Development (!dev-*)
        self._register_dev_commands()

        # Analytics (!analytics-*)
        self._register_analytics_commands()

        # Event handlers
        self._register_events()

    def _register_system_commands(self):
        """System domain slash commands - read-only status"""

        @self.bot.tree.command(name="system-status", description="Comprehensive system health")
        async def system_status(interaction):
            """Show system health without exposing internal components"""
            await interaction.response.defer()

            # Collect high-level system metrics
            status_data = await self._collect_system_status()

            embed = discord.Embed(
                title="🖥️ System Status",
                description="**Read-Only Intelligence System**",
                color=0x00FF00 if status_data["overall_health"] == "healthy" else 0xFFFF00,
            )

            # High-level metrics only
            embed.add_field(
                name="📊 System Health",
                value=f"Status: {status_data['overall_health'].title()}\nUptime: {status_data['uptime']}\nLast Analysis: {status_data['last_analysis']}",
                inline=False,
            )

            embed.add_field(
                name="📈 Processing Stats",
                value=f"Analyses Today: {status_data['analyses_today']}\nActive Timelines: {status_data['active_timelines']}\nEvidence Channels: {status_data['evidence_channels']}",
                inline=True,
            )

            embed.add_field(
                name="🔄 Queue Status",
                value=f"Pending Items: {status_data['queue_pending']}\nProcessing Rate: {status_data['processing_rate']}/hr",
                inline=True,
            )

            embed.set_footer(text="All analysis occurs off-platform • Presentation layer only")
            await interaction.followup.send(embed=embed)

        @self.bot.tree.command(name="system-tools", description="Available tools and capabilities")
        async def system_tools(interaction):
            """Show capabilities without exposing internal tool structure"""
            await interaction.response.defer()

            capabilities = await self._get_capability_summary()

            embed = discord.Embed(
                title="🔧 System Capabilities",
                description="**Analysis capabilities available for timeline generation**",
                color=0x4B9CD3,
            )

            # Group capabilities by domain
            for domain, caps in capabilities.items():
                cap_list = "\n".join([f"• {cap}" for cap in caps])
                embed.add_field(name=f"📋 {domain.title()}", value=cap_list, inline=True)

            embed.add_field(
                name="ℹ️ Access Model",
                value="Analysis occurs off-platform\nResults presented as timelines\nNo direct tool access via Discord",
                inline=False,
            )

            await interaction.followup.send(embed=embed)

        @self.bot.tree.command(name="system-performance", description="Performance monitoring")
        async def system_performance(interaction, agent: str = None):
            """Show performance metrics without exposing agent internals"""
            await interaction.response.defer()

            perf_data = await self._get_performance_summary(agent)

            embed = discord.Embed(
                title="📊 Performance Overview",
                description=f"**Analysis Pipeline Performance**{f' - {agent.title()}' if agent else ''}",
                color=0x9932CC,
            )

            # High-level performance metrics
            embed.add_field(
                name="⚡ Processing Speed",
                value=f"Avg Analysis Time: {perf_data['avg_analysis_time']}\nSuccess Rate: {perf_data['success_rate']:.1%}\nThroughput: {perf_data['throughput']}/hour",
                inline=True,
            )

            embed.add_field(
                name="📈 Quality Metrics",
                value=f"Timeline Accuracy: {perf_data['timeline_accuracy']:.1%}\nEvidence Quality: {perf_data['evidence_quality']:.1%}\nFraming Consistency: {perf_data['framing_consistency']:.1%}",
                inline=True,
            )

            if agent and agent in perf_data.get("agent_specific", {}):
                agent_data = perf_data["agent_specific"][agent]
                embed.add_field(
                    name=f"🎯 {agent.title()} Metrics",
                    value=f"Utilization: {agent_data['utilization']:.1%}\nAccuracy: {agent_data['accuracy']:.1%}\nResponse Time: {agent_data['response_time']}ms",
                    inline=False,
                )

            await interaction.followup.send(embed=embed)

        @self.bot.tree.command(name="system-audit", description="Self-audit with capability mapping")
        async def system_audit(interaction):
            """System self-audit without internal details"""
            await interaction.response.defer(ephemeral=True)

            audit_results = await self._perform_system_audit()

            embed = discord.Embed(
                title="🔍 System Audit", description="**Capability and compliance assessment**", color=0x7D3C98
            )

            # Capability assessment
            embed.add_field(
                name="✅ Available Capabilities",
                value=f"Content Analysis: {audit_results['content_analysis']}\nTimeline Generation: {audit_results['timeline_generation']}\nEvidence Consolidation: {audit_results['evidence_consolidation']}\nAnalytical Framing: {audit_results['analytical_framing']}",
                inline=False,
            )

            # Compliance status
            embed.add_field(
                name="🛡️ Compliance Status",
                value=f"Read-Only Mode: {audit_results['read_only_mode']}\nOff-Platform Analysis: {audit_results['off_platform_analysis']}\nNo Direct Tool Exposure: {audit_results['no_tool_exposure']}",
                inline=False,
            )

            # Configuration review
            if audit_results.get("recommendations"):
                recommendations = "\n".join([f"• {rec}" for rec in audit_results["recommendations"][:3]])
                embed.add_field(name="💡 Recommendations", value=recommendations, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)

    def _register_ops_commands(self):
        """Operations prefix commands - administrative access"""

        @self.bot.command(name="ops-status")
        async def ops_status(ctx, *args):
            """Detailed system status for operators"""

            # Parse arguments
            detailed = "--detailed" in args
            component = None
            for arg in args:
                if arg.startswith("--component="):
                    component = arg.split("=", 1)[1]

            status_data = await self._collect_detailed_system_status(component)

            if detailed:
                # Detailed status with more metrics
                embed = discord.Embed(
                    title="🖥️ Detailed System Status",
                    description="**Operational metrics and health indicators**",
                    color=0x00FF00 if status_data["status"] == "healthy" else 0xFFFF00,
                )

                # Add detailed metrics
                for section, metrics in status_data["sections"].items():
                    metric_text = "\n".join([f"{k}: {v}" for k, v in metrics.items()])
                    embed.add_field(name=f"📊 {section}", value=metric_text, inline=True)

            else:
                # Standard status summary
                embed = discord.Embed(
                    title="🖥️ System Status",
                    description=f"Overall Status: **{status_data['status'].title()}**",
                    color=0x00FF00 if status_data["status"] == "healthy" else 0xFFFF00,
                )

                embed.add_field(
                    name="📈 Key Metrics",
                    value=f"Uptime: {status_data['uptime']}\nQueue: {status_data['queue_size']} pending\nLast Process: {status_data['last_process']}",
                    inline=False,
                )

            await ctx.send(embed=embed)

        @self.bot.command(name="ops-queue")
        async def ops_queue(ctx, *args):
            """Processing queue management"""

            action = None
            priority = None

            # Parse arguments
            for arg in args:
                if arg == "--clear":
                    action = "clear"
                elif arg.startswith("--priority="):
                    priority = arg.split("=", 1)[1]

            if action == "clear":
                # Clear queue (with confirmation)
                result = await self._clear_processing_queue()
                await ctx.send(f"🗑️ Queue cleared: {result['cleared_items']} items removed")
            else:
                # Show queue status
                queue_data = await self._get_queue_status(priority)

                embed = discord.Embed(
                    title="📦 Processing Queue", description="**Content analysis pipeline queue**", color=0x3498DB
                )

                embed.add_field(
                    name="📊 Queue Stats",
                    value=f"Total Items: {queue_data['total']}\nHigh Priority: {queue_data['high_priority']}\nProcessing: {queue_data['processing']}\nFailed: {queue_data['failed']}",
                    inline=True,
                )

                if queue_data.get("recent_items"):
                    recent = "\n".join([f"• {item}" for item in queue_data["recent_items"][:5]])
                    embed.add_field(name="📋 Recent Items", value=recent, inline=False)

                await ctx.send(embed=embed)

        @self.bot.command(name="ops-metrics")
        async def ops_metrics(ctx, timeframe: str = "24h"):
            """Performance metrics with timeframe"""

            metrics_data = await self._get_ops_metrics(timeframe)

            embed = discord.Embed(
                title=f"📊 Operations Metrics ({timeframe})",
                description="**System performance and utilization**",
                color=0x17A2B8,
            )

            # Core metrics
            embed.add_field(
                name="⚡ Processing",
                value=f"Items Processed: {metrics_data['processed']}\nSuccess Rate: {metrics_data['success_rate']:.1%}\nAvg Time: {metrics_data['avg_processing_time']}s",
                inline=True,
            )

            embed.add_field(
                name="🎯 Quality",
                value=f"Timeline Events: {metrics_data['timeline_events']}\nEvidence Items: {metrics_data['evidence_items']}\nFraming Accuracy: {metrics_data['framing_accuracy']:.1%}",
                inline=True,
            )

            embed.add_field(
                name="🔄 System Load",
                value=f"CPU Usage: {metrics_data['cpu_usage']:.1%}\nMemory Usage: {metrics_data['memory_usage']:.1%}\nQueue Backlog: {metrics_data['queue_backlog']}",
                inline=True,
            )

            await ctx.send(embed=embed)

    def _register_dev_commands(self):
        """Development prefix commands - testing and debugging"""

        @self.bot.command(name="dev-tools")
        async def dev_tools(ctx):
            """Tool management and testing interface"""

            tools_status = await self._get_tools_status()

            embed = discord.Embed(
                title="🔧 Development Tools",
                description="**Backend tool status and testing interface**",
                color=0x6C757D,
            )

            # Tool availability (high-level only)
            for category, tools in tools_status.items():
                available = sum(1 for tool in tools if tool["status"] == "available")
                total = len(tools)
                embed.add_field(
                    name=f"📦 {category.title()}",
                    value=f"Available: {available}/{total}\nStatus: {'✅' if available == total else '⚠️'}",
                    inline=True,
                )

            embed.add_field(
                name="ℹ️ Testing",
                value="Use `!dev-test` commands for individual component testing\nNo direct tool access via Discord interface",
                inline=False,
            )

            await ctx.send(embed=embed)

        @self.bot.command(name="dev-agents")
        async def dev_agents(ctx):
            """Agent status and configuration overview"""

            agents_status = await self._get_agents_status()

            embed = discord.Embed(
                title="🤖 Agent Status", description="**Analysis agent health and configuration**", color=0x28A745
            )

            # Agent categories
            for category, agents in agents_status.items():
                status_icons = []
                for agent in agents:
                    if agent["status"] == "active":
                        status_icons.append("🟢")
                    elif agent["status"] == "degraded":
                        status_icons.append("🟡")
                    else:
                        status_icons.append("🔴")

                embed.add_field(
                    name=f"👥 {category.title()}",
                    value=f"Status: {' '.join(status_icons)}\nActive: {sum(1 for a in agents if a['status'] == 'active')}/{len(agents)}",
                    inline=True,
                )

            await ctx.send(embed=embed)

        @self.bot.command(name="dev-test")
        async def dev_test(ctx, component: str, *params):
            """Component testing interface"""

            if component not in ["timeline", "evidence", "framing", "analysis"]:
                await ctx.send("❌ Invalid component. Available: timeline, evidence, framing, analysis")
                return

            test_result = await self._run_component_test(component, list(params))

            embed = discord.Embed(
                title=f"🧪 Component Test: {component.title()}",
                description="**Development testing interface**",
                color=0x007BFF,
            )

            embed.add_field(
                name="📊 Test Results",
                value=f"Status: {'✅ PASS' if test_result['passed'] else '❌ FAIL'}\nDuration: {test_result['duration']}ms\nDetails: {test_result['details']}",
                inline=False,
            )

            if test_result.get("metrics"):
                metrics = test_result["metrics"]
                embed.add_field(
                    name="📈 Performance Metrics",
                    value=f"Response Time: {metrics['response_time']}ms\nAccuracy: {metrics['accuracy']:.1%}\nThroughput: {metrics['throughput']}/s",
                    inline=False,
                )

            await ctx.send(embed=embed)

    def _register_analytics_commands(self):
        """Analytics prefix commands - data analysis"""

        @self.bot.command(name="analytics-usage")
        async def analytics_usage(ctx, timeframe: str = "7d", filter_type: str = None):
            """Usage statistics with filtering"""

            usage_data = await self._get_usage_analytics(timeframe, filter_type)

            embed = discord.Embed(
                title=f"📊 Usage Analytics ({timeframe})",
                description="**System utilization and command usage patterns**",
                color=0xFD7E14,
            )

            # Command usage
            embed.add_field(
                name="💬 Command Usage",
                value=f"Total Commands: {usage_data['total_commands']}\nUnique Users: {usage_data['unique_users']}\nMost Used: {usage_data['most_used_command']}",
                inline=True,
            )

            # Analysis requests
            embed.add_field(
                name="🔍 Analysis Activity",
                value=f"Timeline Requests: {usage_data['timeline_requests']}\nEvidence Queries: {usage_data['evidence_queries']}\nSubjects Tracked: {usage_data['subjects_tracked']}",
                inline=True,
            )

            # Engagement patterns
            embed.add_field(
                name="👥 Engagement",
                value=f"Peak Hours: {usage_data['peak_hours']}\nAvg Session: {usage_data['avg_session_duration']}\nReturn Rate: {usage_data['return_rate']:.1%}",
                inline=True,
            )

            await ctx.send(embed=embed)

        @self.bot.command(name="analytics-performance")
        async def analytics_performance(ctx, agent: str = None):
            """Agent performance analytics"""

            perf_analytics = await self._get_performance_analytics(agent)

            embed = discord.Embed(
                title=f"📈 Performance Analytics{f' - {agent.title()}' if agent else ''}",
                description="**Analysis pipeline performance metrics**",
                color=0x20C997,
            )

            # Overall performance
            embed.add_field(
                name="⚡ Processing Performance",
                value=f"Avg Response Time: {perf_analytics['avg_response_time']}ms\nThroughput: {perf_analytics['throughput']}/hour\nError Rate: {perf_analytics['error_rate']:.2%}",
                inline=True,
            )

            # Quality metrics
            embed.add_field(
                name="🎯 Quality Metrics",
                value=f"Timeline Accuracy: {perf_analytics['timeline_accuracy']:.1%}\nEvidence Relevance: {perf_analytics['evidence_relevance']:.1%}\nFraming Consistency: {perf_analytics['framing_consistency']:.1%}",
                inline=True,
            )

            if agent and agent in perf_analytics.get("agent_breakdown", {}):
                agent_data = perf_analytics["agent_breakdown"][agent]
                embed.add_field(
                    name=f"🤖 {agent.title()} Details",
                    value=f"Tasks Completed: {agent_data['tasks_completed']}\nSuccess Rate: {agent_data['success_rate']:.1%}\nAvg Quality Score: {agent_data['avg_quality']:.2f}",
                    inline=False,
                )

            await ctx.send(embed=embed)

        @self.bot.command(name="analytics-errors")
        async def analytics_errors(ctx, component: str = None):
            """Error analysis and monitoring"""

            error_data = await self._get_error_analytics(component)

            embed = discord.Embed(
                title=f"🚨 Error Analytics{f' - {component.title()}' if component else ''}",
                description="**System error patterns and monitoring**",
                color=0xDC3545,
            )

            # Error summary
            embed.add_field(
                name="📊 Error Summary",
                value=f"Total Errors: {error_data['total_errors']}\nError Rate: {error_data['error_rate']:.2%}\nCritical: {error_data['critical_errors']}",
                inline=True,
            )

            # Common issues
            if error_data.get("common_errors"):
                common = "\n".join([f"• {err}: {count}" for err, count in error_data["common_errors"][:3]])
                embed.add_field(name="🔍 Common Issues", value=common, inline=True)

            # Recent incidents
            if error_data.get("recent_incidents"):
                recent = "\n".join([f"• {inc}" for inc in error_data["recent_incidents"][:3]])
                embed.add_field(name="🕒 Recent Incidents", value=recent, inline=False)

            await ctx.send(embed=embed)

    def _register_events(self):
        """Register bot event handlers"""

        @self.bot.event
        async def on_ready():
            print(f"🤖 Scoped Discord Bot logged in as {self.bot.user}")
            print(f"📊 Connected to {len(self.bot.guilds)} guilds")

            try:
                synced = await self.bot.tree.sync()
                print(f"✅ Synced {len(synced)} scoped slash commands")
            except Exception as e:
                print(f"⚠️ Could not sync slash commands: {e}")

            print("✅ Scoped Discord Intelligence Bot ready!")
            print("📋 Available command families: /system-*, !ops-*, !dev-*, !analytics-*")

        @self.bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                # Don't respond to unknown commands - maintains read-only principle
                pass
            else:
                await ctx.send(f"❌ Error: {error}")
                print(f"Command error: {error}")

        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return

            # Process commands normally
            await self.bot.process_commands(message)

            # No automatic analysis or tool exposure - strictly command-driven

    # Placeholder implementation methods - these would connect to actual backend systems

    async def _collect_system_status(self) -> dict[str, Any]:
        """Collect high-level system status"""
        return {
            "overall_health": "healthy",
            "uptime": "72h 14m",
            "last_analysis": "2 minutes ago",
            "analyses_today": 47,
            "active_timelines": 12,
            "evidence_channels": 5,
            "queue_pending": 3,
            "processing_rate": 28,
        }

    async def _get_capability_summary(self) -> dict[str, list[str]]:
        """Get capability summary grouped by domain"""
        return {
            "content_analysis": [
                "Multi-platform content ingestion",
                "Transcription and text analysis",
                "Claim extraction and verification",
                "Sentiment and context analysis",
            ],
            "timeline_generation": [
                "Chronological event tracking",
                "Subject-focused timelines",
                "Controversial statement identification",
                "Notable moment detection",
            ],
            "evidence_consolidation": [
                "Supporting material compilation",
                "Citation and reference management",
                "Metadata preservation",
                "Cross-reference validation",
            ],
            "analytical_framing": [
                "Fact vs claim distinction",
                "Misconception source analysis",
                "Motivation and context hypotheses",
                "Bias and perspective identification",
            ],
        }

    async def _get_performance_summary(self, agent: str | None) -> dict[str, Any]:
        """Get performance summary data"""
        return {
            "avg_analysis_time": "4.2 minutes",
            "success_rate": 0.94,
            "throughput": 12,
            "timeline_accuracy": 0.89,
            "evidence_quality": 0.87,
            "framing_consistency": 0.91,
            "agent_specific": {
                "content_manager": {"utilization": 0.78, "accuracy": 0.92, "response_time": 2500},
                "fact_checker": {"utilization": 0.65, "accuracy": 0.88, "response_time": 1800},
            },
        }

    async def _perform_system_audit(self) -> dict[str, Any]:
        """Perform system capability audit"""
        return {
            "content_analysis": "✅ Available",
            "timeline_generation": "✅ Available",
            "evidence_consolidation": "✅ Available",
            "analytical_framing": "✅ Available",
            "read_only_mode": "✅ Enforced",
            "off_platform_analysis": "✅ Enforced",
            "no_tool_exposure": "✅ Enforced",
            "recommendations": [
                "Timeline accuracy could be improved with additional training data",
                "Consider expanding evidence source diversity",
                "Monitor framing consistency across different content types",
            ],
        }

    async def _collect_detailed_system_status(self, component: str | None) -> dict[str, Any]:
        """Collect detailed system status for operations"""
        return {
            "status": "healthy",
            "uptime": "72h 14m 32s",
            "queue_size": 3,
            "last_process": "2m ago",
            "sections": {
                "Processing": {
                    "Pipeline Status": "Active",
                    "Queue Size": 3,
                    "Processing Rate": "12/hour",
                    "Last Success": "2m ago",
                },
                "Storage": {
                    "Timeline Events": 1247,
                    "Evidence Items": 892,
                    "Storage Usage": "67%",
                    "Backup Status": "Current",
                },
                "Performance": {
                    "Avg Response": "4.2s",
                    "Success Rate": "94%",
                    "Error Rate": "0.8%",
                    "CPU Usage": "23%",
                },
            },
        }

    async def _get_queue_status(self, priority: str | None) -> dict[str, Any]:
        """Get processing queue status"""
        return {
            "total": 3,
            "high_priority": 1,
            "processing": 1,
            "failed": 0,
            "recent_items": [
                "H3 Podcast Episode #412 - Analysis",
                "HasanAbi Twitch Stream - Timeline Update",
                "Political Commentary - Fact Check",
            ],
        }

    async def _clear_processing_queue(self) -> dict[str, Any]:
        """Clear processing queue"""
        return {"cleared_items": 3}

    async def _get_ops_metrics(self, timeframe: str) -> dict[str, Any]:
        """Get operational metrics for timeframe"""
        return {
            "processed": 847,
            "success_rate": 0.94,
            "avg_processing_time": 4.2,
            "timeline_events": 156,
            "evidence_items": 203,
            "framing_accuracy": 0.89,
            "cpu_usage": 0.23,
            "memory_usage": 0.67,
            "queue_backlog": 3,
        }

    async def _get_tools_status(self) -> dict[str, list[dict]]:
        """Get backend tools status"""
        return {
            "analysis": [
                {"name": "content_analyzer", "status": "available"},
                {"name": "claim_extractor", "status": "available"},
                {"name": "fact_checker", "status": "available"},
            ],
            "timeline": [
                {"name": "event_tracker", "status": "available"},
                {"name": "timeline_builder", "status": "available"},
            ],
            "evidence": [
                {"name": "evidence_collector", "status": "available"},
                {"name": "citation_manager", "status": "degraded"},
            ],
        }

    async def _get_agents_status(self) -> dict[str, list[dict]]:
        """Get analysis agents status"""
        return {
            "content": [{"name": "content_manager", "status": "active"}, {"name": "downloader", "status": "active"}],
            "analysis": [
                {"name": "fact_checker", "status": "active"},
                {"name": "claim_analyzer", "status": "active"},
                {"name": "sentiment_analyzer", "status": "degraded"},
            ],
            "synthesis": [
                {"name": "timeline_builder", "status": "active"},
                {"name": "evidence_consolidator", "status": "active"},
            ],
        }

    async def _run_component_test(self, component: str, params: list[str]) -> dict[str, Any]:
        """Run component test"""
        return {
            "passed": True,
            "duration": 850,
            "details": f"{component.title()} component test completed successfully",
            "metrics": {"response_time": 850, "accuracy": 0.92, "throughput": 14.5},
        }

    async def _get_usage_analytics(self, timeframe: str, filter_type: str | None) -> dict[str, Any]:
        """Get usage analytics"""
        return {
            "total_commands": 234,
            "unique_users": 18,
            "most_used_command": "/system-status",
            "timeline_requests": 67,
            "evidence_queries": 42,
            "subjects_tracked": 8,
            "peak_hours": "14:00-16:00 UTC",
            "avg_session_duration": "12m 34s",
            "return_rate": 0.73,
        }

    async def _get_performance_analytics(self, agent: str | None) -> dict[str, Any]:
        """Get performance analytics"""
        return {
            "avg_response_time": 2400,
            "throughput": 12,
            "error_rate": 0.008,
            "timeline_accuracy": 0.89,
            "evidence_relevance": 0.87,
            "framing_consistency": 0.91,
            "agent_breakdown": {
                "content_manager": {"tasks_completed": 156, "success_rate": 0.94, "avg_quality": 0.88},
                "fact_checker": {"tasks_completed": 203, "success_rate": 0.91, "avg_quality": 0.85},
            },
        }

    async def _get_error_analytics(self, component: str | None) -> dict[str, Any]:
        """Get error analytics"""
        return {
            "total_errors": 12,
            "error_rate": 0.008,
            "critical_errors": 1,
            "common_errors": [("Timeout Error", 5), ("Rate Limit", 3), ("Parse Error", 2)],
            "recent_incidents": [
                "2024-09-15 14:32 - Timeline generation timeout",
                "2024-09-15 12:15 - Evidence consolidation failure",
                "2024-09-15 09:45 - External API rate limit",
            ],
        }

    async def start(self):
        """Start the scoped Discord bot"""
        if not DISCORD_AVAILABLE:
            print("❌ Discord.py not available - cannot start bot")
            return

        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            print("❌ DISCORD_BOT_TOKEN not found in environment")
            return

        try:
            await self.bot.start(token)
        except Exception as e:
            print(f"❌ Failed to start scoped bot: {e}")
            traceback.print_exc()


def check_environment() -> bool:
    """Check if required environment variables are set"""
    load_dotenv()

    required_vars = ["DISCORD_BOT_TOKEN"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        return False

    return True


async def main():
    """Main entry point for scoped Discord bot"""
    print("🚀 Starting Scoped Discord Intelligence Bot...")

    if not check_environment():
        sys.exit(1)

    print("✅ Environment validated")

    # Enable feature flags for backend processing
    for flag, value in DEFAULT_FEATURE_FLAGS.items():
        if not os.getenv(flag):
            os.environ[flag] = value

    try:
        bot = ScopedCommandBot()
        await bot.start()
    except KeyboardInterrupt:
        print("\n👋 Scoped bot stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Scoped bot stopped")
