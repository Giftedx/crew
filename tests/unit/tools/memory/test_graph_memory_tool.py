from __future__ import annotations
import json
from pathlib import Path
import pytest
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.graph_memory_tool import GraphMemoryTool

def _load_graph(path: str) -> dict:
    with Path(path).open('r', encoding='utf-8') as handle:
        return json.load(handle)

def test_graph_memory_tool_creates_graph(tmp_path: Path) -> None:
    tool = GraphMemoryTool(storage_dir=tmp_path)
    result = tool.run(text='Alice meets Bob in Paris. They plan a research project on climate data.', metadata={'source': 'unit-test'}, tags={'analysis'})
    assert isinstance(result, StepResult)
    assert result.success
    assert result['status'] == 'success'
    assert 'graph_id' in result.data
    storage_path = result.data['storage_path']
    graph = _load_graph(storage_path)
    assert graph['metadata']['namespace'].endswith('graph')
    assert graph['metadata']['node_count'] >= 2
    assert graph['metadata']['edge_count'] >= 1
    assert 'keywords' in graph['metadata']
    assert graph['metadata']['source_metadata']['source'] == 'unit-test'

@pytest.mark.parametrize('payload', ['', '   ', None])
def test_graph_memory_tool_skips_empty_inputs(tmp_path: Path, payload: str | None) -> None:
    tool = GraphMemoryTool(storage_dir=tmp_path)
    result = tool.run(text=payload)
    assert isinstance(result, StepResult)
    assert result['status'] == 'skipped'
    assert result.data.get('reason') == 'empty_text'