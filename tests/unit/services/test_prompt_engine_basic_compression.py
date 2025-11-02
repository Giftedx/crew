from platform.prompts.engine import PromptEngine

def _enable_env(monkeypatch):
    monkeypatch.setenv('ENABLE_PROMPT_COMPRESSION', '1')

def test_blank_lines_collapse(monkeypatch):
    _enable_env(monkeypatch)
    eng = PromptEngine()
    original = 'line1\n\n\nline2\n\n\n\nline3'
    out = eng.optimise(original)
    assert out == 'line1\n\nline2\n\nline3'

def test_dedup_identical_lines(monkeypatch):
    _enable_env(monkeypatch)
    eng = PromptEngine()
    original = 'a\na\na\nb\nb'
    out = eng.optimise(original)
    assert out == 'a\nb'

def test_space_squeeze_preserve_indent(monkeypatch):
    _enable_env(monkeypatch)
    eng = PromptEngine()
    original = 'alpha    beta   gamma\n\tcode    block    stays\n    fourspace    code    too\nend'
    out = eng.optimise(original)
    lines = out.splitlines()
    assert lines[0] == 'alpha beta gamma'
    assert lines[1] == '\tcode    block    stays'
    assert lines[2] == '    fourspace    code    too'
    assert lines[3] == 'end'