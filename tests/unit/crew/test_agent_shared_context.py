from ultimate_discord_intelligence_bot.tenancy.shared_context import (
    AgentMessage,
    current_shared_context,
    with_shared_context,
)


def test_shared_context_publish_and_history():
    ctx = with_shared_context("session_test")
    assert current_shared_context() is ctx
    ctx.publish(AgentMessage(type="note", content="hello"))
    ctx.publish(AgentMessage(type="warning", content="careful"))

    all_msgs = ctx.history()
    assert len(all_msgs) == 2
    types = [m.type for m in all_msgs]
    assert set(types) == {"note", "warning"}

    notes = ctx.history("note")
    assert len(notes) == 1
    assert notes[0].content == "hello"
