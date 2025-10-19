# Performance Baseline Measurement Report
============================================================

## System Health

**Overall Status: UNHEALTHY**

- Qdrant: ❌ unhealthy - No module named 'src'
- Llm_Api: ❌ not_configured - No API key found
- Discord: ❌ not_configured - No bot token found

## Evaluation Performance

### Overall Metrics
- Average Quality: 1.000
- Total Cost: $0.0085
- Average Latency: 170.1ms
- Tasks Tested: 5

### Task-Specific Metrics
- **summarize**:
  - Quality: 1.000
  - Cost: $0.0020
  - Latency: 200.1ms
- **rag_qa**:
  - Quality: 1.000
  - Cost: $0.0010
  - Latency: 100.1ms
- **tool_tasks**:
  - Quality: 1.000
  - Cost: $0.0030
  - Latency: 300.1ms
- **classification**:
  - Quality: 1.000
  - Cost: $0.0010
  - Latency: 100.0ms
- **claimcheck**:
  - Quality: 1.000
  - Cost: $0.0015
  - Latency: 150.1ms

## Tool Performance

### Individual Tool Status
- **content_ingestion**: ❌ No module named 'ultimate_discord_intelligence_bot.tools.content_ingestion'
- **debate_analysis**: ❌ No module named 'ultimate_discord_intelligence_bot.tools.debate_analysis'
- **fact_checking**: ❌ No module named 'ultimate_discord_intelligence_bot.tools.fact_checking'
- **claim_verifier**: ❌ No module named 'ultimate_discord_intelligence_bot.tools.claim_verifier'

## Memory System Performance

### Individual System Status
- **Qdrant**: ❌ No module named 'src'
- **Embedding**: ❌ No module named 'src'

## Summary and Recommendations

⚠️ **Overall Status: ISSUES DETECTED**

The following issues were identified:
- System health issues detected

### Recommended Actions:
1. Address system health issues (Qdrant, API keys, etc.)
2. Fix tool initialization errors
3. Resolve memory system connectivity issues
4. Re-run baseline measurements after fixes