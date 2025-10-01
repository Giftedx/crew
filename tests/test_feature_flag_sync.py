import importlib


def test_feature_flags_documentation_in_sync():
    mod = importlib.import_module("scripts.validate_feature_flags")
    assert mod.validate(raise_on_error=False), (
        "Feature flag documentation drift detected (run scripts/validate_feature_flags.py)"
    )
