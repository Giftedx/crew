from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat.groupchat import GroupChat
from autogen.agentchat.manager import GroupChatManager

from ultimate_discord_intelligence_bot.step_result import StepResult

from ..step_result import StepResult


if TYPE_CHECKING:
    from collections.abc import Callable


# This is a conceptual implementation and will require a running Discord bot
# instance to be fully integrated.


class DiscordUserProxy(UserProxyAgent):
    """A UserProxyAgent that interacts with a user through Discord."""

    def __init__(self, name: str, get_input_func: Callable):
        super().__init__(name=name, human_input_mode="ALWAYS")
        self._get_input_func = get_input_func

    def get_human_input(self, prompt: str) -> StepResult:
        """Overrides the default get_human_input to use a Discord channel."""
        return asyncio.run(self._get_input_func(prompt))


class AutoGenDiscordService:
    """A service for managing interactive AutoGen chats in Discord."""

    def __init__(self, get_input_func: Callable, send_message_func: Callable):
        """
        Initializes the AutoGenDiscordService.

        Args:
            get_input_func: An async function to get input from a Discord user.
            send_message_func: An async function to send a message to a Discord channel.
        """
        self.get_input_func = get_input_func
        self.send_message_func = send_message_func
        self.llm_config = {"config_list": [{"model": "gpt-4o-mini"}]}

    async def run_interactive_analysis(self, initial_task: str) -> StepResult:
        """
        Runs an interactive analysis session with an AutoGen crew.

        Args:
            initial_task: The initial task or question from the user.

        Returns:
            A StepResult with the final result of the conversation.
        """
        try:
            # Define the agents
            user_proxy = DiscordUserProxy(name="user_proxy", get_input_func=self.get_input_func)

            analyst_agent = AssistantAgent(
                name="content_analyst",
                system_message="You are a world-class content analyst. Ask clarifying questions to refine the task. When you have enough information, provide a detailed analysis. End your final response with 'ANALYSIS COMPLETE'.",
                llm_config=self.llm_config,
            )

            # Create the group chat and manager
            groupchat = GroupChat(agents=[user_proxy, analyst_agent], messages=[], max_round=10)
            manager = GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)

            # Initiate the chat
            await user_proxy.a_initiate_chat(
                manager,
                message=initial_task,
            )

            # The final message from the analyst should be the result.
            final_message = groupchat.messages[-1]["content"]

            return StepResult.ok(data={"final_analysis": final_message})

        except Exception as e:
            return StepResult.fail(f"AutoGen interactive analysis failed: {e}")


# Example of how this would be integrated with a Discord bot
# This part would go into your Discord bot's command handling logic.


async def example_discord_command_handler(message, initial_task):
    """Example handler for a Discord command like `!analyze-interactive`."""

    # Define how to get input and send messages in the context of the Discord message
    async def get_input_from_discord(prompt: str) -> StepResult:
        await message.channel.send(f"🤖 **Analyst:** {prompt}")

        def check(m):
            return m.author == message.author and m.channel == message.channel

        try:
            # NOTE: `bot` should be an injected or module-level Discord client.
            # If not available in this environment, raise a clear error.
            try:
                response_message = await bot.wait_for("message", check=check, timeout=300.0)  # type: ignore[name-defined]
            except NameError as _e:
                raise RuntimeError("Discord bot client not available in this runtime") from _e
            return response_message.content
        except asyncio.TimeoutError:
            return "No response. Please try again."

    async def send_message_to_discord(text: str):
        await message.channel.send(text)

    # Create and run the service
    autogen_service = AutoGenDiscordService(
        get_input_func=get_input_from_discord, send_message_func=send_message_to_discord
    )

    result = await autogen_service.run_interactive_analysis(initial_task)

    if result.success:
        await message.channel.send("✅ **Interactive Analysis Complete!**")
    else:
        await message.channel.send(f"❌ **An error occurred:** {result.error}")


# Assume 'bot' is your discord.py bot instance
# @bot.command(name="analyze-interactive")
# async def analyze_interactive(ctx, *, task: str):
#     await example_discord_command_handler(ctx.message, task)
