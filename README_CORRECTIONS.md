# README Corrections - Recommended Updates

## Section 1: Update Agent Count in Overview (Line 7)

**Current:**

```markdown
A production-ready, multi-tenant intelligence system powered by autonomous AI agents for content analysis, fact-checking, and cross-platform monitoring. Built with CrewAI orchestration, 111 specialized tools, and a modern 3-layer architecture.
```

**Corrected:**

```markdown
A production-ready, multi-tenant intelligence system powered by autonomous AI agents for content analysis, fact-checking, and cross-platform monitoring. Built with CrewAI orchestration, 31 specialized agents, 111 specialized tools, and a modern 3-layer architecture.
```

## Section 2: Update Core Components (Line 59)

**Current:**

```markdown
- **CrewAI Framework**: Orchestrates 18 specialized agents with role-based tool access
```

**Corrected:**

```markdown
- **CrewAI Framework**: Orchestrates 31 specialized agents with role-based tool access across strategic, operational, and specialized domains
```

## Section 3: Expand Agent Specialists List (Lines 66-87)

**Current:**
Lists only 18 agents with generic descriptions

**Corrected - Complete 31-Agent List:**

```markdown
### Agent Specialists

#### Executive & Strategic Layer (2 agents)

1. **Executive Supervisor**: Strategic oversight, resource allocation, and mission success with 98% accuracy target
2. **Workflow Manager**: Task routing, dependency management, and load balancing across agent hierarchies

#### Coordination & Mission Control (1 agent)

3. **Mission Orchestrator**: End-to-end mission coordination, depth sequencing, and budget management

#### Content Acquisition & Processing (3 agents)

4. **Acquisition Specialist**: Multi-platform content download with rate limit handling and quality fallbacks
5. **Transcription Engineer**: Audio/video transcription with Whisper/AssemblyAI and searchable indexing
6. **Analysis Cartographer**: Linguistic, sentiment, and thematic signal mapping for downstream teams

#### Verification & Risk (2 agents)

7. **Verification Director**: Fact-checking, claim extraction, and defensible verdict generation with 96% accuracy
8. **Risk Intelligence Analyst**: Deception scoring, trust metrics, and longitudinal behavior tracking

#### Knowledge & Personas (2 agents)

9. **Persona Archivist**: Living dossiers with behavior, sentiment, and trust milestones
10. **Knowledge Integrator**: Memory consolidation across vector, graph, and continual memory systems

#### Signal Intelligence (2 agents)

11. **Signal Recon Specialist**: Cross-platform discourse and sentiment tracking for verification priorities
12. **Trend Intelligence Scout**: Emerging content detection and prioritization with watch list monitoring

#### Community & Research (4 agents)

13. **Community Liaison**: Community Q&A with verified intelligence and context retrieval
14. **Argument Strategist**: Steelman arguments, debate prep, and persuasive narrative building
15. **Research Synthesist**: Deep background briefs harmonizing multiple research perspectives
16. **Intelligence Briefing Curator**: Stakeholder-ready intelligence packets with timelines and citations

#### System Reliability (2 agents)

17. **System Reliability Officer**: Pipeline health, dashboard monitoring, and operational visibility
18. **Personality Synthesis Manager**: Consistent tone, style, and persona alignment across outputs

#### Specialized AI Agents - Phase 3.1 (5 agents)

19. **Visual Intelligence Specialist**: Computer vision, image analysis, OCR, and visual fact-checking with 92% accuracy
20. **Audio Intelligence Specialist**: Music recognition, speaker diarization, emotional tone, and acoustic classification
21. **Trend Intelligence Specialist**: Real-time trend monitoring, viral prediction, and long-term forecasting
22. **Content Generation Specialist**: AI-powered content creation, adaptation, and platform optimization
23. **Cross-Platform Intelligence Specialist**: Multi-platform correlation, content propagation tracking, and cross-platform trends

#### Creator Network Intelligence (6 agents)

24. **Network Discovery Specialist**: Social network mapping, collaboration pattern detection, and influence dynamics
25. **Deep Content Analyst**: Multimodal long-form analysis, debate extraction, and narrative arc tracking
26. **Guest Intelligence Specialist**: Guest profiling, collaborator tracking, and monitoring recommendations
27. **Controversy Tracker Specialist**: Drama detection, conflict tracking, and early warning systems
28. **Insight Generation Specialist**: High-level pattern synthesis and actionable intelligence delivery
29. **Quality Assurance Specialist**: Output validation, hallucination detection, consistency checks, and re-analysis triggers

#### Discord AI Conversational (2 agents)

30. **Conversational Response Agent**: Natural, context-aware Discord responses with personality consistency
31. **Personality Evolution Agent**: RL-based personality optimization through user interaction feedback
```

## Section 4: Fix Setup Instructions (Line 158)

**Current:**

```bash
pip install -r requirements.lock
```

**Corrected:**

```bash
# Install with development dependencies (recommended)
pip install -e '.[dev]'

# OR install minimal production dependencies
pip install -e .

# Optional feature sets
pip install -e '.[metrics]'     # Prometheus metrics
pip install -e '.[whisper]'     # Whisper transcription
pip install -e '.[vllm]'        # VLLM inference
pip install -e '.[mcp]'         # Model Context Protocol
```

## Section 5: Clarify Run Command (Line 170)

**Current:**

```bash
python -m app.main
```

**Corrected:**

```bash
# Activate virtual environment (sitecustomize.py handles path setup)
source .venv/bin/activate
python -m app.main

# OR use explicit PYTHONPATH
PYTHONPATH=src python -m app.main

# OR use direct path
python src/app/main.py
```

## Section 6: Update API Usage Examples (Line 289)

**Current:**

```python
from app.crew_executor import UltimateDiscordIntelligenceBotCrew

crew = UltimateDiscordIntelligenceBotCrew()
result = crew.crew().kickoff(inputs={"url": "https://youtube.com/watch?v=example"})
```

**Corrected:**

```python
# Recommended: Domain-based import
from domains.orchestration.crew import get_crew, UltimateDiscordIntelligenceBotCrew

# Get crew instance using factory pattern
crew_adapter = get_crew()
crew_obj = crew_adapter.crew()
result = crew_obj.kickoff(inputs={"url": "https://youtube.com/watch?v=example"})

# OR use direct instantiation
crew_instance = UltimateDiscordIntelligenceBotCrew()
result = crew_instance.crew().kickoff(inputs={"url": "https://youtube.com/watch?v=example"})
```

## Additional Notes

1. **Backward Compatibility**: The old import `from app.crew_executor import ...` still works but triggers a `DeprecationWarning`. Existing code will not break.

2. **Agent Count Consistency**: Update all references to agent count throughout documentation:
   - Main README overview
   - Architecture section
   - Core components description
   - Any diagrams or visualizations

3. **Tools Count**: The "111 specialized tools" claim is **accurate** and requires no changes.

4. **Testing**: All setup instructions should be tested to ensure they work on fresh installations.

5. **Documentation Sync**: Ensure `docs/` folder documentation aligns with these README changes.

## Implementation Priority

**High Priority** (User-facing, impacts onboarding):

- Agent count (18 → 31) throughout README
- Setup instructions (pip install command)
- Agent list expansion (add missing 13 agents)

**Medium Priority** (Developer experience):

- Import example updates (deprecated → recommended)
- Run command clarification (PYTHONPATH handling)

**Low Priority** (Polish):

- Cross-reference documentation consistency
- Architecture diagram updates
- Additional code example validation
