from __future__ import annotations
from typing import TYPE_CHECKING
import yaml
from platform.llm.providers.openrouter import OpenRouterService
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry
if TYPE_CHECKING:
    from pathlib import Path

def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding='utf-8')

def test_tenant_provider_prefs_and_models(tmp_path: Path) -> None:
    acme = tmp_path / 'acme'
    _write_yaml(acme / 'tenant.yaml', {'name': 'Acme', 'workspaces': {'main': {}}})
    _write_yaml(acme / 'routing.yaml', {'providers': ['openrouter', 'openai'], 'models': {'default': 'openai/gpt-3.5', 'analysis': 'openai/gpt-4'}, 'allowed_models': ['gpt-3.5', 'gpt-4']})
    reg = TenantRegistry(tmp_path)
    reg.load()
    svc = OpenRouterService(api_key='', tenant_registry=reg)
    with with_tenant(TenantContext('acme', 'main')):
        res = svc.route('ping', task_type='analysis')
    assert res['status'] == 'success'
    assert res['model'].startswith('openai/gpt-4')
    assert res['provider'].get('order') == ['openrouter', 'openai']