import importlib
import os

# Ensure full mode for helper availability
os.environ.pop("LIGHTWEIGHT_IMPORT", None)
mod = importlib.import_module("scripts.start_full_bot")


def test_fallacy_detection_multiple():
    text = "Everyone knows the world will end if we allow this; you're stupid if you disagree because I said so."
    detected = mod._detect_fallacies(text.lower())
    labels = {d[0] for d in detected}
    # Expect at least popularity, slippery slope, ad hominem, appeal to authority
    assert any("Popularity" in label for label in labels)
    assert any("Slippery" in label for label in labels)
    assert any("Ad Hominem" in label for label in labels)
    assert any("Authority" in label for label in labels)


def test_fallacy_detection_none():
    text = "This argument presents evidence and counterpoints clearly without rhetorical manipulation."
    detected = mod._detect_fallacies(text.lower())
    assert detected == []


def test_fallacy_database_shape():
    db = mod._fallacy_database()
    # Basic shape: keys are tuples, values are (label, explanation)
    assert all(isinstance(k, tuple) for k in db)
    assert all(isinstance(v, tuple) and len(v) == 2 for v in db.values())
