from __future__ import annotations

"""Enhanced topic/keyword extraction utilities with proper NLP."""

import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Set


@dataclass
class TopicResult:
    topics: List[str]
    entities: List[str]
    hashtags: List[str]
    keywords: List[str]
    phrases: List[str]
    
    
# Common stop words to filter out
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
    'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
    'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these', 
    'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
    'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
    'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
    'that', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
    'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'can', 'shall', 'get', 'got',
    'say', 'said', 'go', 'went', 'come', 'came', 'see', 'saw', 'know', 'knew'
}

# Common entity patterns
ENTITY_PATTERNS = [
    r'\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Proper names
    r'\b[A-Z]{2,}\b',  # Acronyms
    r'\b(?:CEO|CTO|CFO|VP|President|Director)\s+[A-Z][a-z]+ [A-Z][a-z]+\b',  # Titles
    r'\b@[A-Za-z0-9_]+\b',  # Social handles
]

# Topic categories with keywords
TOPIC_CATEGORIES = {
    'technology': {
        'ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning',
        'neural network', 'algorithm', 'data science', 'blockchain', 'crypto',
        'cryptocurrency', 'bitcoin', 'software', 'programming', 'coding', 'api',
        'cloud', 'aws', 'azure', 'google cloud', 'database', 'sql', 'nosql'
    },
    'politics': {
        'election', 'vote', 'voting', 'democracy', 'republican', 'democrat',
        'conservative', 'liberal', 'policy', 'government', 'congress', 'senate',
        'president', 'politician', 'campaign', 'poll', 'ballot', 'legislation'
    },
    'business': {
        'startup', 'company', 'corporation', 'business', 'enterprise', 'market',
        'stock', 'investment', 'investor', 'funding', 'revenue', 'profit', 'loss',
        'ceo', 'cto', 'cfo', 'ipo', 'acquisition', 'merger', 'venture capital'
    },
    'science': {
        'research', 'study', 'experiment', 'hypothesis', 'theory', 'discovery',
        'scientist', 'laboratory', 'data', 'analysis', 'peer review', 'journal',
        'publication', 'medicine', 'biology', 'chemistry', 'physics'
    },
    'entertainment': {
        'movie', 'film', 'tv', 'television', 'show', 'series', 'actor', 'actress',
        'director', 'producer', 'netflix', 'youtube', 'streaming', 'music',
        'song', 'album', 'artist', 'celebrity', 'game', 'gaming'
    },
    'sports': {
        'football', 'basketball', 'baseball', 'soccer', 'tennis', 'golf',
        'olympics', 'championship', 'tournament', 'team', 'player', 'coach',
        'season', 'league', 'nfl', 'nba', 'mlb', 'nhl', 'fifa'
    }
}


def extract(text: str) -> TopicResult:
    """Extract topics, entities, keywords, and phrases from text.
    
    This enhanced implementation performs:
    - Hashtag extraction
    - Entity recognition using patterns
    - Keyword extraction with stop word filtering
    - Topic categorization
    - Multi-word phrase detection
    """
    if not text or not text.strip():
        return TopicResult(topics=[], entities=[], hashtags=[], keywords=[], phrases=[])
    
    text_lower = text.lower()
    
    # Extract hashtags
    hashtags = list(set(re.findall(r'#[A-Za-z0-9_]+', text)))
    hashtags = sorted([h.lower() for h in hashtags])
    
    # Extract entities using patterns
    entities = []
    for pattern in ENTITY_PATTERNS:
        matches = re.findall(pattern, text)
        entities.extend(matches)
    
    # Remove duplicates and social handles from entities
    entities = sorted(list(set([e for e in entities if not e.startswith('@')])))
    
    # Extract keywords (filter stop words and short words)
    word_tokens = re.findall(r'\b[a-zA-Z]+\b', text_lower)
    keywords = [
        word for word in word_tokens 
        if len(word) > 2 and word not in STOP_WORDS
    ]
    
    # Count keyword frequency and get top keywords
    keyword_counts = Counter(keywords)
    top_keywords = [word for word, count in keyword_counts.most_common(20)]
    
    # Extract multi-word phrases (2-3 words)
    phrases = []
    words = text_lower.split()
    for i in range(len(words) - 1):
        # Two-word phrases
        if i < len(words) - 1:
            phrase = f"{words[i]} {words[i+1]}"
            if (words[i] not in STOP_WORDS and words[i+1] not in STOP_WORDS 
                and len(words[i]) > 2 and len(words[i+1]) > 2):
                phrases.append(phrase)
        
        # Three-word phrases
        if i < len(words) - 2:
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            if (words[i] not in STOP_WORDS and words[i+2] not in STOP_WORDS
                and len(phrase) > 10):  # Avoid very short phrases
                phrases.append(phrase)
    
    # Remove duplicates and get top phrases
    phrase_counts = Counter(phrases)
    top_phrases = [phrase for phrase, count in phrase_counts.most_common(10)]
    
    # Categorize topics
    detected_topics = set()
    for category, category_keywords in TOPIC_CATEGORIES.items():
        # Check if any category keywords appear in text
        for keyword in category_keywords:
            if keyword in text_lower:
                detected_topics.add(category)
                break
    
    # Also add high-frequency keywords as topics
    for keyword in top_keywords[:10]:
        if len(keyword) > 4:  # Only longer, more meaningful words
            detected_topics.add(keyword)
    
    return TopicResult(
        topics=sorted(list(detected_topics)),
        entities=entities,
        hashtags=hashtags,
        keywords=top_keywords,
        phrases=top_phrases
    )
