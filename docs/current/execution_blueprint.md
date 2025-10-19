# Part D: Execution Blueprint for Cursor Auto-Agent and Plan Modes

This document outlines the execution blueprint for implementing the Creator Intelligence system using a multi-agent approach within the Cursor IDE.

## D1. Decomposition into Agents and Responsibilities

The system will be implemented by a crew of specialized agents, each with a distinct role and set of responsibilities. Their capabilities will be enhanced with multi-modal RAG, durable memory, and a self-correction loop.

- **`Research Agent`**:
  - **Responsibility:** Gathers all public metadata, transcripts, chats, and thumbnails for a given topic or URL.
  - **Inputs:** A topic or URL.
  - **Outputs:** A structured JSON object containing all gathered data with provenance.
  - **Tools:** MCP server tools for platform-specific data fetching.

- **`Multimodal Understanding Agent`**:
  - **Responsibility:** Orchestrates the multimodal understanding pipeline (Part A3). Processes the raw data from the `Research Agent` to extract insights.
  - **Inputs:** The JSON object from the `Research Agent`.
  - **Outputs:** Enriched data written to the Knowledge Graph and Vector Database.
  - **Tools:** The full suite of pipeline tools (`Whisper`, `pyannote.audio`, `BERTopic`, etc.).

- **`Knowledge Graph Agent`**:
  - **Responsibility:** Constructs and maintains the KG. Enforces the schema (`schema.yaml`), resolves entities, and aligns events temporally.
  - **Inputs:** Enriched data from the `Multimodal Understanding Agent`.
  - **Outputs:** A consistent and queryable Knowledge Graph.
  - **Tools:** KG database connectors (e.g., for Neo4j or similar).

- **`Feature Specification Agent`**:
  - **Responsibility:** Produces detailed feature specifications (PRDs) as defined in Part B.
  - **Inputs:** A high-level feature request.
  - **Outputs:** A markdown document (`feature_roadmap.md`) with the full specification.
  - **Tools:** Project management and documentation tools.

- **`Evaluation Agent`**:
  - **Responsibility:** Designs and maintains test fixtures, gold sets, and evaluation harnesses. Defines acceptance thresholds and monitors for model drift.
  - **Inputs:** The output of a pipeline stage or feature.
  - **Outputs:** An evaluation report with metrics and pass/fail status.
  - **Tools:** `pytest`, `scikit-learn`, and other evaluation libraries.

- **`Compliance and Policy Agent`**:
  - **Responsibility:** Encodes policy packs and safety rules. Runs as a final check on any content before it is published to ensure it meets brand suitability guidelines.
  - **Inputs:** A piece of content (e.g., a suggested clip).
  - **Outputs:** A compliance report with a pass/fail status and details on any violations.
  - **Tools:** Classification models trained on the policy packs.

- **`Repository Auditor Agent`**:
  - **Responsibility:** Performs the structural audit of the "Giftedx/crew" repository and drafts the 30-60-90 day roadmap.
  - **Inputs:** The URL of the repository.
  - **Outputs:** The audit report and roadmap.
  - **Tools:** `git`, `tokei`, `pipdeptree`, `pyright`.

- **`Release and Observability Agent`**:
  - **Responsibility:** Publishes the final, reviewed artifacts to Discord. Defines SLIs/SLOs and sets up monitoring dashboards.
  - **Inputs:** A finalized artifact (e.g., a report, a set of clips).
  - **Outputs:** A published message on Discord; a configured monitoring dashboard.
  - **Tools:** MCP server tool for Discord, monitoring provider APIs (e.g., Grafana).

- **`Review Agent`**:
  - **Responsibility:** Manages the self-correction loop. Before any artifact is finalized, this agent inspects it against a checklist of acceptance criteria. If criteria are not met, it sends the task back to the appropriate agent with feedback for self-correction.
  - **Inputs:** An artifact pending finalization.
  - **Outputs:** An approval/rejection decision with feedback.
  - **Tools:** Checklist and validation rule engines.

## D2. Tooling, Datasets, and Fixtures

- **Tool Abstractions:**
  - **Platform Data Readers:** A set of MCP server tools that are TOS-compliant and handle the complexities of fetching data from YouTube, Twitch, and X.
  - **AI Service Wrappers:** Wrappers around external APIs for ASR (`Whisper`), OCR (`EasyOCR`), and embedding models (`Sentence-BERT`).
  - **Database Connectors:** Standardized connectors for the KG (e.g., `neo4j-driver`) and the Vector DB (`qdrant-client`).
- **Datasets:**
  - **Stratified Samples:** A collection of 10-20 representative pieces of content from each creator and platform.
  - **Labeled Subsets:** Small, manually labeled datasets for evaluating the performance of diarization, topic segmentation, claim extraction, and safety classification.
- **Fixtures:**
  - **Deterministic Samples:** A small set of input data with known characteristics to be used in unit tests.
  - **Golden Outputs:** A set of pre-generated, validated outputs for regression testing.
  - **Synthetic Edge Cases:** Manually crafted data to test the system's handling of failure modes (e.g., videos with no speech, text with unsupported languages).

## D3. Plan Mode Workflow

This is the authoritative workflow for executing the project.

1. **Initialize Registers:** Create the initial `assumptions.md`, `risks.md`, and `glossary.md` files.
2. **Build KG Schema:** Create the `schema.yaml` file as specified.
3. **Draft Pipeline Architecture:** Create a document detailing the pipeline, including module boundaries, interfaces, and failure modes.
4. **Specify Core Features:** Generate the `feature_roadmap.md` document with all 12 feature PRDs.
5. **Perform Repository Audit:** Execute the audit workflow from Part C1 and create the audit report.
6. **Define Evaluation Plan:** Create a document outlining the evaluation metrics, datasets, and monitoring plan.
7. **Compile Runbooks:** Create a `runbooks/` directory and populate it with runbooks for common failure modes (e.g., ingestion failures, model regressions).
8. **Final Review:** The `Review Agent` executes its checklist against all generated artifacts. Any deviations are flagged and sent back for correction.

## D4. Auto-Agent Execution Safeguards

- **Idempotency:** All tools that perform write operations (e.g., writing to the DB, posting to Discord) will accept an idempotency token to prevent duplicate operations.
- **Bounded Retries:** All external API calls will be wrapped in a retry mechanism (e.g., using the `tenacity` library) with exponential backoff and a maximum of 3 retries.
- **Circuit Breakers:** If an external service fails consistently, a circuit breaker will trip to prevent further calls for a cool-down period.
- **Partial Results Persistence:** For long-running pipelines, partial results will be saved at each stage, allowing the pipeline to be resumed from the point of failure.

## D5. Output Checklists

The `Review Agent` will use the following checklist before finalizing the project:

- [ ] Every entity and relationship in the KG has provenance and confidence scores.
- [ ] Every pipeline stage lists inputs, outputs, acceptance metrics, and failure modes.
- [ ] Every feature PRD includes user stories, UX states, contracts, KPIs, RICE, and cost/complexity.
- [ ] Repository audit contains a structural map, categorization, refactor proposals with tests, and the 30-60-90 plan.
- [ ] Monitoring plan includes drift detectors, alert thresholds, and red/green gates.
- [ ] Runbooks for all critical failure modes are present and actionable.
- [ ] Assumptions and risks registers are complete and prioritized.
