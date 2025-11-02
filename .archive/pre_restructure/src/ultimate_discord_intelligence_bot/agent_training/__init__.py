"""
Agent Training Module for CrewAI Enhancement

This module provides comprehensive training and enhancement capabilities for CrewAI agents,
including synthetic data generation, performance monitoring, and autonomous learning.

Key Components:
- SyntheticDataGenerator: Creates training examples with varying complexity
- AgentTrainingCoordinator: Enhances agent configurations with improved prompting
- AgentPerformanceMonitor: Tracks real-world performance and provides feedback
- CrewAITrainingOrchestrator: Orchestrates the complete enhancement pipeline

Usage:
    from agent_training.orchestrator import CrewAITrainingOrchestrator

    orchestrator = CrewAITrainingOrchestrator()
    results = orchestrator.run_complete_enhancement()
"""

from .coordinator import AgentTrainingCoordinator
from .orchestrator import CrewAITrainingOrchestrator
from .performance_monitor import AgentPerformanceMonitor
from .synthetic_data_generator import SyntheticDataGenerator


__all__ = [
    "AgentPerformanceMonitor",
    "AgentTrainingCoordinator",
    "CrewAITrainingOrchestrator",
    "SyntheticDataGenerator",
]

__version__ = "1.0.0"
