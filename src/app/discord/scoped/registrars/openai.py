"""OpenAI integration commands for Discord bot."""

from __future__ import annotations

import io
import logging


try:
    import discord
except Exception:  # pragma: no cover
    discord = None  # type: ignore

from ultimate_discord_intelligence_bot.services.openai_cost_monitoring import OpenAICostMonitoringService
from ultimate_discord_intelligence_bot.services.openai_integration_service import OpenAIIntegrationService


logger = logging.getLogger(__name__)


def register_openai_commands(bot_owner) -> None:
    """Register OpenAI-specific Discord commands."""
    bot = bot_owner.bot
    if not bot or discord is None:
        return

    # Initialize OpenAI services
    openai_service = OpenAIIntegrationService()
    cost_monitor = OpenAICostMonitoringService()

    @bot.command(name="openai-analyze")
    async def openai_analyze(ctx, *, content: str):
        """Analyze content using OpenAI enhanced capabilities."""
        await ctx.send("🔍 Starting OpenAI-enhanced analysis...")

        try:
            # Get available enhancements
            enhancements = openai_service.get_available_enhancements()

            # Process with OpenAI enhancements
            result = await openai_service.process_with_enhancements(
                content=content,
                enhancements=enhancements,
                tenant=str(ctx.guild.id) if ctx.guild else "dm",
                workspace=str(ctx.channel.id),
                analysis_type="debate",
            )

            if result.success:
                analysis_data = result.data
                embed = discord.Embed(
                    title="🤖 OpenAI Enhanced Analysis",
                    description="**Advanced AI-powered content analysis**",
                    color=0x00A67E,
                )

                # Add structured analysis if available
                if "structured_analysis" in analysis_data.get("enhanced_analysis", {}):
                    structured = analysis_data["enhanced_analysis"]["structured_analysis"]
                    embed.add_field(
                        name="📊 Structured Analysis",
                        value=f"**Score:** {structured.get('score', 'N/A')}\n**Confidence:** {structured.get('confidence', 'N/A')}",
                        inline=True,
                    )

                # Add function calling results if available
                if "function_analysis" in analysis_data.get("enhanced_analysis", {}):
                    function = analysis_data["enhanced_analysis"]["function_analysis"]
                    embed.add_field(
                        name="🔧 Function Analysis",
                        value=f"**Tools Used:** {len(function.get('tools_used', []))}\n**Reliability:** {function.get('reliability', 'N/A')}",
                        inline=True,
                    )

                # Add enhancements used
                enhancements_used = analysis_data.get("enhancements_applied", [])
                embed.add_field(
                    name="⚡ Enhancements Applied",
                    value=", ".join(enhancements_used) if enhancements_used else "None",
                    inline=False,
                )

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Analysis failed: {result.error}")

        except Exception as e:
            logger.error(f"OpenAI analysis command failed: {e}")
            await ctx.send(f"❌ Analysis failed: {e!s}")

    @bot.command(name="openai-stream")
    async def openai_stream(ctx, *, content: str):
        """Stream OpenAI analysis results in real-time."""
        await ctx.send("🌊 Starting streaming analysis...")

        try:
            message = await ctx.send("🔄 Processing...")

            async for result in openai_service.stream_enhanced_analysis(
                content=content,
                analysis_type="debate",
                tenant=str(ctx.guild.id) if ctx.guild else "dm",
                workspace=str(ctx.channel.id),
            ):
                if result.success and result.data.get("streaming"):
                    # Update message with streaming content
                    content_preview = (
                        result.data["content"][:100] + "..."
                        if len(result.data["content"]) > 100
                        else result.data["content"]
                    )
                    await message.edit(content=f"🔄 **Streaming Analysis:**\n{content_preview}")
                elif result.success and result.data.get("complete"):
                    # Final result
                    embed = discord.Embed(
                        title="✅ Streaming Analysis Complete",
                        description=result.data.get("content", "Analysis completed"),
                        color=0x00A67E,
                    )
                    await message.edit(content="", embed=embed)
                    break
                elif not result.success:
                    await message.edit(content=f"❌ Streaming failed: {result.error}")
                    break

        except Exception as e:
            logger.error(f"OpenAI streaming command failed: {e}")
            await ctx.send(f"❌ Streaming failed: {e!s}")

    @bot.command(name="openai-voice")
    async def openai_voice(ctx, *, text: str):
        """Convert text to speech using OpenAI TTS."""
        await ctx.send("🎤 Converting text to speech...")

        try:
            result = await openai_service.voice.text_to_speech(
                text=text, voice="alloy", tenant=str(ctx.guild.id) if ctx.guild else "dm", workspace=str(ctx.channel.id)
            )

            if result.success:
                audio_data = result.data["audio_data"]
                # Send as file attachment
                file = discord.File(io.BytesIO(audio_data), filename="speech.mp3")
                await ctx.send("🔊 **Generated Speech:**", file=file)
            else:
                await ctx.send(f"❌ Voice generation failed: {result.error}")

        except Exception as e:
            logger.error(f"OpenAI voice command failed: {e}")
            await ctx.send(f"❌ Voice generation failed: {e!s}")

    @bot.command(name="openai-vision")
    async def openai_vision(ctx):
        """Analyze images using OpenAI vision capabilities."""
        if not ctx.message.attachments:
            await ctx.send("❌ Please attach an image to analyze.")
            return

        await ctx.send("👁️ Analyzing image with OpenAI vision...")

        try:
            # Get the first image attachment
            attachment = ctx.message.attachments[0]
            if not attachment.content_type or not attachment.content_type.startswith("image/"):
                await ctx.send("❌ Please attach a valid image file.")
                return

            # Download image data
            image_data = await attachment.read()

            result = await openai_service.vision.analyze_image(
                image_data=image_data,
                prompt="Analyze this image for debate content, bias indicators, and key visual elements.",
                tenant=str(ctx.guild.id) if ctx.guild else "dm",
                workspace=str(ctx.channel.id),
            )

            if result.success:
                analysis = result.data["analysis"]
                embed = discord.Embed(
                    title="👁️ Vision Analysis",
                    description=analysis[:1000] + "..." if len(analysis) > 1000 else analysis,
                    color=0x8B5CF6,
                )
                embed.set_image(url=attachment.url)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Vision analysis failed: {result.error}")

        except Exception as e:
            logger.error(f"OpenAI vision command failed: {e}")
            await ctx.send(f"❌ Vision analysis failed: {e!s}")

    @bot.command(name="openai-costs")
    async def openai_costs(ctx, timeframe: str = "today"):
        """Show OpenAI API usage and costs."""
        await ctx.send("💰 Fetching OpenAI cost information...")

        try:
            # Get current metrics
            metrics = cost_monitor.get_current_metrics()
            summary = cost_monitor.get_cost_summary()

            embed = discord.Embed(
                title="💰 OpenAI Cost Monitoring",
                description=f"**Usage and cost tracking for {timeframe}**",
                color=0xFFD700,
            )

            embed.add_field(
                name="📊 Current Usage",
                value=(
                    f"**Total Requests:** {metrics['total_requests']}\n"
                    f"**Total Tokens:** {metrics['total_tokens']:,}\n"
                    f"**Success Rate:** {metrics['success_rate']:.1%}"
                ),
                inline=True,
            )

            embed.add_field(
                name="💵 Cost Summary",
                value=(
                    f"**Total Cost:** ${metrics['total_cost']:.4f}\n"
                    f"**Avg per Request:** ${metrics['avg_cost_per_request']:.4f}\n"
                    f"**Projected Monthly:** ${summary['projected_monthly_cost']:.2f}"
                ),
                inline=True,
            )

            embed.add_field(
                name="⚡ Performance",
                value=(
                    f"**Avg Response Time:** {metrics['avg_response_time']:.2f}s\n"
                    f"**Peak Usage:** {metrics['peak_usage_hour']}\n"
                    f"**Error Rate:** {metrics['error_rate']:.1%}"
                ),
                inline=True,
            )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"OpenAI costs command failed: {e}")
            await ctx.send(f"❌ Cost monitoring failed: {e!s}")

    @bot.command(name="openai-health")
    async def openai_health(ctx):
        """Check health status of OpenAI services."""
        await ctx.send("🏥 Checking OpenAI service health...")

        try:
            result = await openai_service.health_check()

            if result.success:
                health_data = result.data
                embed = discord.Embed(
                    title="🏥 OpenAI Service Health",
                    description="**Service status and availability**",
                    color=0x00A67E if health_data.get("openai_available") else 0xDC3545,
                )

                # OpenAI availability
                status = "✅ Available" if health_data.get("openai_available") else "❌ Unavailable"
                embed.add_field(name="🔗 OpenAI API", value=status, inline=True)

                # Individual services
                services = health_data.get("services", {})
                service_status = "\n".join(
                    [
                        f"**{name.title()}:** {'✅' if status == 'healthy' else '❌'}"
                        for name, status in services.items()
                    ]
                )
                embed.add_field(name="🛠️ Services", value=service_status or "No services checked", inline=False)

                # Features enabled
                features = health_data.get("features_enabled", [])
                embed.add_field(
                    name="⚡ Features Enabled", value=", ".join(features) if features else "None", inline=False
                )

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Health check failed: {result.error}")

        except Exception as e:
            logger.error(f"OpenAI health command failed: {e}")
            await ctx.send(f"❌ Health check failed: {e!s}")

    @bot.command(name="openai-multimodal")
    async def openai_multimodal(ctx, *, content: str):
        """Analyze content with images using multimodal capabilities."""
        if not ctx.message.attachments:
            await ctx.send("❌ Please attach images for multimodal analysis.")
            return

        await ctx.send("🖼️ Starting multimodal analysis...")

        try:
            # Collect image data
            images = []
            for attachment in ctx.message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    image_data = await attachment.read()
                    images.append(image_data)

            if not images:
                await ctx.send("❌ No valid images found in attachments.")
                return

            result = await openai_service.multimodal.analyze_multimodal_content(
                text=content,
                images=images,
                audio_data=None,
                tenant=str(ctx.guild.id) if ctx.guild else "dm",
                workspace=str(ctx.channel.id),
            )

            if result.success:
                analysis_data = result.data
                embed = discord.Embed(
                    title="🖼️ Multimodal Analysis",
                    description="**Comprehensive analysis across text and images**",
                    color=0x8B5CF6,
                )

                analysis_text = analysis_data.get("multimodal_analysis", "")
                embed.add_field(
                    name="📝 Analysis",
                    value=analysis_text[:1000] + "..." if len(analysis_text) > 1000 else analysis_text,
                    inline=False,
                )

                modalities = analysis_data.get("modalities_analyzed", [])
                embed.add_field(name="🔍 Modalities Analyzed", value=", ".join(modalities), inline=True)

                embed.add_field(name="🤖 Model", value=analysis_data.get("model", "Unknown"), inline=True)

                # Add first image as thumbnail
                if ctx.message.attachments:
                    embed.set_thumbnail(url=ctx.message.attachments[0].url)

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Multimodal analysis failed: {result.error}")

        except Exception as e:
            logger.error(f"OpenAI multimodal command failed: {e}")
            await ctx.send(f"❌ Multimodal analysis failed: {e!s}")


__all__ = ["register_openai_commands"]
