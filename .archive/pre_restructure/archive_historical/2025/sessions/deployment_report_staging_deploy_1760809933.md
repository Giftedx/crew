# Production Deployment Report

**Deployment ID:** deploy_1760809933
**Environment:** staging
**Deployment Date:** 2025-10-18 18:52:42

## Summary

- **Total Steps:** 32
- **Successful:** 9
- **Failed:** 23
- **Success Rate:** 28.12%
- **Deployment Duration:** 28.67s
- **Status:** PARTIAL

## Environment Validation

- **Steps:** 7
- **Successful:** 0
- **Failed:** 7

- **DISCORD_BOT_TOKEN:** ❌ Missing
- **OPENROUTER_API_KEY:** ❌ Missing
- **QDRANT_URL:** ❌ Missing
- **POSTGRES_URL:** ❌ Missing
- **REDIS_URL:** ❌ Missing
- **docker:** ❌ Not available
- **docker_compose:** ❌ Not available

## Application Build

- **Steps:** 3
- **Successful:** 0
- **Failed:** 3

- **install_dependencies:** ❌ Failed: [31mERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'[0m[31m
[0m
- **type_checking:** ❌ Failed:
- **run_tests:** ❌ Failed:

## Infrastructure Deployment

- **Steps:** 4
- **Successful:** 0
- **Failed:** 4

- **postgresql:** ❌ Failed:
- **redis:** ❌ Failed:
- **qdrant:** ❌ Failed:
- **minio:** ❌ Failed:

## Monitoring Deployment

- **Steps:** 3
- **Successful:** 0
- **Failed:** 3

- **prometheus:** ❌ Failed:
- **grafana:** ❌ Failed:
- **alertmanager:** ❌ Failed:

## Application Deployment

- **Steps:** 3
- **Successful:** 0
- **Failed:** 3

- **discord-bot:** ❌ Failed:
- **api-server:** ❌ Failed:
- **worker-processes:** ❌ Failed:

## Health Checks

- **Steps:** 7
- **Successful:** 7
- **Failed:** 0

- **application:** ✅ Healthy (0.00s)
- **prometheus:** ✅ Healthy (0.00s)
- **grafana:** ✅ Healthy (0.00s)
- **postgresql:** ✅ Healthy (0.00s)
- **redis:** ✅ Healthy (0.00s)
- **qdrant:** ✅ Healthy (0.00s)
- **minio:** ✅ Healthy (0.00s)

## Smoke Tests

- **Steps:** 5
- **Successful:** 2
- **Failed:** 3

- **service_integration:** ✅ Passed
- **end_to_end_workflow:** ✅ Passed
- **mcp_tools_validation:** ❌ Test script not found
- **oauth_managers:** ❌ Test script not found
- **memory_operations:** ❌ Test script not found
