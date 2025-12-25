# Mixture-of-Experts Routing Research and Integration Guidelines

## 1. Literature Review: Large-Scale MoE Architectures

### Google Switch Transformer (Fedus et al., 2021)
- Introduced a sparse Mixture-of-Experts (MoE) model where only one or two experts are activated per token, enabling 1.6T parameter models with manageable compute cost.
- Demonstrated up to 4× speedups over dense baselines by combining Top-1 expert routing with aggressive model parallelism and expert capacity factors to prevent overload.
- Highlighted the importance of load-balancing losses (auxiliary losses) to avoid expert collapse and to maintain stable training when routing decisions are discrete.

### DeepSpeed MoE (Microsoft, 2022)
- Extended ZeRO inference/training optimizations to MoE, supporting Top-K gating (K ∈ {1, 2}) with efficient all-to-all communication primitives and token dropping for overloaded experts.
- Provided automatic tensor/data parallel partitioning, enabling scaling to thousands of GPUs while keeping activation memory linear in the number of active experts.
- Added adaptive capacity mechanisms (token priority queueing) and expert parallelism APIs, serving as a blueprint for production-grade MoE deployments with consistent throughput.

### Additional Research Insights
- **Task-Specific Expert Specialization**: Recent works (e.g., Primer, GLaM) show experts can specialize on linguistic or domain-specific patterns when routing signals include positional and token embedding features.
- **Stochastic vs. Deterministic Routing**: Techniques like Random Token Routing and Router Noise (from Switch Transformer ablations) improve exploration, while deterministic gates (Top-1) maximize latency predictability.
- **Training Stability**: Successful large MoE systems use auxiliary load-balancing losses, capacity factors in the 1.0–1.25 range, and token-level dropout during early training to avoid expert dominance.

## 2. Practical Routing Implementations and APIs

### AWS Bedrock Inference Profiles
- Bedrock’s **Provisioned Throughput** and **On-Demand** models allow routing between foundation models (Anthropic, Amazon, AI21) via unified endpoints; routing policies can leverage response metadata (latency, cost, quality).
- The Bedrock Runtime API (`InvokeModel`, `InvokeModelWithResponseStream`) supports specifying target model IDs per request, enabling controller services to implement budget-aware expert selection.

### OpenRouter Meta-Routing Layer
- OpenRouter aggregates multiple LLM providers with a consistent REST API (`POST /api/v1/chat/completions`), exposing routing metadata such as cost-per-token, latency statistics, and model capabilities for dynamic selection.
- Supports **priority queues** and **fallback routing**: clients can specify preferred models and fallbacks, letting OpenRouter handle failover when a provider degrades or hits rate limits.

### DeepSpeed-MII and Azure OpenAI Hybrid Patterns
- DeepSpeed’s Model Implementations for Inference (MII) provide deployable expert graphs with runtime routers that leverage Hugging Face Accelerate interfaces; these can be fronted by Azure API Management for multi-tenant routing.
- Combining Azure OpenAI with custom MoE endpoints allows a gateway to dispatch tasks based on content filters, region residency, and quality tiers, illustrating hybrid expert pools across managed and self-hosted models.

## 3. Dynamic Routing Strategies

| Strategy Dimension | Description | Implementation Considerations |
| --- | --- | --- |
| **Task Classification** | Classify inputs (topic, modality, risk level) via lightweight models or heuristics before routing to specialized experts. | Use embeddings or intent classifiers (e.g., `src/discord/reasoning/token_interpreter.py`) to determine whether to invoke reasoning-heavy vs. retrieval-heavy experts. |
| **Quality Bands** | Maintain tiers of experts (premium, baseline, fast) and choose based on expected answer quality. | Track historical quality metrics in observability dashboards (`reports/monitoring_dashboard_report.md`) to adjust routing thresholds. |
| **Budget Constraints** | Optimize for cost ceilings by routing to cheaper experts unless confidence falls below a threshold. | Utilize token accounting infrastructure (see `reports/performance_optimization_report.md`) to forecast spend per request and escalate to premium experts when necessary. |
| **Latency SLAs** | Route to low-latency experts for real-time interactions (Discord bots) and to slower, higher-quality experts for offline jobs. | Monitor Crew execution timings via telemetry (disable or tune using `docs/core/README.md` guidance) to backpressure routes that exceed SLA. |
| **Safety/Compliance** | Escalate sensitive content to moderated experts with auditing. | Leverage MCP gating in `src/discord/mcp_integration.py` to enforce additional checks before invoking high-risk experts. |

**Routing Control Loop Recommendations**
1. Collect per-expert metrics: success rate, quality score, average latency, token cost.
2. Define routing policies as weighted rules (priority order: safety → budget → quality → latency).
3. Implement A/B experiments to validate new routing policies using replay queues and offline evaluation (e.g., `tests/frameworks/state/test_framework_switching.py` for framework conversions).
4. Persist routing decisions and outcomes for continuous learning (future integration with reinforcement bandits or contextual multi-armed bandits).

## 4. Integration Guidelines for CrewAI Workflows

1. **Centralize Routing Decisions**
   - Create a routing service or module (e.g., `src/app/config/agent_factory.py`) that selects the appropriate expert/model before instantiating CrewAI agents.
   - Extend Crew definitions to include routing metadata (cost tier, latency budget) stored alongside agent configs (e.g., `src/app/config/tasks.yaml`).

2. **Augment CrewAI MCP Server**
   - Extend `src/mcp_server/crewai_server.py` with endpoints exposing routing suggestions and health checks per expert, enabling external controllers (FastMCP clients) to query available experts before execution.
   - Use the `CrewAIServer.execute_crew` path to inject routing context (selected expert ID, fallback list) into Crew input payloads.

3. **Incorporate Dynamic Policies at Runtime**
   - Update workflow managers (e.g., `src/ultimate_discord_intelligence_bot/agents/workflow_manager.py`) to call the routing service based on task descriptors, passing along classification signals (content type, urgency).
   - Utilize the Discord MCP integration (`src/discord/mcp_integration.py`) to enforce budget or safety checks before delegating to premium experts.

4. **Observability and Feedback**
   - Feed routing telemetry into existing monitoring dashboards (`reports/monitoring_dashboard_report.md`) to visualize expert utilization and SLA adherence.
   - Log token consumption and runtime metrics per expert to enhance performance tuning (`reports/performance_optimization_report.md`).

5. **Testing and Validation**
   - Extend the cross-framework tests (`tests/frameworks/test_cross_framework.py`) to include scenarios where CrewAI workflows switch experts mid-run, ensuring state persistence across expert boundaries.
   - Simulate degraded experts and verify fallback behavior by adding fixtures in `fixtures/` that mock provider downtime, validating the routing control loop.

## 5. Recommended Next Steps
- Prototype a routing policy engine module with pluggable strategies (rule-based, bandit, reinforcement learning) and integrate it into the CrewAI agent factory.
- Establish benchmark suites comparing dense vs. MoE expert selections using existing performance tests (`tests/load/test_unified_system_load.py`).
- Document operational runbooks for routing overrides (manual expert pinning, cost ceilings) in the repository’s operational guides.
