"""Task modules for the Ultimate Discord Intelligence Bot.

This package contains domain-specific task modules that were extracted
from the monolithic crew.py file to improve maintainability and organization.
"""

from .content_processing import ContentProcessingTasks
from .quality_assurance import QualityAssuranceTasks


__all__ = [
    "ContentProcessingTasks",
    "QualityAssuranceTasks",
]
