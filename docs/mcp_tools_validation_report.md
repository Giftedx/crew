# MCP Tools Validation Report

**Test Date:** 2025-10-18 03:14:29

## Summary

- **Total Tests:** 30
- **Successful:** 5
- **Failed:** 25
- **Success Rate:** 16.67%
- **Test Duration:** 0.79s

## Tool Registry

- **Namespaces:** 9
- **Total Tools:** 30

### obs
- **Module:** mcp_server.obs_server
- **Tools:** 3
- **Tool Names:** summarize_health, get_counters, recent_degradations

### http
- **Module:** mcp_server.http_server
- **Tools:** 2
- **Tool Names:** http_get, http_json_get

### ingest
- **Module:** mcp_server.ingest_server
- **Tools:** 4
- **Tool Names:** extract_metadata, list_channel_videos, fetch_transcript_local, summarize_subtitles

### kg
- **Module:** mcp_server.kg_server
- **Tools:** 3
- **Tool Names:** kg_query, kg_timeline, policy_keys

### router
- **Module:** mcp_server.routing_server
- **Tools:** 3
- **Tool Names:** estimate_cost, route_completion, choose_embedding_model

### multimodal
- **Module:** mcp_server.multimodal_server
- **Tools:** 6
- **Tool Names:** analyze_image, analyze_video, analyze_audio, analyze_content_auto, get_visual_sentiment, extract_content_themes

### memory
- **Module:** mcp_server.memory_server
- **Tools:** 3
- **Tool Names:** vs_search, vs_list_namespaces, vs_samples

### a2a
- **Module:** mcp_server.a2a_bridge_server
- **Tools:** 1
- **Tool Names:** a2a_call

### crewai
- **Module:** mcp_server.crewai_server
- **Tools:** 5
- **Tool Names:** list_available_crews, get_crew_status, execute_crew, get_agent_performance, abort_crew_execution

## Obs Tools

- **Tests:** 3
- **Successful:** 3
- **Failed:** 0

- **summarize_health:** ✅ Working
- **get_counters:** ✅ Working
- **recent_degradations:** ✅ Working

## Http Tools

- **Tests:** 2
- **Successful:** 2
- **Failed:** 0

- **http_get:** ✅ Working
- **http_json_get:** ✅ Working

## Ingest Tools

- **Tests:** 4
- **Successful:** 0
- **Failed:** 4

- **extract_metadata:** ❌ Failed: invalid_params: extract_metadata() got an unexpected keyword argument 'channel_id'
- **list_channel_videos:** ❌ Failed: invalid_params: list_channel_videos() got an unexpected keyword argument 'url'
- **fetch_transcript_local:** ❌ Failed: invalid_params: fetch_transcript_local() got an unexpected keyword argument 'url'
- **summarize_subtitles:** ❌ Failed: invalid_params: summarize_subtitles() got an unexpected keyword argument 'channel_id'

## Kg Tools

- **Tests:** 3
- **Successful:** 0
- **Failed:** 3

- **kg_query:** ❌ Failed: invalid_params: kg_query() got an unexpected keyword argument 'query'
- **kg_timeline:** ❌ Failed: invalid_params: kg_timeline() got an unexpected keyword argument 'query'
- **policy_keys:** ❌ Failed: invalid_params: policy_keys() got an unexpected keyword argument 'query'

## Router Tools

- **Tests:** 3
- **Successful:** 0
- **Failed:** 3

- **estimate_cost:** ❌ Failed: invalid_params: estimate_cost() got an unexpected keyword argument 'task_type'
- **route_completion:** ❌ Failed: invalid_params: route_completion() got an unexpected keyword argument 'task_type'
- **choose_embedding_model:** ❌ Failed: invalid_params: choose_embedding_model() got an unexpected keyword argument 'task_type'

## Multimodal Tools

- **Tests:** 6
- **Successful:** 0
- **Failed:** 6

- **analyze_image:** ❌ Failed: unknown_or_forbidden: multimodal.analyze_image
- **analyze_video:** ❌ Failed: unknown_or_forbidden: multimodal.analyze_video
- **analyze_audio:** ❌ Failed: unknown_or_forbidden: multimodal.analyze_audio
- **analyze_content_auto:** ❌ Failed: unknown_or_forbidden: multimodal.analyze_content_auto
- **get_visual_sentiment:** ❌ Failed: unknown_or_forbidden: multimodal.get_visual_sentiment
- **extract_content_themes:** ❌ Failed: unknown_or_forbidden: multimodal.extract_content_themes

## Memory Tools

- **Tests:** 3
- **Successful:** 0
- **Failed:** 3

- **vs_search:** ❌ Failed: unknown_or_forbidden: memory.vs_search
- **vs_list_namespaces:** ❌ Failed: unknown_or_forbidden: memory.vs_list_namespaces
- **vs_samples:** ❌ Failed: unknown_or_forbidden: memory.vs_samples

## A2A Tools

- **Tests:** 1
- **Successful:** 0
- **Failed:** 1

- **a2a_call:** ❌ Failed: invalid_params: a2a_call() got an unexpected keyword argument 'target_agent'

## Crewai Tools

- **Tests:** 5
- **Successful:** 0
- **Failed:** 5

- **list_available_crews:** ❌ Failed: unknown_or_forbidden: crewai.list_available_crews
- **get_crew_status:** ❌ Failed: unknown_or_forbidden: crewai.get_crew_status
- **execute_crew:** ❌ Failed: unknown_or_forbidden: crewai.execute_crew
- **get_agent_performance:** ❌ Failed: unknown_or_forbidden: crewai.get_agent_performance
- **abort_crew_execution:** ❌ Failed: unknown_or_forbidden: crewai.abort_crew_execution
