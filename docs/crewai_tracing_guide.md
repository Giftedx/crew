# CrewAI Enterprise Tracing & Observability Guide

This guide explains how to set up and use enhanced tracing for your CrewAI implementation, providing similar capabilities to what you see in CrewAI Enterprise traces.

## Quick Start

### 1. Enable Local Tracing

The enhanced tracing is already configured in your environment. Key settings in `.env`:

```bash
CREWAI_ENABLE_TRACING=true      # Enable trace collection
CREWAI_SAVE_TRACES=true         # Save traces to local files
CREWAI_TRACES_DIR=crew_data/Logs/traces  # Where to store traces
ENABLE_CREW_STEP_VERBOSE=true   # Detailed console output
```

### 2. Run a CrewAI Task

When you run any CrewAI task, traces will be automatically captured:

```bash
# Run through your normal workflow
python -m ultimate_discord_intelligence_bot.setup_cli run crew

# Or trigger a specific pipeline
python scripts/start_full_bot.py
```

### 3. Analyze Traces

Use the trace analysis script to view execution details:

```bash
# Analyze the latest trace
./scripts/analyze_crew_traces.py

# Show detailed output for each step
./scripts/analyze_crew_traces.py --show-output

# Analyze a specific trace file
./scripts/analyze_crew_traces.py --trace-file crew_data/Logs/traces/crew_trace_20250927_143022.json
```

## Enterprise Integration (Optional)

### CrewAI Plus/Enterprise Setup

If you have access to CrewAI Plus or Enterprise, you can enable automatic trace uploading:

1. **Get your API credentials** from <https://app.crewai.com>
1. **Add to your `.env` file**:

   ```bash
   CREWAI_API_KEY=your-api-key-here
   CREWAI_PROJECT_ID=your-project-id-here
   ```

1. **Traces will automatically upload** to your CrewAI dashboard

### Benefits of Enterprise Integration

- **Web-based trace visualization** similar to the URL you shared
- **Team collaboration** on trace analysis
- **Historical trace storage** and comparison
- **Advanced analytics** and performance insights
- **Real-time monitoring** and alerts

## Understanding Trace Data

### Local Trace Files

Traces are saved as JSON files in `crew_data/Logs/traces/` with this structure:

```json
{
  "execution_id": "local_1727443822",
  "start_time": 1727443822.123,
  "current_time": 1727443845.456,
  "total_steps": 12,
  "steps": [
    {
      "step_number": 1,
      "timestamp": "2025-09-27T14:30:22.123Z",
      "agent_role": "Multi-Platform Content Acquisition Specialist", 
      "tool": "MultiPlatformDownloadTool",
      "step_type": "tool_execution",
      "status": "completed",
      "duration_from_start": 1.234,
      "raw_output_length": 156,
      "raw_output": "Successfully downloaded video..."
    }
  ]
}
```

### Key Trace Elements

- **execution_id**: Unique identifier for the trace
- **timestamps**: ISO format timestamps for precise timing
- **agent_role**: Which agent performed the step
- **tool**: Which tool was executed
- **step_type**: Type of operation (tool_execution, thinking, etc.)
- **status**: Step completion status
- **duration_from_start**: Cumulative timing
- **raw_output**: Actual step output (truncated if large)

## Trace Analysis Features

### Summary Dashboard

The analysis script provides:

```text
🚀 CREWAI EXECUTION TRACE ANALYSIS
================================================================================
📋 Execution ID: local_1727443822
⏱️  Total Duration: 23.3s
🔢 Total Steps: 12
🤖 Agents Involved: 4
🔧 Tools Used: 8

📊 EXECUTION OVERVIEW:
   Agents: Multi-Platform Content Acquisition Specialist, Advanced Transcription Engineer, ...
   Tools: MultiPlatformDownloadTool, AudioTranscriptionTool, ...
```

### Step-by-Step Analysis

Detailed execution flow:

```text
🔍 STEP-BY-STEP EXECUTION TRACE:
--------------------------------------------------------------------------------
Step  1 | 14:30:22 |     1.2s | ✅ Multi-Platform Content Acquisition Specialist
        | Tool: MultiPlatformDownloadTool
Step  2 | 14:30:25 |     4.5s | ✅ Advanced Transcription Engineer
        | Tool: AudioTranscriptionTool
```

### Performance Analysis

Identifies bottlenecks and patterns:

```text
📈 PERFORMANCE ANALYSIS:
----------------------------------------
🐌 Slowest Operations:
    12.3s - Advanced Transcription Engineer using AudioTranscriptionTool
     8.7s - Information Verification Director using FactCheckTool
     
🔧 Tool Performance Summary:
   MultiPlatformDownloadTool....   3 uses | avg:     2.1s | max:     4.2s
   AudioTranscriptionTool.......   1 uses | avg:    12.3s | max:    12.3s
```

## Troubleshooting

### Common Issues

**No traces found:**

- Check that `CREWAI_SAVE_TRACES=true` is set
- Verify the traces directory exists: `crew_data/Logs/traces/`
- Ensure you've run a CrewAI task recently

**Trace analysis script not found:**

- Make sure you're in the project root directory
- Verify the script exists at `scripts/analyze_crew_traces.py`
- If needed, make it executable:

  ```bash
  chmod +x scripts/analyze_crew_traces.py
  ```

**Enterprise traces not uploading:**

- Verify your `CREWAI_API_KEY` and `CREWAI_PROJECT_ID` are correct
- Check your internet connection
- Ensure you have proper permissions in the CrewAI project

### Debug Mode

Enable more detailed logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
export ENABLE_CREW_STEP_VERBOSE=true
```

## Advanced Configuration

### Custom Trace Directory

Change where traces are stored:

```bash
CREWAI_TRACES_DIR=/custom/path/to/traces
```

### Embedder Configuration

Customize the embedder used by CrewAI:

```bash
CREW_EMBEDDER_PROVIDER=openai
CREW_EMBEDDER_CONFIG_JSON='{"config": {"dimension": 1536, "model": "text-embedding-3-large"}}'
```

### Performance Tuning

Adjust CrewAI performance settings:

```bash
CREW_MAX_RPM=20              # Requests per minute limit
CREWAI_ENABLE_TRACING=true   # Enable/disable tracing
```

## Integration with Monitoring

### Structured Logs

The enhanced step logger creates structured logs that can be integrated with:

- **Grafana/Prometheus** for metrics visualization
- **ELK Stack** for log analysis
- **OpenTelemetry** for distributed tracing
- **Custom monitoring** solutions

### Metrics Export

Key metrics available for monitoring:

- Step execution times
- Agent utilization
- Tool performance
- Error rates
- Success rates

## Comparison to Enterprise Dashboard

| Feature | Local Implementation | CrewAI Enterprise |
|---------|---------------------|------------------|
| Trace Collection | ✅ JSON files | ✅ Cloud dashboard |
| Step Analysis | ✅ CLI tool | ✅ Web interface |
| Performance Metrics | ✅ Local analysis | ✅ Advanced analytics |
| Team Sharing | ❌ File-based | ✅ Web-based sharing |
| Historical Analysis | ✅ Local files | ✅ Cloud storage |
| Real-time Monitoring | ❌ Post-execution | ✅ Live dashboard |

## Next Steps

1. **Try the local tracing** with your existing CrewAI workflows
1. **Analyze traces** to identify performance bottlenecks
1. **Consider CrewAI Enterprise** for advanced features and team collaboration
1. **Integrate with monitoring** tools for production deployments

The enhanced tracing provides comprehensive visibility into your CrewAI executions, helping you optimize performance and debug issues effectively.
