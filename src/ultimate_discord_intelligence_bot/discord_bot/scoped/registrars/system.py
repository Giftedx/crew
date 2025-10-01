from __future__ import annotations

try:
    import discord  # type: ignore
except Exception:  # pragma: no cover
    discord = None  # type: ignore


def register_system_commands(bot_owner) -> None:
    bot = bot_owner.bot
    if not bot or discord is None:
        return

    @bot.tree.command(name="system-status", description="Comprehensive system health")
    async def system_status(interaction):
        await interaction.response.defer()
        status_data = await bot_owner._collect_system_status()
        embed = discord.Embed(
            title="🖥️ System Status",
            description="**Read-Only Intelligence System**",
            color=0x00FF00 if status_data["overall_health"] == "healthy" else 0xFFFF00,
        )
        embed.add_field(
            name="📊 System Health",
            value=(
                f"Status: {status_data['overall_health'].title()}\n"
                f"Uptime: {status_data['uptime']}\n"
                f"Last Analysis: {status_data['last_analysis']}"
            ),
            inline=False,
        )
        embed.add_field(
            name="📈 Processing Stats",
            value=(
                f"Analyses Today: {status_data['analyses_today']}\n"
                f"Active Timelines: {status_data['active_timelines']}\n"
                f"Evidence Channels: {status_data['evidence_channels']}"
            ),
            inline=True,
        )
        embed.add_field(
            name="🔄 Queue Status",
            value=(
                f"Pending Items: {status_data['queue_pending']}\nProcessing Rate: {status_data['processing_rate']}/hr"
            ),
            inline=True,
        )
        embed.set_footer(text="All analysis occurs off-platform • Presentation layer only")
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="system-tools", description="Available tools and capabilities")
    async def system_tools(interaction):
        await interaction.response.defer()
        capabilities = await bot_owner._get_capability_summary()
        embed = discord.Embed(
            title="🔧 System Capabilities",
            description="**Analysis capabilities available for timeline generation**",
            color=0x4B9CD3,
        )
        for domain, caps in capabilities.items():
            cap_list = "\n".join([f"• {cap}" for cap in caps])
            embed.add_field(name=f"📋 {domain.title()}", value=cap_list, inline=True)
        embed.add_field(
            name="ℹ️ Access Model",
            value=("Analysis occurs off-platform\nResults presented as timelines\nNo direct tool access via Discord"),
            inline=False,
        )
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="system-performance", description="Performance monitoring")
    async def system_performance(interaction, agent: str | None = None):
        await interaction.response.defer()
        perf_data = await bot_owner._get_performance_summary(agent)
        subtitle = f" - {agent.title()}" if agent else ""
        embed = discord.Embed(
            title="📊 Performance Overview",
            description=f"**Analysis Pipeline Performance**{subtitle}",
            color=0x9932CC,
        )
        embed.add_field(
            name="⚡ Processing Speed",
            value=(
                f"Avg Analysis Time: {perf_data['avg_analysis_time']}\n"
                f"Success Rate: {perf_data['success_rate']:.1%}\n"
                f"Throughput: {perf_data['throughput']}/hour"
            ),
            inline=True,
        )
        embed.add_field(
            name="📈 Quality Metrics",
            value=(
                f"Timeline Accuracy: {perf_data['timeline_accuracy']:.1%}\n"
                f"Evidence Quality: {perf_data['evidence_quality']:.1%}\n"
                f"Framing Consistency: {perf_data['framing_consistency']:.1%}"
            ),
            inline=True,
        )
        if agent and agent in perf_data.get("agent_specific", {}):
            agent_data = perf_data["agent_specific"][agent]
            embed.add_field(
                name=f"🎯 {agent.title()} Metrics",
                value=(
                    f"Utilization: {agent_data['utilization']:.1%}\n"
                    f"Accuracy: {agent_data['accuracy']:.1%}\n"
                    f"Response Time: {agent_data['response_time']}ms"
                ),
                inline=False,
            )
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="system-audit", description="Self-audit with capability mapping")
    async def system_audit(interaction):
        await interaction.response.defer(ephemeral=True)
        audit_results = await bot_owner._perform_system_audit()
        embed = discord.Embed(
            title="🔍 System Audit",
            description="**Capability and compliance assessment**",
            color=0x7D3C98,
        )
        embed.add_field(
            name="✅ Available Capabilities",
            value=(
                f"Content Analysis: {audit_results['content_analysis']}\n"
                f"Timeline Generation: {audit_results['timeline_generation']}\n"
                f"Evidence Consolidation: {audit_results['evidence_consolidation']}\n"
                f"Analytical Framing: {audit_results['analytical_framing']}"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛡️ Compliance Status",
            value=(
                f"Read-Only Mode: {audit_results['read_only_mode']}\n"
                f"Off-Platform Analysis: {audit_results['off_platform_analysis']}\n"
                f"No Direct Tool Exposure: {audit_results['no_tool_exposure']}"
            ),
            inline=False,
        )
        if audit_results.get("recommendations"):
            recommendations = "\n".join([f"• {rec}" for rec in audit_results["recommendations"][:3]])
            embed.add_field(name="💡 Recommendations", value=recommendations, inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)


__all__ = ["register_system_commands"]
