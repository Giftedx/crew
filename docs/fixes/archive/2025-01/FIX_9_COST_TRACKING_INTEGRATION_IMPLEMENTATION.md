# Fix #9: Cost Tracking Integration - Implementation Plan

**Date:** 2025-01-03  
**Status:** IN PROGRESS  
**Impact:** MEDIUM - Enables production cost monitoring and budget enforcement

---

## Problem Statement

**Issue:** Cost tracking infrastructure exists (`core/cost_tracker.py`) but is NOT integrated with autonomous intelligence workflow

**Current State:**

- ✅ `CostTracker` class implemented (566 lines) with comprehensive features:
  - LLM cost recording (`record_llm_cost`)
  - Vector operation cost tracking (`record_vector_operation_cost`)
  - Budget enforcement (daily/monthly/hourly limits)
  - Cost aggregation and reporting
  - Alert callbacks (Discord notifications)
- ✅ `RequestCostTracker` implemented for request-scoped cumulative tracking
- ❌ **NOT used in autonomous_orchestrator.py** (zero integration)
- ❌ No cost tracking for `/autointel` workflow
- ❌ No budget limits per tenant or depth level
- ❌ No visibility into LLM usage costs

**Impact:**

- Cannot track costs for autonomous intelligence operations
- No budget enforcement (risk of runaway costs)
- Missing cost optimization opportunities
- No tenant-specific cost accountability

---

## Current Infrastructure Analysis

### 1. Cost Tracker Features (`core/cost_tracker.py`)

**Core Functions:**

```python
# Record LLM costs
record_llm_cost(
    operation_id="autointel_analysis_abc123",
    provider="openai",
    model="gpt-4",
    input_tokens=1500,
    output_tokens=500,
    cost_usd=Decimal("0.045"),
    duration_seconds=2.3,
    tenant_id="guild_123456",
    workspace_id="general"
)

# Record vector operations
record_vector_operation_cost(
    operation_id="memory_store_abc123",
    operation_type="upsert",  # search, upsert, delete
    provider="qdrant",
    vectors_count=10,
    cost_usd=Decimal("0.001"),
    tenant_id="guild_123456"
)

# Get cost summary
summary = get_cost_summary(
    start_time=workflow_start,
    end_time=workflow_end,
    tenant_id="guild_123456"
)
# Returns: total_cost, operations_count, cost_by_provider, cost_by_operation_type

# Set tenant budgets
set_tenant_budget(
    tenant_id="guild_123456",
    max_daily_cost=Decimal("10.00"),
    max_monthly_cost=Decimal("250.00"),
    max_hourly_cost=Decimal("2.00")
)

# Export reports
report = export_cost_report(days=7)
```

**Budget Enforcement:**

- Automatic checks on `record_cost()`
- Triggers Discord alerts when limits exceeded
- Supports hard limits (reject requests) or soft limits (warn only)

### 2. Request Budget Tracker (`services/request_budget.py`)

**Request-Scoped Tracking:**

```python
from services.request_budget import track_request_budget, current_request_tracker

# Context manager for request-scoped budget
with track_request_budget(total_limit=1.50, per_task_limits={"analysis": 0.75}):
    # All LLM calls within this block are tracked
    # Automatic rejection if limits exceeded
    result = await crew.kickoff(...)
```

**Features:**

- Thread-local storage (one tracker per request)
- Cumulative cost enforcement across multiple model calls
- Per-task budget limits (acquisition, transcription, analysis, etc.)
- Transparent integration with existing code

### 3. Integration Points in `/autointel`

**Where to Add Cost Tracking:**

**Point 1: Workflow Start** (`execute_autonomous_intelligence_workflow`)

- Initialize request cost tracker
- Set budget based on depth level
- Start cost monitoring

**Point 2: CrewAI Execution** (`_execute_crew_workflow`)

- Wrap crew.kickoff() with request budget context
- Record workflow-level costs

**Point 3: Task Completion** (`_task_completion_callback`)

- Extract cost data from task outputs (if available)
- Record per-task costs
- Update cumulative totals

**Point 4: Workflow End**

- Get final cost summary
- Log to Discord (if significant)
- Update tenant cost history

---

## Implementation Plan

### Step 1: Add Cost Tracking to Workflow Start (30 lines)

**File:** `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py`  
**Location:** `execute_autonomous_intelligence_workflow()` method (lines ~1036)

**Add:**

```python
from core.cost_tracker import record_llm_cost, get_cost_summary, initialize_cost_tracking
from services.request_budget import track_request_budget
from decimal import Decimal

# In __init__ or module level:
initialize_cost_tracking()  # Setup Discord alerts

# In execute_autonomous_intelligence_workflow():
async def execute_autonomous_intelligence_workflow(
    self, interaction, url, depth="standard", tenant_ctx=None
):
    # ... existing setup ...
    
    # Determine budget based on depth
    budget_limits = self._get_budget_limits(depth)
    
    # Track request-scoped costs
    workflow_id = f"autointel_{int(time.time())}_{hash(url) % 10000}"
    
    with track_request_budget(
        total_limit=budget_limits["total"],
        per_task_limits=budget_limits["per_task"]
    ):
        # Execute workflow
        result = await self._execute_crew_workflow(...)
        
        # Get cost summary
        tracker = current_request_tracker()
        if tracker:
            cost_summary = {
                "total_spent": tracker.total_spent,
                "per_task_spent": tracker.per_task_spent,
                "budget_utilization": tracker.total_spent / budget_limits["total"] * 100
            }
            
            # Log if significant cost
            if tracker.total_spent > 0.50:  # $0.50 threshold
                await interaction.followup.send(
                    f"💰 Cost: ${tracker.total_spent:.2f} "
                    f"({cost_summary['budget_utilization']:.1f}% of budget)"
                )
```

### Step 2: Add Budget Limit Configuration (20 lines)

**Add helper method:**

```python
def _get_budget_limits(self, depth: str) -> dict[str, Any]:
    """Get budget limits based on analysis depth."""
    
    # Budget tiers by depth
    budgets = {
        "quick": {
            "total": 0.50,  # $0.50 total
            "per_task": {
                "acquisition": 0.05,
                "transcription": 0.15,
                "analysis": 0.30
            }
        },
        "standard": {
            "total": 1.50,  # $1.50 total
            "per_task": {
                "acquisition": 0.05,
                "transcription": 0.30,
                "analysis": 0.75,
                "verification": 0.40
            }
        },
        "deep": {
            "total": 3.00,  # $3.00 total
            "per_task": {
                "acquisition": 0.05,
                "transcription": 0.50,
                "analysis": 1.20,
                "verification": 0.75,
                "knowledge": 0.50
            }
        },
        "comprehensive": {
            "total": 5.00,  # $5.00 total
            "per_task": {
                "acquisition": 0.10,
                "transcription": 0.75,
                "analysis": 2.00,
                "verification": 1.00,
                "knowledge": 1.15
            }
        },
        "experimental": {
            "total": 10.00,  # $10.00 total (fallback to comprehensive)
            "per_task": {
                "acquisition": 0.10,
                "transcription": 1.50,
                "analysis": 4.00,
                "verification": 2.00,
                "knowledge": 2.40
            }
        }
    }
    
    return budgets.get(depth, budgets["standard"])
```

### Step 3: Record Individual LLM Costs (40 lines)

**Integration with CrewAI:**

CrewAI doesn't expose per-call cost data directly, so we'll:

1. Track at workflow level (total cost via request budget)
2. Estimate costs based on known model pricing
3. Record actual costs when available from LLM router

**Add cost estimation:**

```python
def _estimate_task_cost(
    self, 
    task_type: str, 
    model: str, 
    input_length: int, 
    output_length: int
) -> Decimal:
    """Estimate task cost based on token usage."""
    
    # Pricing per 1K tokens (USD)
    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    }
    
    model_pricing = pricing.get(model, {"input": 0.01, "output": 0.03})
    
    # Estimate tokens (rough: 1 token ≈ 4 chars)
    input_tokens = input_length // 4
    output_tokens = output_length // 4
    
    input_cost = (input_tokens / 1000) * model_pricing["input"]
    output_cost = (output_tokens / 1000) * model_pricing["output"]
    
    return Decimal(str(input_cost + output_cost))
```

**Record costs in task callback:**

```python
def _task_completion_callback(self, task_output: Any) -> None:
    """Enhanced callback with cost tracking."""
    
    # ... existing JSON extraction ...
    
    # Extract model info if available
    model_used = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
    
    # Estimate cost based on output length
    output_text = str(task_output.raw)
    estimated_cost = self._estimate_task_cost(
        task_type=task_name,  # "acquisition", "transcription", etc.
        model=model_used,
        input_length=len(self._last_input or ""),
        output_length=len(output_text)
    )
    
    # Record cost
    record_llm_cost(
        operation_id=f"{self._workflow_id}_{task_name}",
        provider="openai",  # From env detection
        model=model_used,
        input_tokens=len(self._last_input or "") // 4,
        output_tokens=len(output_text) // 4,
        cost_usd=estimated_cost,
        duration_seconds=task_output.duration or 0.0,
        tenant_id=self._tenant_ctx.tenant_id if self._tenant_ctx else None,
        workspace_id=self._tenant_ctx.workspace_id if self._tenant_ctx else None
    )
    
    # Update request tracker
    tracker = current_request_tracker()
    if tracker:
        tracker.charge(float(estimated_cost), task_name)
```

### Step 4: Add Tenant Budget Configuration (30 lines)

**File:** `src/ultimate_discord_intelligence_bot/setup_cli.py` or new config file

**Add tenant budget setup:**

```python
def setup_tenant_budgets():
    """Configure budgets for known tenants."""
    from core.cost_tracker import set_tenant_budget
    from decimal import Decimal
    
    # Default budget for all tenants
    default_daily = Decimal("20.00")   # $20/day
    default_monthly = Decimal("500.00")  # $500/month
    default_hourly = Decimal("5.00")   # $5/hour
    
    # Set default
    set_tenant_budget(
        tenant_id="default",
        max_daily_cost=default_daily,
        max_monthly_cost=default_monthly,
        max_hourly_cost=default_hourly
    )
    
    # Override for specific tenants (from config)
    tenant_overrides = {
        "guild_123456": {  # High-volume server
            "daily": Decimal("50.00"),
            "monthly": Decimal("1200.00"),
            "hourly": Decimal("10.00")
        },
        "guild_789012": {  # Free-tier server
            "daily": Decimal("5.00"),
            "monthly": Decimal("100.00"),
            "hourly": Decimal("1.00")
        }
    }
    
    for tenant_id, limits in tenant_overrides.items():
        set_tenant_budget(
            tenant_id=tenant_id,
            max_daily_cost=limits["daily"],
            max_monthly_cost=limits["monthly"],
            max_hourly_cost=limits["hourly"]
        )
```

### Step 5: Add Cost Reporting Commands (40 lines)

**Add Discord command for cost reports:**

```python
# In discord_bot/registrations.py or new cost_commands.py

@bot.hybrid_command(name="costReport", description="View cost report for this server")
async def cost_report_command(ctx):
    """Generate cost report for current tenant."""
    
    # Get tenant from guild
    tenant_id = f"guild_{ctx.guild.id}" if ctx.guild else "dm"
    
    # Get cost summary (last 7 days)
    end_time = time.time()
    start_time = end_time - (7 * 24 * 3600)
    
    summary = get_cost_summary(
        start_time=start_time,
        end_time=end_time,
        tenant_id=tenant_id
    )
    
    # Format report
    report = f"""
📊 **Cost Report - Last 7 Days**
**Server:** {ctx.guild.name if ctx.guild else 'Direct Message'}

**Total Cost:** ${summary.total_cost_usd:.2f}
**Operations:** {summary.operations_count}
**Avg Cost/Op:** ${summary.average_cost_per_operation:.4f}

**By Operation:**
"""
    
    for op_type, cost in sorted(
        summary.cost_by_operation_type.items(), 
        key=lambda x: x[1], 
        reverse=True
    ):
        report += f"• {op_type}: ${cost:.2f}\n"
    
    # Get budget status
    budget_status = get_cost_tracker().get_budget_status(tenant_id)
    
    if "error" not in budget_status:
        report += f"""
**Budget Status:**
• Daily: ${budget_status['daily_cost']:.2f} / ${budget_status['daily_budget']:.2f} ({budget_status['daily_utilization']*100:.1f}%)
• Monthly: ${budget_status['monthly_cost']:.2f} / ${budget_status['monthly_budget']:.2f} ({budget_status['monthly_utilization']*100:.1f}%)
"""
    
    await ctx.send(report)


@bot.hybrid_command(name="exportCostReport", description="Export detailed cost report")
async def export_cost_report_command(ctx, days: int = 7):
    """Export comprehensive cost report."""
    
    report = export_cost_report(days=days)
    
    # Send as file if too long
    if len(report) > 1900:
        import io
        file = io.StringIO(report)
        await ctx.send(
            file=discord.File(file, filename=f"cost_report_{days}days.md"),
            content=f"📊 Cost report for last {days} days"
        )
    else:
        await ctx.send(f"```markdown\n{report}\n```")
```

---

## Implementation Summary

**Files to Modify:**

1. **`src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py`** (~120 lines added)
   - Import cost tracking modules
   - Add `_get_budget_limits()` method
   - Add `_estimate_task_cost()` method
   - Wrap workflow with `track_request_budget()`
   - Record costs in `_task_completion_callback()`
   - Add cost summary to workflow result

2. **`src/ultimate_discord_intelligence_bot/setup_cli.py`** (~30 lines added)
   - Add `setup_tenant_budgets()` function
   - Call during initialization

3. **`src/ultimate_discord_intelligence_bot/discord_bot/registrations.py`** (~80 lines added)
   - Add `/costReport` command
   - Add `/exportCostReport` command
   - Add cost display to `/autointel` completion

**Total Estimated Changes:** ~230 lines

**Testing Plan:**

1. **Unit Tests:**
   - Budget limit calculation
   - Cost estimation accuracy
   - Request budget enforcement

2. **Integration Tests:**
   - Full workflow cost tracking
   - Budget limit enforcement
   - Cost report generation

3. **Manual Testing:**
   - Run `/autointel` and verify cost tracking
   - Trigger budget alerts
   - Generate cost reports
   - Verify tenant isolation

---

## Expected Outcomes

**After Implementation:**

✅ **Cost Visibility:**

- All `/autointel` workflows tracked
- Per-task cost breakdown
- Tenant-specific cost attribution

✅ **Budget Enforcement:**

- Automatic rejection when budget exceeded
- Discord alerts for budget issues
- Configurable limits per tenant/depth

✅ **Cost Optimization:**

- Identify expensive operations
- Track cost trends over time
- Compare depth levels vs cost

✅ **Reporting:**

- `/costReport` command for users
- Export detailed reports
- Cost displayed in workflow completion

**Metrics to Track:**

- `autointel_cost_usd` (histogram by depth, tenant)
- `autointel_budget_exceeded_total` (counter)
- `autointel_cost_by_task` (histogram by task type)
- `autointel_operations_count` (counter)

---

## Next Steps

1. Implement Step 1: Workflow cost tracking
2. Implement Step 2: Budget limit configuration
3. Implement Step 3: Individual LLM cost recording
4. Implement Step 4: Tenant budget setup
5. Implement Step 5: Cost reporting commands
6. Add tests and validation
7. Update documentation

**Priority:** MEDIUM (enables cost control but not blocking)  
**Estimated Effort:** ~3-4 hours for full implementation
