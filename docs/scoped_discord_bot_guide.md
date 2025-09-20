# Scoped Discord Bot - User Guide

## 🎯 **Read-Only Presentation System**

This Discord bot provides a **strictly limited interface** for accessing analysis results through timeline presentations and system monitoring.

### 🔒 **Access Model**

- **Analysis occurs off-platform** - no direct tool/agent exposure via Discord
- **Read-only presentation** - bot only displays pre-analyzed results
- **Limited command families** - only system, operations, development, and analytics
- **Timeline-based content** - subject-focused chronological presentations

---

## 📋 **Available Commands**

### 🖥️ **System Domain** (Slash Commands)

**`/system-status`** - Comprehensive system health overview

- Overall system status and uptime
- Processing statistics and queue status
- High-level performance metrics

**`/system-tools`** - Available analysis capabilities

- Content analysis capabilities
- Timeline generation features
- Evidence consolidation tools
- Analytical framing methods

**`/system-performance [agent]`** - Performance monitoring

- Processing speed and success rates
- Quality metrics and accuracy scores
- Agent-specific performance data (optional)

**`/system-audit`** - System self-assessment

- Capability and compliance review
- Read-only mode verification
- Configuration recommendations

### 🔧 **Operations** (Prefix Commands)

**`!ops-status [--detailed] [--component=name]`** - System status for operators

- Detailed system metrics
- Component-specific status
- Administrative health indicators

**`!ops-queue [--clear] [--priority=level]`** - Processing queue management

- Queue status and pending items
- Priority filtering
- Queue clearing (with confirmation)

**`!ops-metrics <timeframe>`** - Performance metrics

- Processing and quality statistics
- System load and utilization
- Configurable time windows (1h, 6h, 24h, 7d)

### 🛠️ **Development** (Prefix Commands)

**`!dev-tools`** - Backend tool status

- Tool availability by category
- Status indicators and health checks
- Testing interface access

**`!dev-agents`** - Analysis agent monitoring

- Agent health and configuration
- Status indicators by category
- Performance overview

**`!dev-test <component> [params]`** - Component testing

- Available components: timeline, evidence, framing, analysis
- Development testing interface
- Performance metrics and validation

### 📊 **Analytics** (Prefix Commands)

**`!analytics-usage [timeframe] [filter]`** - Usage statistics

- Command usage patterns
- User engagement metrics
- Analysis activity summaries

**`!analytics-performance [agent]`** - Performance analytics

- Pipeline performance metrics
- Quality assessments
- Agent-specific breakdowns

**`!analytics-errors [component]`** - Error monitoring

- Error patterns and rates
- Common issues tracking
- Recent incidents review

---

## 🎯 **Key Features**

### 📈 **Timeline Presentations**

- **Subject-focused timelines** for tracked personalities (H3, HasanAbi, etc.)
- **Chronological organization** of content and events
- **Controversial statement identification** with context
- **Evidence references** and supporting materials

### 🔍 **Evidence Channels**

- **Dedicated channels** for supporting materials
- **Analytical framing** distinguishing facts from claims
- **Citation management** and cross-references
- **Metadata preservation** for provenance

### 🛡️ **Compliance Features**

- **Read-only interface** - no direct manipulation
- **Off-platform analysis** - processing happens externally
- **Limited command exposure** - only approved interfaces
- **Audit capabilities** - self-assessment and compliance

---

## 🚀 **Getting Started**

1. **System Status Check**

   ```
   /system-status
   ```

2. **View Available Capabilities**

   ```
   /system-tools
   ```

3. **Monitor Processing Queue**

   ```
   !ops-queue
   ```

4. **Check Usage Analytics**

   ```
   !analytics-usage 24h
   ```

### 📊 **Monitoring Workflow**

1. Use `/system-status` for quick health check
2. Use `!ops-metrics 24h` for detailed performance
3. Use `!analytics-errors` to monitor issues
4. Use `/system-audit` for compliance verification

### 🔧 **Development Workflow**

1. Use `!dev-tools` to check backend status
2. Use `!dev-agents` to monitor analysis components
3. Use `!dev-test timeline` to validate functionality
4. Use `!analytics-performance` to assess quality

---

## ⚠️ **Important Notes**

### 🔒 **Access Limitations**

- **No direct tool access** - tools operate off-platform only
- **No content analysis requests** - analysis happens automatically
- **No agent interaction** - agents work behind the scenes
- **Read-only presentations** - display results only

### 📋 **Command Structure**

- **Slash commands** (`/`) for system domain only
- **Prefix commands** (`!`) for ops, dev, and analytics
- **No custom commands** - strictly limited interface
- **No plugin exposure** - internal tools hidden

### 🎯 **Use Cases**

- **Timeline review** - chronological content summaries
- **System monitoring** - health and performance tracking
- **Evidence access** - supporting material review
- **Quality assessment** - analysis accuracy metrics

---

## 🆘 **Support**

### 📊 **System Issues**

- Use `/system-audit` for self-assessment
- Check `!ops-status --detailed` for diagnostics
- Review `!analytics-errors` for recent problems

### 🔧 **Development Issues**

- Use `!dev-tools` to check component status
- Test with `!dev-test <component>` for validation
- Monitor with `!analytics-performance` for quality

### 📈 **Performance Issues**

- Check `/system-performance` for overview
- Use `!ops-metrics` for detailed analysis
- Review `!analytics-usage` for patterns

---

*This bot implements a read-only presentation model with off-platform analysis. All processing occurs externally with results presented through timeline and evidence channels.*
