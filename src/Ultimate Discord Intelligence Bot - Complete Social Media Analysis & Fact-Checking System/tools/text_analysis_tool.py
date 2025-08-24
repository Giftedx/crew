from crewai_tools import BaseTool
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter

class TextAnalysisTool(BaseTool):
    name: str = "Text Analysis Tool"
    description: str = "Analyze text to extract sentiment, keywords, and topics."

    def __init__(self):
        super().__init__()
        # Download necessary NLTK data
        nltk.download('vader_lexicon')
        nltk.download('punkt')
        nltk.download('stopwords')
        self.sia = SentimentIntensityAnalyzer()

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
