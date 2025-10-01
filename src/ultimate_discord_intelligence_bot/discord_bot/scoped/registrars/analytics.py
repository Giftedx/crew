from __future__ import annotations

try:
    import discord  # type: ignore
except Exception:  # pragma: no cover
    discord = None  # type: ignore


def register_analytics_commands(bot_owner) -> None:
    bot = bot_owner.bot
    if not bot or discord is None:
        return

    @bot.command(name="analytics-usage")
    async def analytics_usage(ctx, timeframe: str = "7d", filter_type: str | None = None):
        usage_data = await bot_owner._get_usage_analytics(timeframe, filter_type)
        embed = discord.Embed(
            title=f"📊 Usage Analytics ({timeframe})",
            description="**System utilization and command usage patterns**",
            color=0xFD7E14,
        )
        embed.add_field(
            name="💬 Command Usage",
            value=(
                f"Total Commands: {usage_data['total_commands']}\n"
                f"Unique Users: {usage_data['unique_users']}\n"
                f"Most Used: {usage_data['most_used_command']}"
            ),
            inline=True,
        )
        embed.add_field(
            name="🔍 Analysis Activity",
            value=(
                f"Timeline Requests: {usage_data['timeline_requests']}\n"
                f"Evidence Queries: {usage_data['evidence_queries']}\n"
                f"Subjects Tracked: {usage_data['subjects_tracked']}"
            ),
            inline=True,
        )
        embed.add_field(
            name="👥 Engagement",
            value=(
                f"Peak Hours: {usage_data['peak_hours']}\n"
                f"Avg Session: {usage_data['avg_session_duration']}\n"
                f"Return Rate: {usage_data['return_rate']:.1%}"
            ),
            inline=True,
        )
        await ctx.send(embed=embed)

    @bot.command(name="analytics-performance")
    async def analytics_performance(ctx, agent: str | None = None):
        perf_analytics = await bot_owner._get_performance_analytics(agent)
        subtitle = f" - {agent.title()}" if agent else ""
        embed = discord.Embed(
            title=f"📈 Performance Analytics{subtitle}",
            description="**Analysis pipeline performance metrics**",
            color=0x20C997,
        )
        embed.add_field(
            name="⚡ Processing Performance",
            value=(
                f"Avg Response Time: {perf_analytics['avg_response_time']}ms\n"
                f"Throughput: {perf_analytics['throughput']}/hour\n"
                f"Error Rate: {perf_analytics['error_rate']:.2%}"
            ),
            inline=True,
        )
        embed.add_field(
            name="🎯 Quality Metrics",
            value=(
                f"Timeline Accuracy: {perf_analytics['timeline_accuracy']:.1%}\n"
                f"Evidence Relevance: {perf_analytics['evidence_relevance']:.1%}\n"
                f"Framing Consistency: {perf_analytics['framing_consistency']:.1%}"
            ),
            inline=True,
        )
        if agent and agent in perf_analytics.get("agent_breakdown", {}):
            agent_data = perf_analytics["agent_breakdown"][agent]
            embed.add_field(
                name=f"🤖 {agent.title()} Details",
                value=(
                    f"Tasks Completed: {agent_data['tasks_completed']}\n"
                    f"Success Rate: {agent_data['success_rate']:.1%}\n"
                    f"Avg Quality Score: {agent_data['avg_quality']:.2f}"
                ),
                inline=False,
            )
        await ctx.send(embed=embed)

    @bot.command(name="analytics-errors")
    async def analytics_errors(ctx, component: str | None = None):
        error_data = await bot_owner._get_error_analytics(component)
        subtitle = f" - {component.title()}" if component else ""
        embed = discord.Embed(
            title=f"🚨 Error Analytics{subtitle}",
            description="**System error patterns and monitoring**",
            color=0xDC3545,
        )
        embed.add_field(
            name="📊 Error Summary",
            value=(
                f"Total Errors: {error_data['total_errors']}\n"
                f"Error Rate: {error_data['error_rate']:.2%}\n"
                f"Critical: {error_data['critical_errors']}"
            ),
            inline=True,
        )
        if error_data.get("common_errors"):
            common = "\n".join([f"• {err}: {count}" for err, count in error_data["common_errors"][:3]])
            embed.add_field(name="🔍 Common Issues", value=common, inline=True)
        if error_data.get("recent_incidents"):
            recent = "\n".join([f"• {inc}" for inc in error_data["recent_incidents"][:3]])
            embed.add_field(name="🕒 Recent Incidents", value=recent, inline=False)
        await ctx.send(embed=embed)


__all__ = ["register_analytics_commands"]
