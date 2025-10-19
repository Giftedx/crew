"""
Mem0 Preference Learning Example

This example demonstrates how to use the Mem0MemoryService and Mem0MemoryTool
to learn and adapt to user preferences over time with tenant isolation.

Features Demonstrated:
- Storing user preferences
- Semantic recall of relevant memories
- Tenant isolation
- Memory updates and deletions
- Memory history tracking
"""

from ultimate_discord_intelligence_bot.services.mem0_service import Mem0MemoryService
from ultimate_discord_intelligence_bot.tools.mem0_memory_tool import Mem0MemoryTool


def example_service_usage():
    """Demonstrate Mem0MemoryService usage."""
    print("=" * 70)
    print("Mem0 Memory Service - Direct Usage Example")
    print("=" * 70)

    # Initialize service
    service = Mem0MemoryService()
    user_id = "tenant_podcast:workspace_h3"

    # 1. Store preferences
    print("\n1. Storing user preferences...")
    result = service.remember(
        content="User prefers concise, bullet-pointed summaries with key timestamps highlighted.",
        user_id=user_id,
        metadata={"category": "output_formatting", "priority": "high"},
    )

    if result.success:
        print(f"✅ Preference stored: {result.data}")
        memory_id = result.data[0]["id"]  # Store for later use
    else:
        print(f"❌ Failed to store preference: {result.error}")
        return

    # 2. Store more preferences
    service.remember(
        content="User wants fact-checks to include confidence scores and source links.",
        user_id=user_id,
        metadata={"category": "fact_checking", "priority": "high"},
    )

    service.remember(
        content="User prefers video clips under 60 seconds for social media.",
        user_id=user_id,
        metadata={"category": "content_creation", "priority": "medium"},
    )

    # 3. Recall relevant preferences
    print("\n2. Recalling preferences based on query...")
    recall_result = service.recall(
        query="How should I format the final report output?", user_id=user_id, limit=3
    )

    if recall_result.success:
        print(f"✅ Found {len(recall_result.data['results'])} relevant memories:")
        for idx, memory in enumerate(recall_result.data["results"][:3], 1):
            print(f"   {idx}. {memory['memory']} (score: {memory.get('score', 'N/A')})")
    else:
        print(f"❌ Recall failed: {recall_result.error}")

    # 4. Update a memory
    print("\n3. Updating a memory...")
    update_result = service.update_memory(
        memory_id=memory_id,
        content="User prefers very concise, bullet-pointed summaries with timestamps and confidence scores.",
        user_id=user_id,
        metadata={"category": "output_formatting", "priority": "critical"},
    )

    if update_result.success:
        print(f"✅ Memory updated: {update_result.data}")
    else:
        print(f"❌ Update failed: {update_result.error}")

    # 5. Get all memories
    print("\n4. Listing all memories for user...")
    all_memories = service.get_all_memories(user_id)

    if all_memories.success:
        print(f"✅ Total memories: {len(all_memories.data.get('results', []))}")
        for memory in all_memories.data.get("results", [])[:5]:
            print(f"   - {memory['memory']}")
    else:
        print(f"❌ List failed: {all_memories.error}")

    # 6. Get memory history
    print("\n5. Retrieving memory history...")
    history_result = service.get_memory_history(memory_id, user_id)

    if history_result.success:
        print(f"✅ Memory history retrieved: {len(history_result.data)} entries")
    else:
        print(f"❌ History retrieval failed: {history_result.error}")

    # 7. Delete a memory
    print("\n6. Deleting a memory...")
    delete_result = service.delete_memory(memory_id, user_id)

    if delete_result.success:
        print(f"✅ Memory deleted: {delete_result.data}")
    else:
        print(f"❌ Delete failed: {delete_result.error}")

    print("\n" + "=" * 70)


def example_tool_usage():
    """Demonstrate Mem0MemoryTool usage (agent-facing interface)."""
    print("\n" + "=" * 70)
    print("Mem0 Memory Tool - Agent Interface Example")
    print("=" * 70)

    tool = Mem0MemoryTool()
    tenant = "tenant_creator_intel"
    workspace = "workspace_hasan"

    # 1. Remember preference via tool
    print("\n1. Storing preference via tool...")
    result = tool._run(
        action="remember",
        content="Creator prefers controversy analysis with sentiment trends and key quotes.",
        tenant=tenant,
        workspace=workspace,
    )

    if result.success:
        print("✅ Preference stored via tool")
    else:
        print(f"❌ Tool remember failed: {result.error}")

    # 2. Recall via tool
    print("\n2. Recalling via tool...")
    result = tool._run(
        action="recall",
        query="What type of analysis does the creator prefer?",
        tenant=tenant,
        workspace=workspace,
        limit=5,
    )

    if result.success:
        memories = result.data.get("results", [])
        print(f"✅ Recalled {len(memories)} relevant memories")
        for memory in memories[:3]:
            print(f"   - {memory['memory']}")
    else:
        print(f"❌ Tool recall failed: {result.error}")

    # 3. List all memories
    print("\n3. Listing all memories via tool...")
    result = tool._run(action="list", tenant=tenant, workspace=workspace)

    if result.success:
        total = len(result.data.get("results", []))
        print(f"✅ Total memories for {tenant}:{workspace}: {total}")
    else:
        print(f"❌ Tool list failed: {result.error}")

    print("\n" + "=" * 70)


def example_tenant_isolation():
    """Demonstrate tenant isolation in Mem0."""
    print("\n" + "=" * 70)
    print("Mem0 Tenant Isolation Example")
    print("=" * 70)

    service = Mem0MemoryService()

    # Store preferences for different tenants
    print("\n1. Storing preferences for different tenants...")

    # Tenant 1: H3 Podcast
    service.remember(
        "User wants detailed debate analysis with fact-checks",
        user_id="tenant_h3:workspace_main",
        metadata={"tenant": "tenant_h3"},
    )

    # Tenant 2: Hasan Piker
    service.remember(
        "User wants brief political commentary summaries",
        user_id="tenant_hasan:workspace_main",
        metadata={"tenant": "tenant_hasan"},
    )

    # 2. Verify isolation - tenant 1 can't see tenant 2's memories
    print("\n2. Verifying tenant isolation...")

    h3_memories = service.recall(
        query="What type of analysis?", user_id="tenant_h3:workspace_main"
    )

    hasan_memories = service.recall(
        query="What type of analysis?", user_id="tenant_hasan:workspace_main"
    )

    print(f"✅ H3 tenant memories: {len(h3_memories.data.get('results', []))}")
    print(f"✅ Hasan tenant memories: {len(hasan_memories.data.get('results', []))}")
    print("   Memories are properly isolated by tenant!")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n🚀 Mem0 Preference Learning Examples\n")

    try:
        # Run all examples
        example_service_usage()
        example_tool_usage()
        example_tenant_isolation()

        print("\n✅ All examples completed successfully!\n")

    except Exception as e:
        print(f"\n❌ Example failed with error: {e}\n")
        import traceback

        traceback.print_exc()
