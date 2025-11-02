"""Discord Result Persistence - Workflow result persistence utilities.

This module contains Discord result persistence logic extracted from discord_helpers.py,
providing utilities to persist workflow results when Discord sessions close.
"""
from __future__ import annotations
import json
import logging
import time
from pathlib import Path
from typing import Any
logger = logging.getLogger(__name__)

def _get_metrics():
    """Lazy import of metrics to avoid circular dependencies."""
    try:
        from platform.observability.metrics import get_metrics
        return get_metrics()
    except ImportError:

        class NoOpMetrics:

            def counter(self, *args, **kwargs):
                pass

            def histogram(self, *args, **kwargs):
                pass
        return NoOpMetrics()

async def persist_workflow_results(workflow_id: str, results: dict[str, Any], url: str, depth: str, log: logging.Logger | None=None) -> str:
    """Persist workflow results to disk when Discord session closes.

    This allows users to retrieve results even after the interaction timeout.
    Results are stored in data/orphaned_results/ with workflow_id as filename.

    Args:
        workflow_id: Unique identifier for the workflow
        results: Complete workflow results dictionary
        url: Original URL that was analyzed
        depth: Analysis depth used
        log: Optional logger instance

    Returns:
        Path to the persisted result file, or empty string on failure

    Examples:
        >>> path = await persist_workflow_results(
        ...     "abc123", results, "https://example.com", "experimental"
        ... )
        >>> print(path)
        "data/orphaned_results/abc123.json"
    """
    _logger = log or logger
    try:
        results_dir = Path('data/orphaned_results')
        results_dir.mkdir(parents=True, exist_ok=True)
        result_file = results_dir / f'{workflow_id}.json'
        result_data = {'workflow_id': workflow_id, 'timestamp': time.time(), 'url': url, 'depth': depth, 'results': results, 'retrieval_info': {'command': f'/retrieve_results workflow_id:{workflow_id}', 'file_path': str(result_file), 'status': 'session_closed_during_workflow'}}
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2, default=str)
        _logger.info(f'✅ Workflow results persisted to {result_file} (workflow_id={workflow_id})')
        _get_metrics().counter('workflow_results_persisted_total', labels={'reason': 'session_closed', 'depth': depth})
        return str(result_file)
    except Exception as e:
        _logger.error(f'❌ Failed to persist workflow results: {e}', exc_info=True)
        return ''