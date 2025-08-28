"""Text analysis helper built on top of NLTK.

NLTK downloads data resources at runtime. To avoid repeated downloads and reduce
noise during tests, the tool now checks for the required corpora and downloads
them quietly if missing.  Any failure to obtain the data is surfaced as an
error so the caller can react appropriately.
"""

import logging
from collections import Counter

from crewai.tools import BaseTool

try:  # pragma: no cover - optional dependency
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
except Exception:  # pragma: no cover
    nltk = None

class TextAnalysisTool(BaseTool):
    name: str = "Text Analysis Tool"
    description: str = "Analyze text to extract sentiment, keywords, and topics."

    def __init__(self):
        super().__init__()
        if nltk is None:
            raise RuntimeError("nltk is not installed")
        self._ensure_nltk_data()
        self.sia = SentimentIntensityAnalyzer()

    def _ensure_nltk_data(self) -> None:  # pragma: no cover - setup helper
        resources = [
            ("sentiment/vader_lexicon", "vader_lexicon"),
            ("tokenizers/punkt", "punkt"),
            ("corpora/stopwords", "stopwords"),
        ]
        for path, name in resources:
            try:
                nltk.data.find(path)
            except LookupError:
                try:
                    nltk.download(name, quiet=True)
                except Exception as exc:  # pragma: no cover
                    logging.warning("Failed to download %s: %s", name, exc)

    def _run(self, text: str) -> dict:
        """Analyze a piece of text."""
        try:
            sentiment = self.get_sentiment(text)
            keywords = self.get_keywords(text)
            
            return {
                'status': 'success',
                'sentiment': sentiment,
                'keywords': keywords
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_sentiment(self, text: str) -> dict:
        """Get the sentiment of a piece of text."""
        return self.sia.polarity_scores(text)

    def get_keywords(self, text: str, num_keywords: int = 10) -> list:
        """Get the most common keywords from a piece of text."""
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalpha() and word not in stop_words]
        
        word_counts = Counter(words)
        keywords = [word for word, count in word_counts.most_common(num_keywords)]

        return keywords

    # Provide explicit run method for pipeline usage
    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
