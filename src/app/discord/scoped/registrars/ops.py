from __future__ import annotations


try:
    import discord  # type: ignore
except Exception:  # pragma: no cover
    discord = None  # type: ignore


def register_ops_commands(bot_owner) -> None:
    bot = bot_owner.bot
    if not bot or discord is None:
        return

    @bot.command(name="ops-status")
    async def ops_status(ctx, *args):
        detailed = "--detailed" in args
        component = None
        for arg in args:
            if arg.startswith("--component="):
                component = arg.split("=", 1)[1]
        status_data = await bot_owner._collect_detailed_system_status(component)
        if detailed:
            embed = discord.Embed(
                title="🖥️ Detailed System Status",
                description="**Operational metrics and health indicators**",
                color=0x00FF00 if status_data["status"] == "healthy" else 0xFFFF00,
            )
            for section, metrics in status_data["sections"].items():
                metric_text = "\n".join([f"{k}: {v}" for k, v in metrics.items()])
                embed.add_field(name=f"📊 {section}", value=metric_text, inline=True)
        else:
            embed = discord.Embed(
                title="🖥️ System Status",
                description=f"Overall Status: **{status_data['status'].title()}**",
                color=0x00FF00 if status_data["status"] == "healthy" else 0xFFFF00,
            )
            embed.add_field(
                name="📈 Key Metrics",
                value=(
                    f"Uptime: {status_data['uptime']}\n"
                    f"Queue: {status_data['queue_size']} pending\n"
                    f"Last Process: {status_data['last_process']}"
                ),
                inline=False,
            )
        await ctx.send(embed=embed)

    @bot.command(name="ops-queue")
    async def ops_queue(ctx, *args):
        action = None
        priority = None
        for arg in args:
            if arg == "--clear":
                action = "clear"
            elif arg.startswith("--priority="):
                priority = arg.split("=", 1)[1]
        if action == "clear":
            result = await bot_owner._clear_processing_queue()
            await ctx.send(f"🗑️ Queue cleared: {result['cleared_items']} items removed")
            return
        queue_data = await bot_owner._get_queue_status(priority)
        embed = discord.Embed(
            title="📦 Processing Queue",
            description="**Content analysis pipeline queue**",
            color=0x3498DB,
        )
        embed.add_field(
            name="📊 Queue Stats",
            value=(
                f"Total Items: {queue_data['total']}\n"
                f"High Priority: {queue_data['high_priority']}\n"
                f"Processing: {queue_data['processing']}\n"
                f"Failed: {queue_data['failed']}"
            ),
            inline=True,
        )
        if queue_data.get("recent_items"):
            recent = "\n".join([f"• {item}" for item in queue_data["recent_items"][:5]])
            embed.add_field(name="📋 Recent Items", value=recent, inline=False)
        await ctx.send(embed=embed)

    @bot.command(name="ops-metrics")
    async def ops_metrics(ctx, timeframe: str = "24h"):
        metrics_data = await bot_owner._get_ops_metrics(timeframe)
        embed = discord.Embed(
            title=f"📊 Operations Metrics ({timeframe})",
            description="**System performance and utilization**",
            color=0x17A2B8,
        )
        embed.add_field(
            name="⚡ Processing",
            value=(
                f"Items Processed: {metrics_data['processed']}\n"
                f"Success Rate: {metrics_data['success_rate']:.1%}\n"
                f"Avg Time: {metrics_data['avg_processing_time']}s"
            ),
            inline=True,
        )
        embed.add_field(
            name="🎯 Quality",
            value=(
                f"Timeline Events: {metrics_data['timeline_events']}\n"
                f"Evidence Items: {metrics_data['evidence_items']}\n"
                f"Framing Accuracy: {metrics_data['framing_accuracy']:.1%}"
            ),
            inline=True,
        )
        embed.add_field(
            name="🔄 System Load",
            value=(
                f"CPU Usage: {metrics_data['cpu_usage']:.1%}\n"
                f"Memory Usage: {metrics_data['memory_usage']:.1%}\n"
                f"Queue Backlog: {metrics_data['queue_backlog']}"
            ),
            inline=True,
        )
        await ctx.send(embed=embed)


__all__ = ["register_ops_commands"]
