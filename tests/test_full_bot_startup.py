import importlib
import os


def test_full_bot_creation_attributes():
    os.environ["LIGHTWEIGHT_IMPORT"] = "1"
    mod = importlib.import_module("scripts.start_full_bot")
    # create_full_bot should be callable without awaiting (returns bot instance)
    bot = mod.create_full_bot()
    # Basic sanity checks
    assert hasattr(bot, "pipeline_tool")
    assert hasattr(bot, "youtube_tool")
    assert hasattr(bot, "analysis_tool")
    assert hasattr(bot, "vector_tool")
    assert hasattr(bot, "fact_check_tool")
    assert hasattr(bot, "fallacy_tool")
    assert hasattr(bot, "debate_tool")
    # Intents configured
    intents = bot.intents
    assert intents.message_content is True
    assert intents.guilds is True
