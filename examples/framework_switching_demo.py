"""Framework Switching Demo: Demonstrates state preservation across framework transitions.

This example shows how UnifiedWorkflowState enables seamless switching between
different AI frameworks (LangGraph, CrewAI, AutoGen, LlamaIndex) while preserving
conversation history, context, and checkpoints.

The workflow simulates a customer support scenario that transitions through multiple
frameworks, each handling a different aspect of the interaction.
"""

import asyncio
from datetime import datetime

from ai.frameworks.state import UnifiedWorkflowState
from ai.frameworks.state.persistence import MemoryBackend, SQLiteBackend


def print_separator(title: str) -> None:
    """Print a visual separator."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_state_summary(state: UnifiedWorkflowState, framework: str) -> None:
    """Print a summary of the current state."""
    print(f"Framework: {framework}")
    print(f"Workflow ID: {state.metadata.workflow_id}")
    print(f"Messages: {len(state.messages)}")
    print(f"Context Keys: {list(state.context.keys())}")
    print(f"Checkpoints: {len(state.checkpoints)}")
    print()


def simulate_langgraph_processing(state: UnifiedWorkflowState) -> UnifiedWorkflowState:
    """Simulate LangGraph processing: Initial customer query analysis.

    LangGraph excels at graph-based workflows with state management.
    Here we use it to analyze the initial customer query and extract intent.
    """
    print_separator("Stage 1: LangGraph - Query Analysis")

    # Convert to LangGraph format
    langgraph_state = state.to_langgraph_state()
    print("Converted to LangGraph state:")
    print(f"  State keys: {list(langgraph_state.keys())}")
    print(f"  Messages: {len(langgraph_state['messages'])}")

    # Simulate LangGraph processing
    print("\nSimulating LangGraph graph execution...")
    langgraph_state["analysis_complete"] = True
    langgraph_state["customer_sentiment"] = "frustrated"
    langgraph_state["urgency_level"] = "high"
    langgraph_state["intent"] = "refund_request"

    # Add assistant response
    langgraph_state["messages"].append(
        {
            "role": "assistant",
            "content": "I understand you're requesting a refund. Let me route this to our refund team.",
        }
    )

    print("LangGraph processing complete:")
    print(f"  Intent detected: {langgraph_state['intent']}")
    print(f"  Sentiment: {langgraph_state['customer_sentiment']}")
    print(f"  Urgency: {langgraph_state['urgency_level']}")

    # Convert back to unified state
    updated_state = UnifiedWorkflowState.from_langgraph_state(langgraph_state, workflow_id=state.metadata.workflow_id)

    # Create checkpoint after LangGraph processing
    checkpoint = updated_state.create_checkpoint(
        "post_langgraph_analysis", framework="langgraph", stage="analysis_complete"
    )
    print(f"\nCheckpoint created: {checkpoint.name} (ID: {checkpoint.id[:8]}...)")

    print_state_summary(updated_state, "LangGraph")
    return updated_state


def simulate_crewai_processing(state: UnifiedWorkflowState) -> UnifiedWorkflowState:
    """Simulate CrewAI processing: Team collaboration for refund decision.

    CrewAI excels at multi-agent collaboration. Here we simulate a team of agents
    (Refund Analyst, Policy Checker, Customer Success) working together.
    """
    print_separator("Stage 2: CrewAI - Team Collaboration")

    # Convert to CrewAI format
    crewai_context = state.to_crewai_context()
    print("Converted to CrewAI context:")
    print(f"  Context keys: {list(crewai_context.keys())}")
    print(f"  Conversation history length: {len(crewai_context.get('conversation_history', ''))}")

    # Simulate CrewAI crew execution
    print("\nSimulating CrewAI crew execution...")
    print("  Agent 1 (Refund Analyst): Checking refund eligibility...")
    print("  Agent 2 (Policy Checker): Reviewing company policy...")
    print("  Agent 3 (Customer Success): Evaluating customer relationship...")

    # Update context with crew results
    crewai_context["refund_eligible"] = True
    crewai_context["refund_amount"] = 299.99
    crewai_context["policy_exception"] = False
    crewai_context["customer_lifetime_value"] = 2500.00
    crewai_context["crew_decision"] = "approve_refund"

    # Add crew conversation to history
    crew_discussion = (
        "\n[Refund Analyst]: Customer is within 30-day return window. Eligible for refund."
        "\n[Policy Checker]: Standard refund policy applies. No exceptions needed."
        "\n[Customer Success]: High-value customer. Approve to maintain relationship."
        "\n[Crew Decision]: APPROVE refund of $299.99"
    )
    crewai_context["conversation_history"] += crew_discussion

    print("CrewAI crew decision:")
    print(f"  Decision: {crewai_context['crew_decision'].upper()}")
    print(f"  Refund amount: ${crewai_context['refund_amount']}")
    print(f"  Customer LTV: ${crewai_context['customer_lifetime_value']}")

    # Convert back to unified state
    updated_state = UnifiedWorkflowState.from_crewai_context(crewai_context, workflow_id=state.metadata.workflow_id)

    # Add system message about crew decision
    updated_state.add_message("system", f"CrewAI team approved refund: ${crewai_context['refund_amount']}")

    # Create checkpoint after CrewAI processing
    checkpoint = updated_state.create_checkpoint(
        "post_crewai_decision",
        framework="crewai",
        stage="team_decision_complete",
        decision=crewai_context["crew_decision"],
    )
    print(f"\nCheckpoint created: {checkpoint.name} (ID: {checkpoint.id[:8]}...)")

    print_state_summary(updated_state, "CrewAI")
    return updated_state


def simulate_autogen_processing(state: UnifiedWorkflowState) -> UnifiedWorkflowState:
    """Simulate AutoGen processing: Multi-turn conversation for refund processing.

    AutoGen excels at conversational AI with multi-agent debates. Here we simulate
    a back-and-forth conversation to finalize the refund details.
    """
    print_separator("Stage 3: AutoGen - Refund Processing Conversation")

    # Convert to AutoGen format
    autogen_messages = state.to_autogen_messages()
    print("Converted to AutoGen messages:")
    print(f"  Message count: {len(autogen_messages)}")
    print(f"  Message roles: {[m['role'] for m in autogen_messages[-5:]]}")

    # Simulate AutoGen conversation
    print("\nSimulating AutoGen multi-turn conversation...")

    # Turn 1: Request refund details
    autogen_messages.append(
        {
            "role": "assistant",
            "name": "RefundAgent",
            "content": "To process your refund of $299.99, I need to confirm a few details. What payment method was used?",
        }
    )

    # Turn 2: Customer response
    autogen_messages.append({"role": "user", "content": "I paid with my Visa ending in 4242."})

    # Turn 3: Process refund
    autogen_messages.append(
        {
            "role": "assistant",
            "name": "RefundAgent",
            "content": "Thank you. Processing refund of $299.99 to Visa ending in 4242...",
        }
    )

    # Turn 4: Confirmation
    autogen_messages.append(
        {"role": "system", "content": "Refund processed successfully. Transaction ID: TXN-20251101-8472"}
    )

    print("AutoGen conversation turns:")
    for i, msg in enumerate(autogen_messages[-4:], 1):
        role = msg.get("name", msg["role"]).title()
        content_preview = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
        print(f"  Turn {i} ({role}): {content_preview}")

    # Convert back to unified state
    updated_state = UnifiedWorkflowState.from_autogen_messages(
        autogen_messages,
        workflow_id=state.metadata.workflow_id,
        context=state.context,  # Preserve context from previous stages
    )

    # Update context with processing results
    updated_state.update_context(
        refund_processed=True,
        transaction_id="TXN-20251101-8472",
        payment_method="Visa-4242",
        processing_timestamp=datetime.now().isoformat(),
    )

    # Create checkpoint after AutoGen processing
    checkpoint = updated_state.create_checkpoint(
        "post_autogen_processing", framework="autogen", stage="refund_processed", transaction_id="TXN-20251101-8472"
    )
    print(f"\nCheckpoint created: {checkpoint.name} (ID: {checkpoint.id[:8]}...)")

    print_state_summary(updated_state, "AutoGen")
    return updated_state


def simulate_llamaindex_processing(state: UnifiedWorkflowState) -> UnifiedWorkflowState:
    """Simulate LlamaIndex processing: Knowledge retrieval for follow-up.

    LlamaIndex excels at RAG (Retrieval-Augmented Generation). Here we use it to
    retrieve relevant knowledge for customer follow-up recommendations.
    """
    print_separator("Stage 4: LlamaIndex - Knowledge Retrieval & Follow-up")

    # Convert to LlamaIndex format
    llamaindex_chat_history = state.to_llamaindex_chat_history()
    print("Converted to LlamaIndex chat history:")
    print(f"  Chat turns: {len(llamaindex_chat_history)}")

    # Simulate LlamaIndex RAG
    print("\nSimulating LlamaIndex knowledge retrieval...")
    print("  Querying knowledge base: 'customer retention after refund'")
    print("  Retrieved documents: 3 relevant articles")

    # Simulate retrieved knowledge
    knowledge_summary = (
        "Best practices for customer retention after refunds: "
        "(1) Offer 15% discount on next purchase, "
        "(2) Provide extended warranty on replacement items, "
        "(3) Assign dedicated customer success manager for 90 days."
    )

    # Add knowledge-enhanced response to chat history
    llamaindex_chat_history.append(
        {
            "role": "assistant",
            "content": (
                "Your refund has been processed. Based on our customer retention program, "
                "I'd like to offer you a 15% discount on your next purchase and assign you "
                "a dedicated customer success manager for the next 90 days. "
                "Would you be interested in these benefits?"
            ),
        }
    )

    print("LlamaIndex RAG results:")
    print("  Knowledge applied: Customer retention best practices")
    print("  Offer: 15% discount + dedicated CSM")

    # Convert back to unified state
    updated_state = UnifiedWorkflowState.from_llamaindex_chat_history(
        llamaindex_chat_history,
        workflow_id=state.metadata.workflow_id,
        context=state.context,  # Preserve all context
    )

    # Update context with follow-up details
    updated_state.update_context(
        retention_offer_made=True,
        discount_percentage=15,
        csm_assigned=True,
        knowledge_sources=["KB-1234", "KB-5678", "KB-9012"],
    )

    # Create final checkpoint
    checkpoint = updated_state.create_checkpoint(
        "workflow_complete", framework="llamaindex", stage="retention_offer_made", status="success"
    )
    print(f"\nCheckpoint created: {checkpoint.name} (ID: {checkpoint.id[:8]}...)")

    print_state_summary(updated_state, "LlamaIndex")
    return updated_state


async def demonstrate_persistence(state: UnifiedWorkflowState) -> None:
    """Demonstrate state persistence across backend types."""
    print_separator("Persistence Demo: Saving & Loading Across Backends")

    workflow_id = state.metadata.workflow_id

    # 1. Memory Backend
    print("1. MemoryBackend (in-memory storage):")
    memory_backend = MemoryBackend()
    await memory_backend.save(workflow_id, state.to_dict())
    loaded_memory = await memory_backend.load(workflow_id)
    print(f"   Saved and loaded {len(loaded_memory['messages'])} messages")
    print(f"   Context keys: {list(loaded_memory['context'].keys())[:5]}...")

    # 2. SQLite Backend
    print("\n2. SQLiteBackend (file-based persistence):")
    sqlite_backend = SQLiteBackend("/tmp/framework_demo.db")
    await sqlite_backend.save(workflow_id, state.to_dict())
    loaded_sqlite = await sqlite_backend.load(workflow_id)
    print("   Saved to: /tmp/framework_demo.db")
    print(f"   Loaded {len(loaded_sqlite['messages'])} messages")
    print(f"   Checkpoints: {len(loaded_sqlite['checkpoints'])}")
    sqlite_backend.close()

    # 3. Demonstrate persistence across process restart
    print("\n3. Simulating process restart...")
    print("   Closing backend...")
    sqlite_backend.close()

    print("   Creating new backend instance...")
    new_backend = SQLiteBackend("/tmp/framework_demo.db")
    reloaded_state = await new_backend.load(workflow_id)
    restored_state = UnifiedWorkflowState.from_dict(reloaded_state)

    print(f"   Successfully restored workflow: {restored_state.metadata.workflow_id}")
    print(f"   Messages preserved: {len(restored_state.messages)}")
    print(f"   Context preserved: {len(restored_state.context)} keys")
    print(f"   Checkpoints preserved: {len(restored_state.checkpoints)}")
    new_backend.close()


def print_final_summary(state: UnifiedWorkflowState) -> None:
    """Print a comprehensive final summary."""
    print_separator("Final Workflow Summary")

    print("Workflow Execution Complete!")
    print(f"Workflow ID: {state.metadata.workflow_id}")

    # Calculate runtime (created_at is already a datetime object)
    if isinstance(state.metadata.created_at, str):
        created_at = datetime.fromisoformat(state.metadata.created_at)
    else:
        created_at = state.metadata.created_at
    runtime = (datetime.now() - created_at).total_seconds()
    print(f"Total Runtime: {runtime:.2f}s")
    print()

    print("Message History:")
    for i, msg in enumerate(state.messages, 1):
        role = msg.role.value if hasattr(msg.role, "value") else msg.role
        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        print(f"  {i}. [{role.upper()}] {content_preview}")

    print(f"\nContext Summary ({len(state.context)} keys):")
    for key, value in list(state.context.items())[:10]:
        print(f"  - {key}: {value}")
    if len(state.context) > 10:
        print(f"  ... and {len(state.context) - 10} more keys")

    print(f"\nCheckpoint History ({len(state.checkpoints)} checkpoints):")
    for cp in state.checkpoints:
        framework = cp.metadata.get("framework", "unknown")
        stage = cp.metadata.get("stage", "unknown")
        print(f"  - {cp.name}: {framework} ({stage})")

    print("\nFramework Journey:")
    print("  1. LangGraph   → Query analysis & intent detection")
    print("  2. CrewAI      → Multi-agent team decision")
    print("  3. AutoGen     → Conversational refund processing")
    print("  4. LlamaIndex  → Knowledge-enhanced follow-up")

    print("\nKey Achievements:")
    print("  ✅ State preserved across 4 framework transitions")
    print("  ✅ Conversation history maintained (all messages intact)")
    print("  ✅ Context accumulated across all stages")
    print("  ✅ Checkpoints created at each transition")
    print("  ✅ Workflow resumable from any checkpoint")
    print("  ✅ Persistence demonstrated (Memory & SQLite)")


async def main() -> None:
    """Run the complete framework switching demonstration."""
    print_separator("Framework Switching Demo: Customer Support Workflow")

    print("This demo shows how UnifiedWorkflowState enables seamless transitions")
    print("between different AI frameworks while preserving all conversation state.")
    print("\nScenario: Customer refund request workflow")
    print("  - Stage 1: LangGraph analyzes customer intent")
    print("  - Stage 2: CrewAI team collaborates on decision")
    print("  - Stage 3: AutoGen processes refund conversation")
    print("  - Stage 4: LlamaIndex provides retention offer")
    print()

    # Initialize workflow
    state = UnifiedWorkflowState()
    print(f"Initialized workflow: {state.metadata.workflow_id}\n")

    # Add initial customer message
    state.add_message(
        "user",
        "I want a refund for my order #12345. The product didn't work as advertised "
        "and I'm really frustrated. I need this resolved ASAP!",
    )
    state.update_context(customer_id="CUST-9876", order_id="ORD-12345", order_date="2024-10-15", order_amount=299.99)

    # Stage 1: LangGraph
    state = simulate_langgraph_processing(state)

    # Stage 2: CrewAI
    state = simulate_crewai_processing(state)

    # Stage 3: AutoGen
    state = simulate_autogen_processing(state)

    # Stage 4: LlamaIndex
    state = simulate_llamaindex_processing(state)

    # Demonstrate persistence
    await demonstrate_persistence(state)

    # Final summary
    print_final_summary(state)

    print_separator("Demo Complete")
    print("Key Takeaways:")
    print("  1. UnifiedWorkflowState provides a single state representation")
    print("  2. Each framework sees state in its native format via converters")
    print("  3. State transitions are seamless and lossless")
    print("  4. Checkpoints enable workflow resumption at any stage")
    print("  5. Multiple persistence backends support different deployment needs")
    print()


if __name__ == "__main__":
    asyncio.run(main())
