from __future__ import annotations

import time
from typing import Any, Literal, Optional, TypedDict

try:  # Prefer persistent checkpoints when available
    from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    SqliteSaver = None  # type: ignore[assignment]

try:
    from langgraph.checkpoint.memory import MemorySaver  # type: ignore
    from langgraph.graph import END, START, StateGraph  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    MemorySaver = None  # type: ignore[assignment]
    END = START = StateGraph = None  # type: ignore[assignment]

from .step_result import StepResult
from .tools import (
    AudioTranscriptionTool,
    ClaimExtractorTool,
    EnhancedAnalysisTool,
    FactCheckTool,
    MultiPlatformDownloadTool,
)


# Define the state for the mission graph
class MissionState(TypedDict, total=False):
    """Represents the state of the content processing mission."""

    request_url: str
    quality: str
    error: Optional[str]

    # Each major step will populate its result here
    acquisition_result: Optional[StepResult]
    transcription_result: Optional[StepResult]
    analysis_result: Optional[StepResult]
    verification_result: Optional[StepResult]

    # To track which step we are in
    current_step: str


# Node function for the acquisition step
def _run_with_retries(
    fn: Any, *, max_attempts: int = 3, step_name: str = "step"
) -> StepResult:
    """Run a tool or callable with basic retry logic based on StepResult."""
    attempt = 1
    while True:
        try:
            res = fn()
            if isinstance(res, StepResult):
                if res.success:
                    return res
                # Retry if suggested
                if attempt < max_attempts and res.should_retry(attempt):
                    time.sleep(res.get_retry_delay(attempt))
                    attempt += 1
                    continue
                return res
            # If tool returns dict-like, normalize
            return StepResult.from_dict(res)
        except Exception as exc:  # Defensive: wrap into processing error
            if attempt < max_attempts:
                time.sleep(min(2 ** (attempt - 1), 4))
                attempt += 1
                continue
            return StepResult.processing_error(f"{step_name} execution failed: {exc}")


def acquisition_node(state: MissionState) -> dict:
    """Downloads the media for the given URL."""
    print("--- Starting Acquisition Step ---")
    state["current_step"] = "acquisition"

    download_tool = MultiPlatformDownloadTool()

    # The `run` method of the tool handles async execution internally
    result = _run_with_retries(
        lambda: download_tool.run(url=state["request_url"], quality=state["quality"]),
        step_name="acquisition",
    )

    if not result.success:
        print(f"--- Acquisition Failed: {result.error} ---")
        return {"error": result.error, "acquisition_result": result}

    print("--- Acquisition Successful ---")
    return {"acquisition_result": result}


def transcription_node(state: MissionState) -> dict:
    """Transcribes the downloaded media."""
    print("--- Starting Transcription Step ---")
    state["current_step"] = "transcription"

    acquisition_result = state.get("acquisition_result")
    if (
        not acquisition_result
        or not acquisition_result.success
        or not acquisition_result.data
    ):
        error_msg = "Transcription failed: No successful acquisition result found."
        print(f"--- {error_msg} ---")
        return {"error": error_msg}

    # Assuming the file path is in the data of the acquisition result
    # This might need adjustment based on the actual structure of StepResult.data
    file_path = acquisition_result.data.get("file_path")
    if not file_path:
        error_msg = "Transcription failed: File path not found in acquisition result."
        print(f"--- {error_msg} ---")
        return {"error": error_msg}

    transcription_tool = AudioTranscriptionTool()
    result = _run_with_retries(
        lambda: transcription_tool.run(file_path=file_path), step_name="transcription"
    )

    if not result.success:
        print(f"--- Transcription Failed: {result.error} ---")
        return {"error": result.error, "transcription_result": result}

    print("--- Transcription Successful ---")
    return {"transcription_result": result}


def analysis_node(state: MissionState) -> dict:
    """Analyzes the transcript for insights."""
    print("--- Starting Analysis Step ---")
    state["current_step"] = "analysis"

    transcription_result = state.get("transcription_result")
    if (
        not transcription_result
        or not transcription_result.success
        or not transcription_result.data
    ):
        error_msg = "Analysis failed: No successful transcription result found."
        print(f"--- {error_msg} ---")
        return {"error": error_msg}

    # Assuming the transcript text is in the data
    transcript_text = transcription_result.data.get("transcript")
    if not transcript_text:
        error_msg = (
            "Analysis failed: Transcript text not found in transcription result."
        )
        print(f"--- {error_msg} ---")
        return {"error": error_msg}

    analysis_tool = EnhancedAnalysisTool()
    result = _run_with_retries(
        lambda: analysis_tool.run(transcript=transcript_text), step_name="analysis"
    )

    if not result.success:
        print(f"--- Analysis Failed: {result.error} ---")
        return {"error": result.error, "analysis_result": result}

    print("--- Analysis Successful ---")
    return {"analysis_result": result}


def verification_node(state: MissionState) -> dict:
    """Extracts and verifies claims from the analysis."""
    print("--- Starting Verification Step ---")
    state["current_step"] = "verification"

    analysis_result = state.get("analysis_result")
    if not analysis_result or not analysis_result.success or not analysis_result.data:
        error_msg = "Verification failed: No successful analysis result found."
        print(f"--- {error_msg} ---")
        return {"error": error_msg}

    # Assuming the analysis text is in the data
    analysis_text = analysis_result.data.get("analysis_summary")
    if not analysis_text:
        error_msg = (
            "Verification failed: Analysis summary not found in analysis result."
        )
        print(f"--- {error_msg} ---")
        return {"error": error_msg}

    claim_extractor = ClaimExtractorTool()
    fact_checker = FactCheckTool()

    claims_result = _run_with_retries(
        lambda: claim_extractor.run(text=analysis_text), step_name="claim_extract"
    )
    if not claims_result.success or not claims_result.data:
        # If no claims are extracted, we can consider this a success for this path.
        print("--- No claims to verify ---")
        return {"verification_result": StepResult.ok(data={"verified_claims": []})}

    verified_claims = []
    for claim in claims_result.data.get("claims", []):
        fact_check_result = _run_with_retries(
            lambda: fact_checker.run(claim=claim), step_name="fact_check"
        )
        if fact_check_result.success:
            verified_claims.append(fact_check_result.data)

    print("--- Verification Successful ---")
    return {
        "verification_result": StepResult.ok(data={"verified_claims": verified_claims})
    }


# This function decides whether to continue to the next step or end the process
def should_continue(state: MissionState) -> Literal["continue", "end"]:
    """Determines whether to continue the pipeline or end due to an error."""
    if state.get("error"):
        return "end"
    return "continue"


def create_mission_graph():
    """Creates and configures the mission workflow as a state graph.

    Returns the workflow object, or raises if langgraph is unavailable.
    """
    if StateGraph is None:
        raise RuntimeError("langgraph is not installed")
    workflow = StateGraph(MissionState)

    # Add nodes for each stage of the pipeline
    workflow.add_node("acquisition", acquisition_node)
    workflow.add_node("transcription", transcription_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("verification", verification_node)

    # Define the edges that connect the nodes
    workflow.add_edge(START, "acquisition")

    # Add a conditional edge from acquisition to transcription or end
    workflow.add_conditional_edges(
        "acquisition", should_continue, {"continue": "transcription", "end": END}
    )

    workflow.add_conditional_edges(
        "transcription", should_continue, {"continue": "analysis", "end": END}
    )

    workflow.add_conditional_edges(
        "analysis", should_continue, {"continue": "verification", "end": END}
    )
    workflow.add_edge("verification", END)

    return workflow


def compile_mission_graph():
    """Compiles the mission graph with checkpointing enabled."""
    graph = create_mission_graph()

    # Prefer persistent, fallback to in-memory
    if SqliteSaver is not None:
        try:
            checkpointer = SqliteSaver("crew_data/langgraph/checkpoints.sqlite")  # type: ignore[call-arg]
        except Exception:
            checkpointer = MemorySaver()
    else:
        checkpointer = MemorySaver()

    # `compile()` returns a runnable application
    return graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    # This section is for demonstration and testing purposes.
    mission_graph_app = compile_mission_graph()

    # To run the graph:
    # config = {"configurable": {"thread_id": "mission_123"}}
    # inputs = {"request_url": "http://example.com/video.mp4", "quality": "1080p"}
    # for event in mission_graph_app.stream(inputs, config=config):
    #     print(event)

    print("LangGraph pipeline structure defined. Node implementation is next.")
