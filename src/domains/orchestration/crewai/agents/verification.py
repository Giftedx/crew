"""Verification agents for fact-checking and claim verification.

This module contains agents responsible for verifying claims, fact-checking,
and ensuring content accuracy and reliability.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crewai import Agent
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
from ultimate_discord_intelligence_bot.tools import (
    ClaimVerifierTool,
    ConsistencyCheckTool,
    ContextVerificationTool,
    DeceptionScoringTool,
    FactCheckTool,
    LogicalFallacyTool,
    OutputValidationTool,
    PerspectiveSynthesizerTool,
    SteelmanArgumentTool,
    TrustworthinessTrackerTool,
    TruthScoringTool,
)
from domains.intelligence.analysis import EnhancedAnalysisTool, TextAnalysisTool

_flags = FeatureFlags.from_env()


class VerificationAgents:
    """Verification agents for fact-checking and claim verification."""

    def __init__(self):
        """Initialize verification agents."""
        self.flags = _flags

    def verification_director(self) -> Agent:
        """Fact-checking and verification director."""
        from crewai import Agent

        return Agent(
            role="Verification Director",
            goal="Coordinate comprehensive fact-checking and verification processes with quality assurance.",
            backstory="Expert in fact-checking and verification with focus on accuracy and reliability.",
            tools=[
                FactCheckTool(),
                ClaimVerifierTool(),
                TruthScoringTool(),
                DeceptionScoringTool(),
                ContextVerificationTool(),
                ConsistencyCheckTool(),
                OutputValidationTool(),
                TrustworthinessTrackerTool(),
            ],
            verbose=True,
            allow_delegation=False,
        )

    def fact_checking_specialist(self) -> Agent:
        """Fact-checking specialist."""
        from crewai import Agent

        return Agent(
            role="Fact-Checking Specialist",
            goal="Verify factual claims against reliable sources with comprehensive evidence gathering.",
            backstory="Specialist in fact-checking with expertise in evidence gathering and source verification.",
            tools=[
                FactCheckTool(),
                ClaimVerifierTool(),
                TruthScoringTool(),
                ContextVerificationTool(),
                TrustworthinessTrackerTool(),
            ],
            verbose=True,
            allow_delegation=False,
        )

    def claim_verification_specialist(self) -> Agent:
        """Claim verification specialist."""
        from crewai import Agent

        return Agent(
            role="Claim Verification Specialist",
            goal="Verify extracted claims with high accuracy and comprehensive evidence.",
            backstory="Expert in claim verification with focus on accuracy and evidence quality.",
            tools=[
                ClaimVerifierTool(),
                FactCheckTool(),
                TruthScoringTool(),
                ContextVerificationTool(),
                ConsistencyCheckTool(),
            ],
            verbose=True,
            allow_delegation=False,
        )

    def context_verification_specialist(self) -> Agent:
        """Context verification specialist."""
        from crewai import Agent

        return Agent(
            role="Context Verification Specialist",
            goal="Verify contextual accuracy and citation integrity with comprehensive validation.",
            backstory="Specialist in context verification with expertise in citation and source validation.",
            tools=[
                ContextVerificationTool(),
                FactCheckTool(),
                ClaimVerifierTool(),
                TruthScoringTool(),
                TrustworthinessTrackerTool(),
            ],
            verbose=True,
            allow_delegation=False,
        )

    def deception_detection_specialist(self) -> Agent:
        """Deception detection specialist."""
        from crewai import Agent

        return Agent(
            role="Deception Detection Specialist",
            goal="Detect deceptive content and misleading information with advanced analysis.",
            backstory="Expert in deception detection with focus on identifying misleading content and manipulation.",
            tools=[
                DeceptionScoringTool(),
                LogicalFallacyTool(),
                TruthScoringTool(),
                ContextVerificationTool(),
                FactCheckTool(),
            ],
            verbose=True,
            allow_delegation=False,
        )

    def logical_fallacy_specialist(self) -> Agent:
        """Logical fallacy detection specialist."""
        from crewai import Agent

        return Agent(
            role="Logical Fallacy Specialist",
            goal="Detect logical fallacies and reasoning errors in content with comprehensive analysis.",
            backstory="Specialist in logical fallacy detection with expertise in reasoning analysis and error identification.",
            tools=[LogicalFallacyTool(), SteelmanArgumentTool(), PerspectiveSynthesizerTool(), TextAnalysisTool()],
            verbose=True,
            allow_delegation=False,
        )

    def steelman_argument_specialist(self) -> Agent:
        """Steelman argument specialist."""
        from crewai import Agent

        return Agent(
            role="Steelman Argument Specialist",
            goal="Create the strongest possible version of arguments for comprehensive analysis.",
            backstory="Expert in steelman argumentation with focus on creating robust argument structures.",
            tools=[SteelmanArgumentTool(), PerspectiveSynthesizerTool(), LogicalFallacyTool(), TextAnalysisTool()],
            verbose=True,
            allow_delegation=False,
        )

    def perspective_synthesis_specialist(self) -> Agent:
        """Perspective synthesis specialist."""
        from crewai import Agent

        return Agent(
            role="Perspective Synthesis Specialist",
            goal="Synthesize multiple perspectives into coherent, unified summaries.",
            backstory="Specialist in perspective synthesis with expertise in combining diverse viewpoints.",
            tools=[PerspectiveSynthesizerTool(), SteelmanArgumentTool(), TextAnalysisTool(), EnhancedAnalysisTool()],
            verbose=True,
            allow_delegation=False,
        )
