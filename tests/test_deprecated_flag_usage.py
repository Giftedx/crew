import importlib


def test_no_stray_deprecated_retry_flag():
    mod = importlib.import_module("scripts.validate_deprecated_flags")
    assert mod.validate(raise_on_error=False), "Stray deprecated flag usage (ENABLE_ANALYSIS_HTTP_RETRY) detected"
