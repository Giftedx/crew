# Agent Tool Mapping Guide

## Comprehensive Tool Ecosystem for Multi-Agent Intelligence Operations

This document provides detailed guidance on tool allocation and usage patterns across the redesigned 15-agent CrewAI roster for optimal autonomous intelligence operations.

## Strategic Control & Coordination

### Autonomous Mission Coordinator

**Primary Role**: Strategic workflow orchestration and resource allocation
**Core Tools**:

- `PipelineTool()` - Execute full ContentPipeline workflows
- `AdvancedPerformanceAnalyticsTool()` - Monitor system performance and resource usage
- `TimelineTool()` - Track mission progress and coordinate temporal dependencies
- `PerspectiveSynthesizerTool()` - Synthesize multiple agent outputs
- `MCPCallTool()` - Cross-tenant coordination and external integrations
- `SystemStatusTool()` - Monitor overall system health

**Usage Patterns**:

- Begin all workflows with PipelineTool for baseline content processing
- Use AdvancedPerformanceAnalyticsTool to track resource consumption
- Coordinate agent handoffs using TimelineTool timestamps
- Synthesize cross-agent insights with PerspectiveSynthesizerTool

## Content Acquisition & Processing

### Multi-Platform Acquisition Specialist

**Primary Role**: Sophisticated content acquisition across 20+ platforms
**Core Tools**:

- `MultiPlatformDownloadTool()` - Primary acquisition tool for all platforms
- `EnhancedYouTubeDownloadTool()` - Advanced YouTube content extraction
- `YtDlpDownloadTool()` - Fallback downloader with extensive format support
- Platform-specific tools: `YouTubeDownloadTool()`, `TwitchDownloadTool()`, `TwitterDownloadTool()`, etc.
- Resolver tools: `PodcastResolverTool()`, `SocialResolverTool()`, `TwitchResolverTool()`
- `DriveUploadTool()`, `DriveUploadToolBypass()` - Content preservation and sharing

**Usage Patterns**:

1. Start with MultiPlatformDownloadTool for broad platform support
2. Escalate to platform-specific tools when specialized features needed
3. Use resolver tools for metadata enrichment and URL normalization
4. Always preserve content to Drive for downstream processing

### Advanced Transcription Engineer

**Primary Role**: High-fidelity speech-to-text with linguistic enhancement
**Core Tools**:

- `AudioTranscriptionTool()` - Core speech recognition engine
- `TranscriptIndexTool()` - Create searchable transcript indices
- `TimelineTool()` - Synchronize transcripts with media timelines
- `DriveUploadTool()` - Preserve enhanced transcripts
- `TextAnalysisTool()` - Quality assessment and enhancement

**Usage Patterns**:

- Process all audio/video through AudioTranscriptionTool
- Build comprehensive indices with TranscriptIndexTool
- Synchronize speaker changes and topic shifts with TimelineTool
- Enhance transcript quality using TextAnalysisTool feedback

### Comprehensive Linguistic Analyst

**Primary Role**: Deep linguistic analysis and semantic extraction
**Core Tools**:

- `EnhancedAnalysisTool()` - Advanced NLP and semantic analysis
- `TextAnalysisTool()` - Core text processing and analysis
- `SentimentTool()` - Emotional tone and sentiment mapping
- `PerspectiveSynthesizerTool()` - Multi-perspective analysis synthesis
- `TranscriptIndexTool()` - Leverage indexed content for analysis
- `LCSummarizeTool()` - Content summarization and key point extraction

**Usage Patterns**:

- Apply EnhancedAnalysisTool for comprehensive linguistic mapping
- Track sentiment evolution using SentimentTool across content timeline
- Synthesize multiple analytical perspectives with PerspectiveSynthesizerTool
- Create executive summaries with LCSummarizeTool

## Verification & Risk Assessment

### Information Verification Director

**Primary Role**: Multi-source fact-checking and claim verification
**Core Tools**:

- `FactCheckTool()` - Primary fact verification engine
- `LogicalFallacyTool()` - Identify logical reasoning errors
- `ClaimExtractorTool()` - Extract verifiable claims from content
- `ContextVerificationTool()` - Cross-reference contextual information
- `PerspectiveSynthesizerTool()` - Synthesize verification results
- `VectorSearchTool()` - Search existing knowledge base
- `RagQueryVectorStoreTool()` - Query RAG systems for verification

**Usage Patterns**:

1. Extract claims using ClaimExtractorTool
2. Verify each claim with FactCheckTool
3. Check for logical fallacies using LogicalFallacyTool
4. Cross-reference context with ContextVerificationTool
5. Query knowledge bases with VectorSearchTool for supporting evidence

### Threat Intelligence Analyst

**Primary Role**: Deception detection and risk assessment
**Core Tools**:

- `DeceptionScoringTool()` - Quantify deception probability
- `TruthScoringTool()` - Assess truthfulness metrics
- `TrustworthinessTrackerTool()` - Track entity reliability over time
- `LeaderboardTool()` - Maintain ranking systems for entities
- `LogicalFallacyTool()` - Identify manipulative reasoning patterns
- `PerspectiveSynthesizerTool()` - Synthesize risk assessments

**Usage Patterns**:

- Score all content for deception using DeceptionScoringTool
- Assess truthfulness with TruthScoringTool
- Update entity trustworthiness scores with TrustworthinessTrackerTool
- Identify manipulation techniques with LogicalFallacyTool

## Behavioral Analysis & Knowledge Systems

### Behavioral Profiling Specialist

**Primary Role**: Psychological profiling and behavioral analysis
**Core Tools**:

- `CharacterProfileTool()` - Build comprehensive personality profiles
- `TimelineTool()` - Track behavioral changes over time
- `SentimentTool()` - Analyze emotional patterns
- `TrustworthinessTrackerTool()` - Monitor trust evolution
- `DeceptionScoringTool()` - Identify deceptive behavioral patterns
- `PerspectiveSynthesizerTool()` - Synthesize behavioral insights

**Usage Patterns**:

- Build detailed profiles using CharacterProfileTool
- Track behavioral evolution with TimelineTool
- Analyze emotional patterns using SentimentTool
- Correlate trust and deception metrics across time

### Knowledge Integration Architect

**Primary Role**: Multi-layer memory system orchestration
**Core Tools**:

- `MemoryStorageTool()` - Primary knowledge storage
- `GraphMemoryTool()` - Relationship and graph-based knowledge
- `HippoRagContinualMemoryTool()` - Continual learning systems
- `MemoryCompactionTool()` - Optimize memory efficiency
- `RagIngestTool()`, `RagIngestUrlTool()` - Content ingestion
- `RagHybridTool()` - Hybrid retrieval systems
- `VectorSearchTool()` - Vector-based knowledge retrieval
- `RagQueryVectorStoreTool()` - Query optimization
- `OfflineRAGTool()` - Offline knowledge processing

**Usage Patterns**:

1. Ingest all verified content using RagIngestTool
2. Build knowledge graphs with GraphMemoryTool
3. Implement continual learning with HippoRagContinualMemoryTool
4. Optimize storage efficiency using MemoryCompactionTool
5. Provide hybrid retrieval through RagHybridTool

## Social Intelligence & Monitoring

### Social Intelligence Coordinator

**Primary Role**: Cross-platform social monitoring and sentiment tracking
**Core Tools**:

- `SocialMediaMonitorTool()` - Multi-platform social monitoring
- `XMonitorTool()` - Twitter/X-specific monitoring
- `DiscordMonitorTool()` - Discord community monitoring
- `SentimentTool()` - Track sentiment across platforms
- `MultiPlatformMonitorTool()` - Comprehensive platform monitoring
- `SocialResolverTool()` - Social media URL resolution
- `PerspectiveSynthesizerTool()` - Synthesize cross-platform insights

**Usage Patterns**:

- Monitor multiple platforms simultaneously
- Track sentiment evolution across conversations
- Identify viral content and trending topics
- Correlate cross-platform narrative spread

### Trend Analysis Scout

**Primary Role**: Emerging content and viral pattern detection
**Core Tools**:

- `MultiPlatformMonitorTool()` - Broad platform scanning
- `ResearchAndBriefTool()` - Research emerging topics
- `ResearchAndBriefMultiTool()` - Multi-source research synthesis
- `SocialResolverTool()` - Content URL normalization
- `SentimentTool()` - Track sentiment momentum
- `VectorSearchTool()` - Compare against historical patterns
- `RagQueryVectorStoreTool()` - Query knowledge for context

**Usage Patterns**:

- Continuously scan for emerging content patterns
- Research background context for trending topics
- Compare current trends against historical data
- Provide early warning for viral content

## Research & Intelligence Synthesis

### Research Synthesis Specialist

**Primary Role**: Multi-source intelligence gathering and synthesis
**Core Tools**:

- `ResearchAndBriefTool()` - Primary research capabilities
- `ResearchAndBriefMultiTool()` - Multi-source research synthesis
- `RagHybridTool()` - Hybrid knowledge retrieval
- `RagQueryVectorStoreTool()` - Optimized knowledge queries
- `LCSummarizeTool()` - Research summarization
- `OfflineRAGTool()` - Offline research processing
- `VectorSearchTool()` - Knowledge base exploration
- `ContextVerificationTool()` - Research verification
- `PerspectiveSynthesizerTool()` - Multi-source synthesis

**Usage Patterns**:

1. Gather information from multiple research tools
2. Cross-verify research findings
3. Synthesize insights from diverse sources
4. Create comprehensive research briefings

### Intelligence Briefing Director

**Primary Role**: Executive briefing creation and strategic communication
**Core Tools**:

- `LCSummarizeTool()` - Executive summary creation
- `PerspectiveSynthesizerTool()` - Multi-agent insight synthesis
- `RagQueryVectorStoreTool()` - Reference and citation management
- `VectorSearchTool()` - Supporting evidence retrieval
- `TimelineTool()` - Temporal context and chronology
- `DriveUploadTool()` - Briefing distribution and archival
- `ResearchAndBriefTool()` - Additional research as needed
- `ContextVerificationTool()` - Briefing accuracy verification

**Usage Patterns**:

- Synthesize all agent outputs into coherent briefings
- Maintain clear chronological context
- Provide executive-ready summaries
- Ensure all briefings are properly archived

## Strategic Communication & Operations

### Strategic Argument Analyst

**Primary Role**: Argumentation analysis and debate preparation
**Core Tools**:

- `SteelmanArgumentTool()` - Construct strongest possible arguments
- `DebateCommandTool()` - Debate strategy and preparation
- `FactCheckTool()` - Argument verification
- `PerspectiveSynthesizerTool()` - Multi-perspective argument analysis
- `LogicalFallacyTool()` - Identify reasoning weaknesses
- `ClaimExtractorTool()` - Extract key argument points

**Usage Patterns**:

- Construct steelman versions of all arguments
- Identify logical weaknesses and fallacies
- Prepare comprehensive debate strategies
- Synthesize multiple argumentative perspectives

### System Operations Manager

**Primary Role**: System health and performance optimization
**Core Tools**:

- `SystemStatusTool()` - Core system monitoring
- `AdvancedPerformanceAnalyticsTool()` - Performance analytics and optimization
- `DiscordPrivateAlertTool()` - Incident notification system
- `PipelineTool()` - Pipeline health monitoring
- `TimelineTool()` - Performance timeline tracking
- `MCPCallTool()` - System coordination

**Usage Patterns**:

- Continuously monitor system health metrics
- Proactively identify performance bottlenecks
- Coordinate incident response and alerts
- Optimize resource allocation across workflows

### Community Engagement Coordinator

**Primary Role**: Community interaction and communication management
**Core Tools**:

- `DiscordQATool()` - Community question answering
- `DiscordPostTool()` - Community communication
- `VectorSearchTool()` - Knowledge retrieval for answers
- `PerspectiveSynthesizerTool()` - Synthesize responses
- `LCSummarizeTool()` - Create accessible summaries
- `TimelineTool()` - Track community interactions

**Usage Patterns**:

- Answer community questions using verified knowledge
- Facilitate meaningful community dialogue
- Translate complex analysis into accessible communications
- Maintain engagement timeline and follow-ups

## Tool Selection Strategy by Analysis Depth

### Standard Analysis (10 stages)

- Focus on core tools for each agent
- Prioritize speed and efficiency
- Use primary tools without extensive cross-references

### Deep Analysis (15 stages)

- Add secondary tools for enhanced capabilities
- Include cross-agent tool coordination
- Utilize synthesis tools for deeper insights

### Comprehensive Analysis (20 stages)

- Full tool ecosystem utilization
- Advanced coordination between agents
- Comprehensive verification and cross-referencing

### Experimental Analysis (25 stages)

- All available tools across all agents
- Maximum coordination and synthesis
- Advanced predictive and learning capabilities
- Full multi-modal integration and optimization
