from __future__ import annotations


try:
    import discord  # type: ignore
except Exception:  # pragma: no cover
    discord = None  # type: ignore


def register_dev_commands(bot_owner) -> None:
    bot = bot_owner.bot
    if not bot or discord is None:
        return

    @bot.command(name="dev-tools")
    async def dev_tools(ctx):
        tools_status = await bot_owner._get_tools_status()
        embed = discord.Embed(
            title="🔧 Development Tools",
            description="**Backend tool status and testing interface**",
            color=0x6C757D,
        )
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
            value=(
                "Use `!dev-test` commands for individual component testing\nNo direct tool access via Discord interface"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @bot.command(name="dev-agents")
    async def dev_agents(ctx):
        agents_status = await bot_owner._get_agents_status()
        embed = discord.Embed(
            title="🤖 Agent Status",
            description="**Analysis agent health and configuration**",
            color=0x28A745,
        )
        for category, agents in agents_status.items():
            status_icons = [
                "🟢" if a["status"] == "active" else ("🟡" if a["status"] == "degraded" else "🔴") for a in agents
            ]
            embed.add_field(
                name=f"👥 {category.title()}",
                value=f"Status: {' '.join(status_icons)}\nActive: {sum(1 for a in agents if a['status'] == 'active')}/{len(agents)}",
                inline=True,
            )
        await ctx.send(embed=embed)

    @bot.command(name="dev-test")
    async def dev_test(ctx, component: str, *params):
        if component not in ["timeline", "evidence", "framing", "analysis"]:
            await ctx.send("❌ Invalid component. Available: timeline, evidence, framing, analysis")
            return
        test_result = await bot_owner._run_component_test(component, list(params))
        embed = discord.Embed(
            title=f"🧪 Component Test: {component.title()}",
            description="**Development testing interface**",
            color=0x007BFF,
        )
        embed.add_field(
            name="📊 Test Results",
            value=(
                f"Status: {'✅ PASS' if test_result['passed'] else '❌ FAIL'}\n"
                f"Duration: {test_result['duration']}ms\n"
                f"Details: {test_result['details']}"
            ),
            inline=False,
        )
        if test_result.get("metrics"):
            metrics = test_result["metrics"]
            embed.add_field(
                name="📈 Performance Metrics",
                value=(
                    f"Response Time: {metrics['response_time']}ms\n"
                    f"Accuracy: {metrics['accuracy']:.1%}\n"
                    f"Throughput: {metrics['throughput']}/s"
                ),
                inline=False,
            )
        await ctx.send(embed=embed)


__all__ = ["register_dev_commands"]
