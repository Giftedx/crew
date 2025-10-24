#!/usr/bin/env python3
"""Configuration validation script to check docs against actual YAML files."""

import sys
from pathlib import Path
from typing import Any

import yaml


def load_yaml_file(file_path: Path) -> dict[Any, Any]:
    """Load and parse a YAML file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return {}


def compare_structures(actual: dict[Any, Any], expected_keys: list[str], file_name: str) -> list[str]:
    """Compare actual YAML structure with expected keys from documentation."""
    issues = []

    actual_keys = {str(k) for k in actual}
    expected_key_set = set(expected_keys)

    # Check for missing documented keys
    missing_keys = expected_key_set - actual_keys
    if missing_keys:
        issues.append(f"Missing keys in {file_name}: {sorted(missing_keys)}")

    # Check for undocumented keys
    extra_keys = actual_keys - expected_key_set
    if extra_keys:
        issues.append(f"Undocumented keys in {file_name}: {sorted(extra_keys)}")

    return issues


def validate_security_config():
    """Validate security.yaml against documentation."""
    print("🔍 Validating security.yaml...")

    actual = load_yaml_file(Path("/home/crew/config/security.yaml"))

    # Expected structure based on documentation and actual config
    expected_keys = [
        "role_permissions",
        "rate_limits",
        "moderation",
        "network",
        "webhooks",
        "secrets",
        "abac",
        "feature_flags",
    ]

    issues = compare_structures(actual, expected_keys, "security.yaml")

    # Check role_permissions structure
    if "role_permissions" in actual:
        expected_roles = ["viewer", "user", "moderator", "ops", "admin"]
        actual_roles = set(actual["role_permissions"].keys())
        expected_role_set = set(expected_roles)

        missing_roles = expected_role_set - actual_roles
        if missing_roles:
            issues.append(f"Missing roles in security.yaml: {sorted(missing_roles)}")

    # Note: burst_allowance is documented as not implemented, so don't flag it as missing

    return issues


def validate_policy_config():
    """Validate policy.yaml against documentation."""
    print("🔍 Validating policy.yaml...")

    actual = load_yaml_file(Path("/home/crew/config/policy.yaml"))

    # Expected structure based on ACTUAL implementation
    expected_keys = [
        "allowed_sources",
        "forbidden_types",
        "pii_types",
        "masks",
        "storage",
        "consent",
        "per_command",
    ]

    issues = compare_structures(actual, expected_keys, "policy.yaml")

    # Check for expected PII types (using actual structure)
    if "pii_types" in actual:
        expected_pii_types = [
            "email",
            "phone",
            "ip",
            "credit_like",
            "gov_id_like",
            "address_like",
            "geo_exact",
        ]
        actual_pii_types = set(actual["pii_types"].keys())
        expected_pii_set = set(expected_pii_types)
        missing_types = expected_pii_set - actual_pii_types
        if missing_types:
            issues.append(f"Missing PII types: {sorted(missing_types)}")

    # Check masks structure matches pii_types
    if "masks" in actual and "pii_types" in actual:
        pii_types = set(actual["pii_types"].keys())
        mask_keys = set(actual["masks"].keys())
        if pii_types != mask_keys:
            issues.append(f"Masks don't match PII types. PII: {sorted(pii_types)}, Masks: {sorted(mask_keys)}")

    return issues


def validate_archive_routes_config():
    """Validate archive_routes.yaml against documentation."""
    print("🔍 Validating archive_routes.yaml...")

    actual = load_yaml_file(Path("/home/crew/config/archive_routes.yaml"))

    # Expected structure based on ACTUAL implementation
    expected_keys = ["defaults", "routes", "per_tenant_overrides"]

    issues = compare_structures(actual, expected_keys, "archive_routes.yaml")

    # Check defaults structure
    if "defaults" in actual:
        defaults = actual["defaults"]
        expected_default_keys = ["max_retries", "chunking"]
        actual_default_keys = set(defaults.keys())
        expected_default_set = set(expected_default_keys)
        missing_defaults = expected_default_set - actual_default_keys
        if missing_defaults:
            issues.append(f"Missing keys in defaults: {sorted(missing_defaults)}")

    # Check routes structure
    if "routes" in actual:
        routes = actual["routes"]
        expected_route_types = ["images", "videos", "audio", "docs", "blobs"]
        actual_route_types = set(routes.keys())
        expected_route_set = set(expected_route_types)
        missing_routes = expected_route_set - actual_route_types
        if missing_routes:
            issues.append(f"Missing route types: {sorted(missing_routes)}")

    return issues


def validate_ingest_config():
    """Validate ingest.yaml against documentation."""
    print("🔍 Validating ingest.yaml...")

    actual = load_yaml_file(Path("/home/crew/config/ingest.yaml"))

    # Check if documented structure matches actual
    if "youtube" in actual and "twitch" in actual:
        print("✅ Basic platform sections found")

    if "chunk" in actual:
        chunk_config = actual["chunk"]
        if "max_chars" in chunk_config and "overlap" in chunk_config:
            print("✅ Chunking configuration found")
        else:
            return ["Missing chunk configuration parameters"]

    return []


def validate_other_configs():
    """Check for configs that exist but may not be documented."""
    config_dir = Path("/home/crew/config")
    actual_files = [f.name for f in config_dir.glob("*.yaml")]

    documented_files = [
        "archive_routes.yaml",
        "grounding.yaml",
        "ingest.yaml",
        "profiles.yaml",
        "policy.yaml",
        "poller.yaml",
        "retry.yaml",
        "deprecations.yaml",
        "security.yaml",
    ]

    issues = []

    # Check for undocumented files
    undocumented = set(actual_files) - set(documented_files)
    if undocumented:
        issues.append(f"Config files not mentioned in documentation: {sorted(undocumented)}")

    # Check for documented files that don't exist
    missing = set(documented_files) - set(actual_files)
    if missing:
        issues.append(f"Documented config files that don't exist: {sorted(missing)}")

    return issues


def validate_tenant_configs():
    """Validate tenant configuration structure."""
    print("🔍 Validating tenant configurations...")

    tenant_dir = Path("/home/crew/tenants/default")
    if not tenant_dir.exists():
        return ["Tenant directory /home/crew/tenants/default does not exist"]

    expected_tenant_files = [
        "tenant.yaml",
        "routing.yaml",
        "budgets.yaml",
        "policy_overrides.yaml",
    ]
    actual_tenant_files = [f.name for f in tenant_dir.glob("*.yaml")]

    issues = []

    missing_tenant_files = set(expected_tenant_files) - set(actual_tenant_files)
    if missing_tenant_files:
        issues.append(f"Missing tenant config files: {sorted(missing_tenant_files)}")

    # Load and check tenant configs that exist
    for file_name in expected_tenant_files:
        file_path = tenant_dir / file_name
        if file_path.exists():
            config = load_yaml_file(file_path)
            if not config:
                issues.append(f"Empty or invalid YAML in {file_name}")

    return issues


def main():
    """Main validation function."""
    print("🔧 Configuration Documentation Validation")
    print("=" * 50)

    all_issues = []

    # Validate individual config files
    all_issues.extend(validate_security_config())
    all_issues.extend(validate_policy_config())
    all_issues.extend(validate_archive_routes_config())
    all_issues.extend(validate_ingest_config())
    all_issues.extend(validate_other_configs())
    all_issues.extend(validate_tenant_configs())

    # Report results
    print("\n" + "=" * 50)
    if all_issues:
        print(f"❌ Found {len(all_issues)} configuration issues:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")

        print("\n💡 Summary: Documentation needs significant updates to match actual configuration structure.")
    else:
        print("✅ All configuration documentation appears accurate!")

    return len(all_issues)


if __name__ == "__main__":
    issue_count = main()
    sys.exit(1 if issue_count > 0 else 0)
