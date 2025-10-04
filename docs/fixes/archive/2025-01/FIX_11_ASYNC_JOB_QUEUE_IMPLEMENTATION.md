# Fix #11: Async Job Queue for Pipeline API - Implementation Plan

**Date:** 2025-01-03  
**Priority:** MEDIUM  
**Status:** IN PROGRESS  
**Estimated Effort:** ~250 lines

---

## Problem Statement

**Current Limitation:**
The `/pipeline/run` endpoint executes the content pipeline synchronously, which causes:

1. **HTTP Timeout Risk:** Expensive analyses (comprehensive/experimental depth) can exceed typical HTTP timeouts (30-60s)
2. **No Concurrent Processing:** Users must wait for one job to complete before starting another
3. **No Status Visibility:** Once a request is made, there's no way to check progress
4. **Poor UX:** Long-running tasks block the HTTP connection

**Evidence from Codebase:**

```python
# src/server/routes/pipeline_api.py:59-62
with with_tenant(ctx):
    result: StepResult = await tool._run_async(url.strip(), resolved_quality or "1080p")
# Blocks until complete - can take minutes for comprehensive analysis
```

---

## Solution Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 Client (HTTP Request)                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│           POST /pipeline/jobs (NEW ENDPOINT)                 │
│  - Validates input                                           │
│  - Creates job ID                                            │
│  - Enqueues job                                              │
│  - Returns: {"job_id": "...", "status": "queued"}           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   In-Memory Job Queue                        │
│  jobs: dict[str, Job]                                        │
│  - job_id → Job(status, result, error, created_at, ...)    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Background Task Executor                        │
│  asyncio.create_task(execute_job(...))                      │
│  - Runs PipelineTool in background                          │
│  - Updates job status: queued → running → completed/failed  │
│  - Stores result or error                                   │
└─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│          GET /pipeline/jobs/{job_id} (NEW)                   │
│  - Returns job status and result (if complete)              │
│  - DELETE /pipeline/jobs/{job_id} to cancel/remove          │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

```python
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

class JobStatus(str, Enum):
    QUEUED = "queued"       # Job created, waiting to start
    RUNNING = "running"     # Job is executing
    COMPLETED = "completed" # Job finished successfully
    FAILED = "failed"       # Job encountered error
    CANCELLED = "cancelled" # Job was cancelled by user

@dataclass
class Job:
    job_id: str
    status: JobStatus
    url: str
    quality: str
    tenant_id: str
    workspace_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    progress: float = 0.0  # 0-100 percentage
```

---

## Implementation Steps

### Step 1: Create Job Queue Module (~100 lines)

**File:** `src/server/job_queue.py` (NEW)

**Components:**

1. **JobStatus enum** - 5 states (queued, running, completed, failed, cancelled)
2. **Job dataclass** - Full job metadata + result storage
3. **JobQueue class** - In-memory job storage with thread-safe operations
   - `create_job()` - Generate ID, store job, return job_id
   - `get_job()` - Retrieve job by ID
   - `update_status()` - Transition job state
   - `delete_job()` - Remove completed/failed jobs
   - `list_jobs()` - Get all jobs (optionally filtered by status/tenant)

**Features:**

- Thread-safe operations (asyncio.Lock)
- Automatic job expiry (configurable TTL for completed jobs)
- Tenant isolation (filter jobs by tenant_id)
- Progress tracking (0-100%)

### Step 2: Extend Pipeline API Routes (~100 lines)

**File:** `src/server/routes/pipeline_api.py` (MODIFY)

**New Endpoints:**

1. **POST /pipeline/jobs**

   ```python
   async def _create_pipeline_job(payload: dict[str, Any]) -> JSONResponse:
       # Validate input (url, quality, tenant_id, workspace_id)
       # Create job in queue
       # Start background task: asyncio.create_task(_execute_job(job_id))
       # Return: {"job_id": "...", "status": "queued", "created_at": "..."}
   ```

2. **GET /pipeline/jobs/{job_id}**

   ```python
   async def _get_pipeline_job(job_id: str) -> JSONResponse:
       # Retrieve job from queue
       # Return: {"job_id": "...", "status": "...", "result": {...}, "progress": 50}
       # 404 if not found
   ```

3. **DELETE /pipeline/jobs/{job_id}**

   ```python
   async def _delete_pipeline_job(job_id: str) -> JSONResponse:
       # Cancel job if running (set status=cancelled)
       # Remove job from queue
       # Return: {"job_id": "...", "status": "cancelled"}
   ```

4. **GET /pipeline/jobs**

   ```python
   async def _list_pipeline_jobs(
       tenant_id: str | None = None,
       status: str | None = None
   ) -> JSONResponse:
       # List jobs (optionally filtered)
       # Return: {"jobs": [...], "count": 5}
   ```

**Background Executor:**

```python
async def _execute_job(job_id: str, queue: JobQueue, tool: PipelineTool) -> None:
    """Execute pipeline job in background."""
    job = queue.get_job(job_id)
    if not job:
        return
    
    try:
        # Update status to running
        queue.update_status(job_id, JobStatus.RUNNING, started_at=datetime.utcnow())
        
        # Execute pipeline
        ctx = TenantContext(tenant_id=job.tenant_id, workspace_id=job.workspace_id)
        with with_tenant(ctx):
            result: StepResult = await tool._run_async(job.url, job.quality)
        
        # Update with result
        queue.update_status(
            job_id, 
            JobStatus.COMPLETED,
            result=result.to_dict(),
            completed_at=datetime.utcnow()
        )
    
    except Exception as exc:
        # Update with error
        queue.update_status(
            job_id,
            JobStatus.FAILED,
            error=str(exc),
            completed_at=datetime.utcnow()
        )
```

### Step 3: Add Feature Flag (~5 lines)

**File:** `src/core/settings.py` (MODIFY)

```python
# Add to Settings class
enable_pipeline_job_queue: bool = Field(False, alias="ENABLE_PIPELINE_JOB_QUEUE")
```

### Step 4: Update App Registration (~10 lines)

**File:** `src/server/routes/pipeline_api.py` (MODIFY)

```python
def register_pipeline_routes(app: FastAPI, settings: Any) -> None:
    # Existing /pipeline/run endpoint (keep for backward compatibility)
    
    # NEW: Check ENABLE_PIPELINE_JOB_QUEUE flag
    try:
        job_queue_enabled = bool(getattr(settings, "enable_pipeline_job_queue"))
    except Exception:
        job_queue_enabled = False
    
    if job_queue_enabled:
        # Initialize job queue (singleton)
        from server.job_queue import JobQueue
        queue = JobQueue()
        
        # Register async endpoints
        # POST /pipeline/jobs
        # GET /pipeline/jobs/{job_id}
        # DELETE /pipeline/jobs/{job_id}
        # GET /pipeline/jobs
```

### Step 5: Add Cleanup & Monitoring (~35 lines)

**Background Tasks:**

1. **Job Expiry Task** (runs every 5 minutes)

   ```python
   async def _cleanup_expired_jobs(queue: JobQueue, ttl_seconds: int = 3600):
       """Remove completed/failed jobs older than TTL."""
       while True:
           await asyncio.sleep(300)  # 5 minutes
           queue.cleanup_expired_jobs(ttl_seconds)
   ```

2. **Metrics Emission**

   ```python
   # In JobQueue class methods
   from obs.metrics import get_metrics
   
   get_metrics().counter("pipeline_jobs_created_total", labels={"tenant": tenant_id})
   get_metrics().counter("pipeline_jobs_completed_total", labels={"status": status})
   get_metrics().histogram("pipeline_job_duration_seconds", duration)
   ```

---

## API Examples

### Create Job (Async)

**Request:**

```bash
curl -X POST http://localhost:8000/pipeline/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=...",
    "quality": "1080p",
    "tenant_id": "acme",
    "workspace_id": "main"
  }'
```

**Response:**

```json
{
  "job_id": "job_1704326400_abc123",
  "status": "queued",
  "created_at": "2025-01-03T12:00:00Z",
  "url": "https://youtube.com/watch?v=..."
}
```

### Check Job Status

**Request:**

```bash
curl http://localhost:8000/pipeline/jobs/job_1704326400_abc123
```

**Response (Running):**

```json
{
  "job_id": "job_1704326400_abc123",
  "status": "running",
  "progress": 45.0,
  "created_at": "2025-01-03T12:00:00Z",
  "started_at": "2025-01-03T12:00:01Z",
  "url": "https://youtube.com/watch?v=..."
}
```

**Response (Completed):**

```json
{
  "job_id": "job_1704326400_abc123",
  "status": "completed",
  "progress": 100.0,
  "created_at": "2025-01-03T12:00:00Z",
  "started_at": "2025-01-03T12:00:01Z",
  "completed_at": "2025-01-03T12:03:45Z",
  "result": {
    "success": true,
    "data": {
      "transcript": "...",
      "summary": "...",
      "drive_url": "..."
    }
  }
}
```

### List All Jobs

**Request:**

```bash
curl http://localhost:8000/pipeline/jobs?tenant_id=acme&status=running
```

**Response:**

```json
{
  "jobs": [
    {
      "job_id": "job_1704326400_abc123",
      "status": "running",
      "progress": 45.0,
      "url": "https://youtube.com/watch?v=...",
      "created_at": "2025-01-03T12:00:00Z"
    }
  ],
  "count": 1
}
```

### Cancel Job

**Request:**

```bash
curl -X DELETE http://localhost:8000/pipeline/jobs/job_1704326400_abc123
```

**Response:**

```json
{
  "job_id": "job_1704326400_abc123",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

---

## Configuration

**Environment Variables:**

```bash
# Enable async job queue
export ENABLE_PIPELINE_JOB_QUEUE=1

# Optional: Job TTL (default 3600 seconds = 1 hour)
export PIPELINE_JOB_TTL=7200

# Optional: Max concurrent jobs (default 5)
export PIPELINE_MAX_CONCURRENT_JOBS=10
```

---

## Benefits

1. **No HTTP Timeouts:** Jobs execute in background, client gets immediate response
2. **Progress Visibility:** Clients can poll job status to track progress
3. **Concurrent Processing:** Multiple analyses can run simultaneously (up to max_concurrent_jobs)
4. **Better UX:** Users aren't blocked waiting for long analyses
5. **Resilience:** Failed jobs don't crash the HTTP connection
6. **Tenant Isolation:** Jobs are scoped to tenant_id for multi-tenancy

---

## Migration Path

**Backward Compatibility:**

- Keep existing `/pipeline/run` endpoint (synchronous)
- Add new `/pipeline/jobs` endpoints (asynchronous)
- Users can choose based on use case:
  - Quick analyses: Use `/pipeline/run` (immediate result)
  - Expensive analyses: Use `/pipeline/jobs` (background processing)

**Deprecation Plan (Future):**

1. Add deprecation warning to `/pipeline/run` response headers
2. Update documentation to recommend `/pipeline/jobs`
3. Eventually remove `/pipeline/run` in major version bump

---

## Testing Strategy

### Unit Tests

```python
# tests/test_job_queue.py
def test_create_job():
    queue = JobQueue()
    job_id = queue.create_job(url="https://...", quality="1080p", ...)
    assert job_id.startswith("job_")
    
def test_job_status_transitions():
    queue = JobQueue()
    job_id = queue.create_job(...)
    queue.update_status(job_id, JobStatus.RUNNING)
    assert queue.get_job(job_id).status == JobStatus.RUNNING
    
def test_job_expiry():
    queue = JobQueue()
    job_id = queue.create_job(...)
    queue.update_status(job_id, JobStatus.COMPLETED)
    queue.cleanup_expired_jobs(ttl_seconds=0)  # Immediate expiry
    assert queue.get_job(job_id) is None
```

### Integration Tests

```python
# tests/test_pipeline_api_async.py
async def test_create_and_poll_job():
    # Create job
    response = await client.post("/pipeline/jobs", json={"url": "..."})
    assert response.status_code == 201
    job_id = response.json()["job_id"]
    
    # Poll until complete
    while True:
        response = await client.get(f"/pipeline/jobs/{job_id}")
        status = response.json()["status"]
        if status in ["completed", "failed"]:
            break
        await asyncio.sleep(1)
    
    # Verify result
    assert response.json()["result"]["success"] is True
```

---

## Metrics & Monitoring

**Key Metrics:**

- `pipeline_jobs_created_total{tenant, status}` - Job creation rate
- `pipeline_jobs_completed_total{tenant, status}` - Job completion rate by status
- `pipeline_job_duration_seconds{tenant}` - Job execution time distribution
- `pipeline_jobs_active{tenant}` - Current running jobs
- `pipeline_jobs_queued{tenant}` - Jobs waiting to start

**Dashboards:**

- Job throughput over time
- Success/failure rate
- Average job duration by tenant
- Queue depth monitoring

---

## Future Enhancements

1. **Persistent Queue:** Store jobs in Redis/PostgreSQL for crash recovery
2. **Job Prioritization:** High-priority jobs run first
3. **Webhook Callbacks:** Notify external systems when jobs complete
4. **Rate Limiting:** Per-tenant job creation limits
5. **Job Dependencies:** Chain jobs (job B runs after job A completes)
6. **Scheduled Jobs:** Cron-like job scheduling
7. **Batch Operations:** Submit multiple URLs in one request

---

## Files to Create/Modify

### New Files (1)

1. **`src/server/job_queue.py`** (~100 lines)
   - JobStatus enum
   - Job dataclass
   - JobQueue class

### Modified Files (2)

1. **`src/server/routes/pipeline_api.py`** (~100 lines added)
   - POST /pipeline/jobs
   - GET /pipeline/jobs/{job_id}
   - DELETE /pipeline/jobs/{job_id}
   - GET /pipeline/jobs
   - Background executor

2. **`src/core/settings.py`** (~5 lines added)
   - enable_pipeline_job_queue flag

### Test Files (2)

1. **`tests/test_job_queue.py`** (NEW - ~50 lines)
2. **`tests/test_pipeline_api_async.py`** (NEW - ~100 lines)

**Total:** ~355 lines (exceeds estimate, but comprehensive)

---

## Implementation Priority

**Phase 1 (Core):**

- ✅ JobQueue class with basic operations
- ✅ POST /pipeline/jobs endpoint
- ✅ GET /pipeline/jobs/{job_id} endpoint
- ✅ Background executor

**Phase 2 (Management):**

- ✅ DELETE /pipeline/jobs/{job_id} endpoint
- ✅ GET /pipeline/jobs listing endpoint
- ✅ Job expiry cleanup task

**Phase 3 (Monitoring):**

- ✅ Metrics instrumentation
- ✅ Progress tracking
- ⏳ Dashboard creation (future)

---

**Next Steps:** Implement Phase 1 (core functionality) in `src/server/job_queue.py` and update `src/server/routes/pipeline_api.py`.
