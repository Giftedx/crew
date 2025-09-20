# 🎯 Scoped Discord Bot Implementation

## Overview

This implementation provides a **read-only presentation Discord bot** with strictly limited command exposure, designed to present analysis results without direct tool or agent access.

## 🔒 **Key Design Principles**

### Read-Only Presentation Model

- **No direct tool access** via Discord interface
- **Off-platform analysis** - all processing happens externally
- **Timeline-based content presentation** for tracked subjects
- **Evidence consolidation** with analytical framing

### Limited Command Exposure

- **Only 4 command families** exposed to users
- **System Domain** (`/system-*`) - health and capabilities
- **Operations** (`!ops-*`) - administrative monitoring
- **Development** (`!dev-*`) - component testing
- **Analytics** (`!analytics-*`) - usage and performance

### Compliance and Security

- **Audit capabilities** for self-assessment
- **No user data exposure** in command outputs
- **Graceful error handling** without internal details
- **Rate limiting** and access controls

---

## 🚀 **Quick Start**

### 1. Launch the Scoped Bot

```bash
# Using the startup script (recommended)
./scripts/start_scoped_bot.sh

# Or directly with Python
python scripts/scoped_discord_bot.py
```

### 2. Verify System Status

```bash
# Check overall system health
/system-status

# View available capabilities
/system-tools

# Monitor processing queue
!ops-queue
```

### 3. Test Core Functions

```bash
# Test timeline generation
!dev-test timeline

# Check performance metrics
!analytics-performance

# Review system compliance
/system-audit
```

---

## 📋 **Command Reference**

### 🖥️ System Commands (Slash)

| Command | Description | Example |
|---------|-------------|---------|
| `/system-status` | System health overview | `/system-status` |
| `/system-tools` | Available capabilities | `/system-tools` |
| `/system-performance` | Performance monitoring | `/system-performance content_manager` |
| `/system-audit` | Compliance assessment | `/system-audit` |

### 🔧 Operations Commands (Prefix)

| Command | Description | Example |
|---------|-------------|---------|
| `!ops-status` | Detailed system status | `!ops-status --detailed` |
| `!ops-queue` | Queue management | `!ops-queue --priority=high` |
| `!ops-metrics` | Performance metrics | `!ops-metrics 24h` |

### 🛠️ Development Commands (Prefix)

| Command | Description | Example |
|---------|-------------|---------|
| `!dev-tools` | Backend tool status | `!dev-tools` |
| `!dev-agents` | Agent monitoring | `!dev-agents` |
| `!dev-test` | Component testing | `!dev-test timeline` |

### 📊 Analytics Commands (Prefix)

| Command | Description | Example |
|---------|-------------|---------|
| `!analytics-usage` | Usage statistics | `!analytics-usage 7d` |
| `!analytics-performance` | Performance analytics | `!analytics-performance fact_checker` |
| `!analytics-errors` | Error monitoring | `!analytics-errors timeline` |

---

## 🏗️ **Architecture**

### Bot Structure

```
ScopedCommandBot
├── TimelineManager          # Subject timeline management
├── System Commands          # /system-* (slash commands)
├── Operations Commands      # !ops-* (prefix commands)
├── Development Commands     # !dev-* (prefix commands)
├── Analytics Commands       # !analytics-* (prefix commands)
└── Backend Integration      # Off-platform analysis connection
```

### Data Flow

```
External Analysis → Timeline Events → Evidence Consolidation → Discord Presentation
                                   ↓
User Commands → Read-Only Interface → Formatted Results → Discord Embeds
```

### Security Model

```
Discord User → Limited Commands → Presentation Layer → (No Direct Access) → Backend Tools
```

---

## 🔧 **Configuration**

### Environment Variables

```bash
# Required
DISCORD_BOT_TOKEN=your_discord_bot_token

# Optional feature flags
ENABLE_INGEST_CONCURRENT=1
ENABLE_HTTP_RETRY=1
ENABLE_RL_GLOBAL=1
ENABLE_ANALYSIS_SENTIMENT=1
ENABLE_MEMORY_ARCHIVER=1
```

### Bot Configuration

The bot uses `config/scoped_bot_config.py` for detailed configuration:

- **Command limits** and allowed families
- **Timeline settings** and subject management
- **Performance thresholds** and monitoring
- **Compliance criteria** and audit settings

### Feature Flags

```python
# Core mode enforcement
READ_ONLY_MODE = True
OFF_PLATFORM_ANALYSIS = True
NO_TOOL_EXPOSURE = True
LIMITED_COMMAND_FAMILIES = True

# Feature toggles
ENABLE_SYSTEM_COMMANDS = True
ENABLE_OPS_COMMANDS = True
ENABLE_DEV_COMMANDS = True
ENABLE_ANALYTICS_COMMANDS = True
```

---

## 📊 **Timeline System**

### Subject Management

The bot tracks timelines for specific subjects:

- **H3 Podcast** - Episode analysis and controversial moments
- **HasanAbi** - Stream content and political commentary
- **Political Commentary** - General political analysis
- **General Analysis** - Misc content and topics

### Timeline Events

Each timeline event includes:

```python
{
    "timestamp": "2024-09-15T10:30:00Z",
    "type": "controversial_statement",
    "title": "Statement about political topic",
    "description": "Context and analysis",
    "source_url": "https://youtube.com/watch?v=...",
    "confidence": 0.85,
    "evidence_refs": ["evidence_123", "citation_456"],
    "analytical_framing": "Fact vs claim distinction"
}
```

### Evidence Consolidation

Supporting materials are organized with:

- **Analytical framing** distinguishing facts from claims
- **Citation management** with proper attribution
- **Cross-references** between related content
- **Metadata preservation** for provenance tracking

---

## 🛡️ **Compliance Features**

### Self-Audit Capabilities

The bot performs regular self-assessments:

```bash
# Run compliance check
/system-audit

# Results include:
# ✅ Read-only mode enforced
# ✅ Off-platform analysis verified
# ✅ No tool exposure confirmed
# ✅ Timeline accuracy: 89%
# ✅ Evidence quality: 87%
```

### Access Controls

- **Command family restrictions** - only approved commands exposed
- **Rate limiting** - prevents abuse and overload
- **Error sanitization** - no internal details exposed
- **Audit logging** - all activity tracked for compliance

### Performance Monitoring

Continuous monitoring of:

- **Response times** and processing speed
- **Success rates** and error patterns
- **Queue status** and backlog management
- **Quality metrics** for timeline and evidence accuracy

---

## 🔍 **Monitoring and Analytics**

### Performance Metrics

The bot tracks comprehensive metrics:

```bash
# System performance
!ops-metrics 24h
# → Processing: 847 items, 94% success rate
# → Quality: Timeline 89%, Evidence 87%, Framing 91%
# → Load: CPU 23%, Memory 67%, Queue 3 pending

# Agent performance
!analytics-performance content_manager
# → Tasks: 156 completed, 94% success rate
# → Quality: 88% average score
# → Response: 2.4s average time
```

### Usage Analytics

Track user engagement and system utilization:

```bash
!analytics-usage 7d
# → Commands: 234 total, 18 unique users
# → Popular: /system-status, !ops-queue, !dev-test
# → Timeline requests: 67, Evidence queries: 42
# → Peak usage: 14:00-16:00 UTC
```

### Error Analysis

Monitor system health and identify issues:

```bash
!analytics-errors
# → Error rate: 0.8% (12 total)
# → Common: Timeout (5), Rate limit (3), Parse error (2)
# → Recent: Timeline timeout, Evidence failure, API limit
```

---

## 🧪 **Development and Testing**

### Component Testing

Test individual system components:

```bash
# Test timeline generation
!dev-test timeline
# → Status: ✅ PASS
# → Duration: 850ms
# → Accuracy: 92%

# Test evidence consolidation
!dev-test evidence
# → Status: ✅ PASS
# → Response time: 1.2s
# → Quality score: 87%
```

### Agent Monitoring

Track analysis agent health:

```bash
!dev-agents
# → Content agents: 🟢🟢 (2/2 active)
# → Analysis agents: 🟢🟢🟡 (2/3 active, 1 degraded)
# → Synthesis agents: 🟢🟢 (2/2 active)
```

### Backend Integration

Monitor backend tool status:

```bash
!dev-tools
# → Analysis: ✅ 3/3 available
# → Timeline: ✅ 2/2 available
# → Evidence: ⚠️ 1/2 available (1 degraded)
```

---

## 📁 **File Structure**

```
scripts/
├── scoped_discord_bot.py      # Main bot implementation
├── start_scoped_bot.sh        # Startup script with environment setup
└── helpers/
    └── ui_constants.py        # UI constants and formatting

config/
├── scoped_bot_config.py       # Bot configuration and feature flags
└── ...

docs/
├── scoped_discord_bot_guide.md # User guide and command reference
└── ...
```

---

## 🔗 **Integration Points**

### Backend Analysis Pipeline

The scoped bot integrates with the existing analysis infrastructure:

- **Ingest queue** - monitors content processing
- **Analysis results** - presents completed analyses
- **Timeline events** - displays chronological data
- **Evidence storage** - accesses supporting materials

### CrewAI Agent System

Connects to the 13-agent CrewAI system:

- **Content managers** - content downloading and processing
- **Fact checkers** - claim verification and scoring
- **Analysts** - sentiment, topic, and context analysis
- **Synthesizers** - timeline building and evidence consolidation

### Data Storage

Interfaces with storage systems:

- **Vector stores** - semantic search and retrieval
- **Timeline databases** - chronological event storage
- **Evidence archives** - supporting material storage
- **Metrics storage** - performance and usage data

---

## 🎯 **Implementation Notes**

### Design Decisions

1. **Read-only by design** - prevents accidental data modification
2. **Limited command exposure** - reduces attack surface
3. **Off-platform analysis** - maintains separation of concerns
4. **Timeline focus** - provides chronological context
5. **Evidence consolidation** - supports analytical integrity

### Security Considerations

- **No direct tool access** - tools remain behind API boundaries
- **Sanitized error messages** - internal details not exposed
- **Rate limiting** - prevents abuse and overload
- **Audit logging** - compliance and monitoring
- **Command family restrictions** - only approved interfaces exposed

### Performance Optimizations

- **Mock data mode** - fast responses during development
- **Async operations** - non-blocking command processing
- **Response caching** - reduce backend load
- **Graceful degradation** - partial functionality during issues

---

## 📞 **Support and Troubleshooting**

### Common Issues

1. **Commands not working** - Check feature flags and bot permissions
2. **Slow responses** - Monitor queue status with `!ops-queue`
3. **Missing data** - Verify backend integration and analysis pipeline
4. **Permission errors** - Ensure proper Discord role configuration

### Diagnostics

```bash
# Check system health
/system-status

# Verify backend connectivity
!ops-status --detailed

# Test component functionality
!dev-test timeline

# Review error patterns
!analytics-errors
```

### Logs and Monitoring

- **Bot logs** - `/home/crew/logs/scoped_discord_bot.log`
- **Performance metrics** - Available via `!analytics-performance`
- **Error tracking** - Available via `!analytics-errors`
- **Audit logs** - Compliance and usage tracking

---

*This scoped implementation provides a secure, read-only interface for accessing analysis results while maintaining strict separation between user interactions and internal system capabilities.*
