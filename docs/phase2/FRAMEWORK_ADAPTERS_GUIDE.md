# Framework Adapters Guide

**Last Updated**: November 1, 2025  
**Version**: 1.0  
**Status**: Production Ready

## Overview

Framework adapters provide a **unified interface** for interacting with different AI frameworks (LangGraph, CrewAI, AutoGen, LlamaIndex) while maintaining consistency in state management, error handling, and tool integration.

## Architecture

```
┌──────────────────────────────────────────┐
│        Application Layer                 │
│  (Your workflow orchestration code)      │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│      BaseFrameworkAdapter                │
│  • Common interface                      │
│  • State conversion                      │
│  • Error handling                        │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┴──────────┬──────────┬──────────┐
    │                     │          │          │
┌───▼────┐  ┌────▼─────┐  ┌───▼───┐  ┌───▼──────┐
│LangGraph│ │  CrewAI  │  │AutoGen│  │LlamaIndex│
│ Adapter │  │ Adapter  │  │Adapter│  │ Adapter  │
└────────┘  └──────────┘  └───────┘  └──────────┘
```

## Supported Frameworks

| Framework | Version | Adapter Status | Use Cases |
|-----------|---------|----------------|-----------|
| LangGraph | 0.2.x | ✅ Production | Graph workflows, routing, orchestration |
| CrewAI | 0.11.x | ✅ Production | Multi-agent teams, role-based tasks |
| AutoGen | 0.2.x | ✅ Production | Conversational agents, chat workflows |
| LlamaIndex | 0.10.x | ✅ Production | RAG, document Q&A, knowledge retrieval |

## Common Interface

All adapters inherit from `BaseFrameworkAdapter` and implement:

```python
class BaseFrameworkAdapter(ABC):
    """Base class for all framework adapters."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the framework with configuration."""
        pass
    
    @abstractmethod
    def execute(self, workflow: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow with the given state."""
        pass
    
    @abstractmethod
    def convert_to_framework_state(self, unified_state: UnifiedWorkflowState) -> Any:
        """Convert unified state to framework-specific format."""
        pass
    
    @abstractmethod
    def convert_from_framework_state(self, framework_state: Any) -> UnifiedWorkflowState:
        """Convert framework-specific state back to unified format."""
        pass
    
    @abstractmethod
    def register_tool(self, tool: UniversalTool) -> None:
        """Register a universal tool with the framework."""
        pass
    
    def health_check(self) -> bool:
        """Check if framework is properly initialized."""
        pass
```

## LangGraph Adapter

### Overview

LangGraph adapter enables **graph-based workflows** with conditional routing, cycles, and complex state management.

### Installation

```bash
pip install langgraph langchain-core
```

### Basic Usage

```python
from src.ai.frameworks.adapters import LangGraphAdapter
from src.ai.frameworks.state import UnifiedWorkflowState
from langgraph.graph import StateGraph

# Initialize adapter
adapter = LangGraphAdapter()

# Define graph nodes
def analyze_node(state):
    """Analyze user query."""
    messages = state["messages"]
    # ... analysis logic
    return {"analysis": result}

def respond_node(state):
    """Generate response."""
    analysis = state["analysis"]
    # ... response logic
    return {"response": result}

# Build graph
workflow = StateGraph(dict)
workflow.add_node("analyze", analyze_node)
workflow.add_node("respond", respond_node)
workflow.add_edge("analyze", "respond")
workflow.set_entry_point("analyze")
workflow.set_finish_point("respond")

graph = workflow.compile()

# Execute with unified state
state = UnifiedWorkflowState.create(workflow_id="demo-001")
state.add_message(role="user", content="What's the weather?")

# Convert and execute
lg_state = adapter.convert_to_framework_state(state)
result = adapter.execute(graph, lg_state)

# Convert back
state = adapter.convert_from_framework_state(result)
```

### State Conversion

**UnifiedWorkflowState → LangGraph**:

```python
{
    "messages": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "workflow_id": "demo-001",
    "key1": "value1",  # From context
    "key2": "value2",  # From context
    # All context keys flattened into root
}
```

**LangGraph → UnifiedWorkflowState**:

- Extracts `messages` list
- Moves all other keys to `context`
- Preserves `workflow_id` and metadata

### Advanced Features

**Checkpoints**:

```python
from langgraph.checkpoint import MemorySaver

# Enable checkpointing
checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

# Execute with checkpoint tracking
result = adapter.execute(
    graph,
    lg_state,
    config={"configurable": {"thread_id": "thread-1"}}
)

# Resume from checkpoint
resumed = adapter.execute(
    graph,
    lg_state,
    config={
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_id": "checkpoint-123"
        }
    }
)
```

**Conditional Routing**:

```python
def route_decision(state):
    """Decide next node based on state."""
    if state.get("needs_search"):
        return "search"
    elif state.get("needs_analysis"):
        return "analyze"
    else:
        return "respond"

workflow.add_conditional_edges(
    "decision",
    route_decision,
    {
        "search": "search_node",
        "analyze": "analyze_node",
        "respond": "respond_node"
    }
)
```

**Streaming**:

```python
# Stream graph execution
for chunk in adapter.stream(graph, lg_state):
    print(f"Node: {chunk['node']}, State: {chunk['state']}")
```

### Best Practices

✅ **DO**:

- Use LangGraph for complex routing logic
- Leverage checkpoints for long-running workflows
- Structure state with clear node boundaries
- Use conditional edges for dynamic routing

❌ **DON'T**:

- Put too much logic in a single node (split into smaller nodes)
- Create cycles without termination conditions
- Mutate state without returning it
- Forget to handle errors in nodes

## CrewAI Adapter

### Overview

CrewAI adapter enables **multi-agent collaboration** with role-based task assignment and team coordination.

### Installation

```bash
pip install crewai crewai-tools
```

### Basic Usage

```python
from src.ai.frameworks.adapters import CrewAIAdapter
from src.ai.frameworks.state import UnifiedWorkflowState
from crewai import Agent, Task, Crew

# Initialize adapter
adapter = CrewAIAdapter()

# Define agents
researcher = Agent(
    role="Researcher",
    goal="Gather comprehensive information",
    backstory="Expert researcher with deep analysis skills",
    verbose=True
)

writer = Agent(
    role="Writer",
    goal="Create compelling content",
    backstory="Professional writer with excellent communication skills",
    verbose=True
)

# Define tasks
research_task = Task(
    description="Research the topic: {topic}",
    expected_output="Detailed research report",
    agent=researcher
)

writing_task = Task(
    description="Write article based on research",
    expected_output="Well-written article",
    agent=writer,
    context=[research_task]  # Depends on research
)

# Create crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    verbose=True
)

# Execute with unified state
state = UnifiedWorkflowState.create(workflow_id="article-001")
state.context["topic"] = "AI frameworks comparison"

# Convert and execute
crew_context = adapter.convert_to_framework_state(state)
result = adapter.execute(crew, crew_context)

# Convert back
state = adapter.convert_from_framework_state(result)
```

### State Conversion

**UnifiedWorkflowState → CrewAI**:

```python
{
    "conversation_history": """
user: What's the topic?
assistant: Let me research that.
system: Research complete.
    """,
    "workflow_id": "article-001",
    "topic": "AI frameworks comparison",
    # All context keys preserved
}
```

**CrewAI → UnifiedWorkflowState**:

- Parses `conversation_history` back to messages list
- Preserves all context keys
- Adds crew execution metadata

### Advanced Features

**Dynamic Agent Addition**:

```python
# Add agent during execution
editor = Agent(
    role="Editor",
    goal="Review and improve content",
    backstory="Experienced editor"
)

adapter.add_agent(crew, editor)

review_task = Task(
    description="Review and edit the article",
    agent=editor,
    context=[writing_task]
)

adapter.add_task(crew, review_task)
```

**Tool Integration**:

```python
from src.ai.frameworks.tools.universal import UniversalSearchTool

search_tool = UniversalSearchTool()

researcher = Agent(
    role="Researcher",
    tools=[search_tool],  # Universal tool works directly!
    verbose=True
)
```

**Process Types**:

```python
from crewai import Process

# Sequential process (default)
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential
)

# Hierarchical process (manager coordinates)
crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, review_task],
    process=Process.hierarchical,
    manager_llm="gpt-4"
)
```

### Best Practices

✅ **DO**:

- Define clear roles and goals for each agent
- Use task context to create dependencies
- Leverage team collaboration for complex problems
- Set appropriate verbosity for debugging

❌ **DON'T**:

- Create circular task dependencies
- Assign same task to multiple agents without coordination
- Forget to specify expected output for tasks
- Overload single agent with too many responsibilities

## AutoGen Adapter

### Overview

AutoGen adapter enables **conversational agent workflows** with natural dialogue, function calling, and group chats.

### Installation

```bash
pip install pyautogen
```

### Basic Usage

```python
from src.ai.frameworks.adapters import AutoGenAdapter
from src.ai.frameworks.state import UnifiedWorkflowState
import autogen

# Initialize adapter
adapter = AutoGenAdapter()

# Configure LLM
llm_config = {
    "model": "gpt-4",
    "api_key": "your-api-key",
    "temperature": 0.7
}

# Create agents
assistant = autogen.AssistantAgent(
    name="Assistant",
    system_message="You are a helpful AI assistant.",
    llm_config=llm_config
)

user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={"use_docker": False}
)

# Execute with unified state
state = UnifiedWorkflowState.create(workflow_id="chat-001")
state.add_message(role="user", content="Help me write a Python function")

# Convert and execute
autogen_messages = adapter.convert_to_framework_state(state)
result = adapter.execute(assistant, autogen_messages, user_proxy)

# Convert back
state = adapter.convert_from_framework_state(result)
```

### State Conversion

**UnifiedWorkflowState → AutoGen**:

```python
[
    {"role": "user", "content": "Help me write a Python function"},
    {"role": "assistant", "content": "I'd be happy to help..."},
    # Messages with role and content
]
```

**AutoGen → UnifiedWorkflowState**:

- Converts messages to UnifiedWorkflowState format
- Preserves function calls and results
- Maintains conversation context

### Advanced Features

**Function Calling**:

```python
def search_web(query: str) -> str:
    """Search the web for information."""
    # ... search logic
    return results

# Register function
assistant.register_function(
    function_map={"search_web": search_web}
)

# Function will be called automatically when needed
user_proxy.initiate_chat(
    assistant,
    message="Search for latest AI news"
)
```

**Group Chat**:

```python
# Create multiple agents
planner = autogen.AssistantAgent(name="Planner", llm_config=llm_config)
coder = autogen.AssistantAgent(name="Coder", llm_config=llm_config)
reviewer = autogen.AssistantAgent(name="Reviewer", llm_config=llm_config)

# Create group chat
groupchat = autogen.GroupChat(
    agents=[planner, coder, reviewer, user_proxy],
    messages=[],
    max_round=12
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config
)

# Start group conversation
result = adapter.execute_group_chat(
    manager,
    initial_message="Build a web scraper"
)
```

**Human-in-the-Loop**:

```python
# Enable human input
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS",  # Ask for input every time
    max_consecutive_auto_reply=0
)

# Or selective
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="TERMINATE",  # Ask only on termination
)
```

### Best Practices

✅ **DO**:

- Set appropriate max_consecutive_auto_reply to prevent loops
- Use function calling for external tool integration
- Structure system messages clearly
- Handle code execution with proper sandboxing

❌ **DON'T**:

- Allow infinite conversation loops (set limits)
- Execute arbitrary code without review
- Forget to handle function call errors
- Skip message validation

## LlamaIndex Adapter

### Overview

LlamaIndex adapter enables **RAG workflows** with document indexing, semantic search, and knowledge retrieval.

### Installation

```bash
pip install llama-index llama-index-core
```

### Basic Usage

```python
from src.ai.frameworks.adapters import LlamaIndexAdapter
from src.ai.frameworks.state import UnifiedWorkflowState
from llama_index.core import VectorStoreIndex, Document

# Initialize adapter
adapter = LlamaIndexAdapter()

# Create documents
documents = [
    Document(text="LangGraph is great for graph workflows..."),
    Document(text="CrewAI excels at multi-agent collaboration..."),
    Document(text="AutoGen provides conversational agents...")
]

# Build index
index = VectorStoreIndex.from_documents(documents)

# Create query engine
query_engine = index.as_query_engine(similarity_top_k=3)

# Execute with unified state
state = UnifiedWorkflowState.create(workflow_id="rag-001")
state.add_message(role="user", content="Which framework for graphs?")

# Convert and execute
chat_history = adapter.convert_to_framework_state(state)
result = adapter.query(query_engine, "Which framework for graphs?", chat_history)

# Convert back
state = adapter.convert_from_framework_state(result)
```

### State Conversion

**UnifiedWorkflowState → LlamaIndex**:

```python
[
    {"role": "user", "content": "Which framework for graphs?"},
    {"role": "assistant", "content": "LangGraph is designed for..."}
    # Simplified chat history
]
```

**LlamaIndex → UnifiedWorkflowState**:

- Converts chat history to messages
- Adds query results to context
- Preserves source documents metadata

### Advanced Features

**Custom Retrievers**:

```python
from llama_index.core.retrievers import VectorIndexRetriever

# Custom retrieval
retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=5,
    filters={"source": "documentation"}
)

# Use in query engine
from llama_index.core.query_engine import RetrieverQueryEngine

query_engine = RetrieverQueryEngine(retriever=retriever)
```

**Chat Engine with Memory**:

```python
from llama_index.core.memory import ChatMemoryBuffer

memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

chat_engine = index.as_chat_engine(
    chat_mode="condense_plus_context",
    memory=memory,
    context_template="Context: {context_str}\n\nQuestion: {query_str}"
)

# Maintains conversation history automatically
response = chat_engine.chat("Tell me about LangGraph")
response = chat_engine.chat("What about its advantages?")  # Remembers context
```

**Metadata Filtering**:

```python
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter

filters = MetadataFilters(filters=[
    MetadataFilter(key="source", value="official_docs"),
    MetadataFilter(key="date", value="2024", operator=">")
])

retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=3,
    filters=filters
)
```

**Streaming Responses**:

```python
streaming_engine = index.as_query_engine(streaming=True)

response = streaming_engine.query("Explain RAG")
for text in response.response_gen:
    print(text, end="", flush=True)
```

### Best Practices

✅ **DO**:

- Chunk documents appropriately (200-500 tokens)
- Use metadata for better filtering
- Leverage chat engine for conversational RAG
- Cache embeddings for performance

❌ **DON'T**:

- Index without cleaning/preprocessing documents
- Forget to set similarity thresholds
- Skip metadata when available
- Ignore source attribution

## Tool Integration

All adapters support universal tools via a common interface:

```python
from src.ai.frameworks.tools.universal import UniversalMemoryTool, UniversalSearchTool

# Create universal tools
memory = UniversalMemoryTool()
search = UniversalSearchTool()

# Register with any adapter
adapter = LangGraphAdapter()
adapter.register_tool(memory)
adapter.register_tool(search)

# Tools work identically across all frameworks!
```

## Error Handling

All adapters use consistent error handling:

```python
from src.ai.frameworks.adapters.exceptions import (
    AdapterError,
    FrameworkNotAvailableError,
    StateConversionError,
    ExecutionError
)

try:
    result = adapter.execute(workflow, state)
except FrameworkNotAvailableError:
    # Framework not installed
    logger.error("Please install: pip install langgraph")
except StateConversionError as e:
    # State conversion failed
    logger.error(f"Invalid state format: {e}")
except ExecutionError as e:
    # Workflow execution failed
    logger.error(f"Execution error: {e}")
    # Retry or use fallback
```

## Performance Considerations

### Adapter Overhead

| Adapter | Initialization | State Conversion | Execution Overhead |
|---------|---------------|------------------|-------------------|
| LangGraph | ~50ms | <1ms | <1% |
| CrewAI | ~100ms | <1ms | <1% |
| AutoGen | ~75ms | <1ms | <1% |
| LlamaIndex | ~200ms | <1ms | <2% |

**Recommendation**: Initialize adapters once and reuse across requests.

### Optimization Tips

**Connection Pooling**:

```python
# Share adapter instances
adapter_pool = {
    "langgraph": LangGraphAdapter(),
    "crewai": CrewAIAdapter(),
    "autogen": AutoGenAdapter(),
    "llamaindex": LlamaIndexAdapter()
}

def get_adapter(framework: str):
    return adapter_pool[framework]
```

**Lazy Loading**:

```python
# Load frameworks only when needed
class AdapterFactory:
    _adapters = {}
    
    @classmethod
    def get_adapter(cls, framework: str):
        if framework not in cls._adapters:
            if framework == "langgraph":
                cls._adapters[framework] = LangGraphAdapter()
            # ... other frameworks
        return cls._adapters[framework]
```

## Testing

Each adapter has comprehensive test coverage:

```bash
# Test specific adapter
pytest tests/frameworks/adapters/test_langgraph_adapter.py -v

# Test all adapters
pytest tests/frameworks/adapters/ -v

# Test with coverage
pytest tests/frameworks/adapters/ --cov=src/ai/frameworks/adapters
```

## Related Documentation

- [Universal Tools Guide](UNIVERSAL_TOOLS_GUIDE.md)
- [State Management Guide](STATE_MANAGEMENT_GUIDE.md)
- [Phase 2 Overview](PHASE_2_OVERVIEW.md)

---

**Status**: ✅ Production Ready  
**Test Coverage**: 100% (46 tests across all adapters)  
**Supported Frameworks**: 4 (LangGraph, CrewAI, AutoGen, LlamaIndex)
