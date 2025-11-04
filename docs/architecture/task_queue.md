# Task Queue Architecture

**Current Implementation** (verified November 3, 2025):

- **Task System**: Arq with Redis backend
- **Worker**: `src/tasks/worker.py`
- **Queue Service**: `src/tasks/queue_service.py`
- **Pipeline Integration**: Async video processing support

This document describes the asynchronous task queue system using Arq for background job processing.

## Overview

The task queue system provides asynchronous job processing capabilities, allowing long-running operations to be offloaded from the main application flow. This enables:

- Non-blocking video processing
- Batch content analysis
- Scheduled monitoring tasks
- Improved scalability and resource utilization

## Architecture

### Components

1. **Arq Worker** (`src/tasks/worker.py`)
   - Background worker process that executes jobs
   - Manages Redis connection pool
   - Handles graceful shutdown and job lifecycle

2. **Task Queue Service** (`src/tasks/queue_service.py`)
   - High-level API for job management
   - Methods: enqueue, get_status, cancel, retry
   - Redis-backed job storage

3. **Job Definitions** (`src/tasks/jobs.py`)
   - Background job functions
   - Video processing, batch analysis, scheduled monitoring
   - Returns structured results

4. **Pipeline Integration** (`src/tasks/pipeline_integration.py`)
   - Connects task queue with content pipeline
   - Enables async video processing
   - Status tracking and callbacks

### Job Lifecycle

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client    │────▶│     Redis    │────▶│  Arq Worker │
│ Application │     │   Job Queue  │     │  Execution   │
└─────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌──────────────┐
                    │  Job Status  │     │  Results DB  │
                    │   Storage    │     │              │
                    └──────────────┘     └──────────────┘
```

1. **Enqueue**: Application enqueues job with parameters
2. **Store**: Job stored in Redis with queued status
3. **Execute**: Worker picks up job and executes function
4. **Complete**: Results stored, status updated to complete
5. **Retrieve**: Client queries job status and results

## Configuration

### Environment Variables

```bash
# Redis Connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0

# Worker Settings
ARQ_MAX_JOBS=10              # Max concurrent jobs
ARQ_TIMEOUT=300               # Job timeout in seconds
ARQ_MAX_RETRIES=3             # Max retry attempts
ARQ_RETRY_DELAY=60            # Delay between retries
```

### Arq Settings

Defined in `src/tasks/arq_config.py`:

```python
ARQ_SETTINGS = {
    "redis_settings": {...},
    "max_jobs": 10,
    "timeout": 300,
    "retry_policy": {
        "max_retries": 3,
        "retry_delay": 60,
    },
}
```

## Usage

### Enqueue a Job

```python
from src.tasks.queue_service import TaskQueueService

queue = TaskQueueService()
await queue.initialize()

job_id = await queue.enqueue(
    "process_video_async",
    video_url="https://example.com/video",
    tenant="my_tenant",
    workspace="my_workspace"
)
```

### Check Job Status

```python
status = await queue.get_status(job_id)
print(f"Job {job_id}: {status['status']}")
print(f"Result: {status['result']}")
```

### Cancel a Job

```python
success = await queue.cancel(job_id)
```

### Retry a Failed Job

```python
new_job_id = await queue.retry(job_id)
```

## Job Types

### 1. Video Processing

Process video content asynchronously:

```python
async def process_video_async(ctx, video_url, tenant, workspace):
    # Download and process video
    # Returns results dictionary
```

### 2. Batch Analysis

Analyze multiple content items:

```python
async def batch_analysis_async(ctx, content_items, tenant, workspace):
    # Process multiple items
    # Returns batch results
```

### 3. Scheduled Monitoring

System health monitoring:

```python
async def scheduled_monitoring_async(ctx):
    # Check system health
    # Returns monitoring results
```

## Retry Policy

Jobs automatically retry on failure:

- **Max Retries**: 3 attempts
- **Retry Delay**: 60 seconds between attempts
- **Exponential Backoff**: Enabled for network errors
- **Manual Retry**: Available via `queue.retry(job_id)`

## Monitoring

### Worker Health

```python
stats = worker.get_worker_stats()
print(f"Status: {stats['status']}")
print(f"Max Jobs: {stats['max_jobs']}")
```

### Job Metrics

- Total jobs enqueued
- Successful completions
- Failed jobs count
- Average processing time
- Queue depth

## Deployment

### Docker Compose

```yaml
arq-worker:
  build:
    context: .
    dockerfile: Dockerfile
  command: python -m src.tasks.worker
  environment:
    - REDIS_HOST=redis
    - REDIS_PORT=6379
  depends_on:
    - redis
```

### Manual Deployment

```bash
# Start worker
python -m src.tasks.worker

# Run with custom settings
ARQ_MAX_JOBS=20 python -m src.tasks.worker
```

## Scaling Considerations

### Horizontal Scaling

Run multiple worker instances:

```bash
# Worker 1
ARQ_MAX_JOBS=10 python -m src.tasks.worker

# Worker 2
ARQ_MAX_JOBS=10 python -m src.tasks.worker
```

### Vertical Scaling

Increase worker capacity:

```bash
ARQ_MAX_JOBS=50 python -m src.tasks.worker
```

### Load Balancing

Redis automatically distributes jobs across workers based on capacity.

## Troubleshooting

### Worker Not Processing Jobs

- Check Redis connection
- Verify worker is running
- Check job queue depth
- Review worker logs

### Jobs Timing Out

- Increase `ARQ_TIMEOUT` setting
- Optimize job execution time
- Split large jobs into smaller tasks

### Redis Connection Issues

- Verify Redis is running
- Check network connectivity
- Validate credentials
- Test with redis-cli

## Best Practices

1. **Job Granularity**: Keep jobs focused and atomic
2. **Error Handling**: Always handle exceptions gracefully
3. **Resource Limits**: Set appropriate timeout values
4. **Monitoring**: Track job success/failure rates
5. **Idempotency**: Design jobs to be safely retried
6. **Logging**: Log all job activities for debugging
7. **Resource Cleanup**: Clean up resources in finally blocks

## See Also

- [Arq Documentation](https://arq-docs.helpmanual.io/)
- [Redis Documentation](https://redis.io/docs/)
- [Configuration Guide](../configuration.md)
