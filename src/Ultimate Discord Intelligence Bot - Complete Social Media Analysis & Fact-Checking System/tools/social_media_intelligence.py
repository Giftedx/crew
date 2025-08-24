import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import time
import hashlib
import requests
from urllib.parse import urljoin, quote
import re
from crewai_tools import BaseTool

# Social media and web scraping imports
try:
    import praw  # Reddit API
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False
    logging.warning("PRAW not available. Install with: pip install praw")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium not available. Install with: pip install selenium")

try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    logging.warning("Newspaper3k not available. Install with: pip install newspaper3k")

@dataclass
class SocialMediaPost:
    """Represents a social media post"""
    platform: str
    post_id: str
    author: str
    content: str
    url: str
    timestamp: datetime
    engagement_metrics: Dict[str, int]
    metadata: Dict[str, Any] = None
    sentiment_score: float = 0.0
    relevance_score: float = 0.0
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class FactCheckResult:
    """Represents a fact-check result"""
    claim: str
    verdict: str  # true, false, partially_true, unverified
    confidence: float
    sources: List[Dict[str, Any]]
    evidence: List[str]
    reasoning: str
    timestamp: datetime
    fact_checker: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TruthScore:
    """Represents a speaker's truth score"""
    speaker_id: str
    total_claims: int
    true_claims: int
    false_claims: int
    partially_true_claims: int
    unverified_claims: int
    overall_score: float
    confidence: float
    last_updated: datetime
    claim_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.claim_history is None:
            self.claim_history = []

class RedditIntelligenceGatherer:
    """Advanced Reddit intelligence gathering"""
    
    def __init__(self):
        self.reddit_client = None
        self.subreddit_cache = {}
        self._initialize_reddit()
    
    def _initialize_reddit(self):
        """Initialize Reddit client"""
        if not REDDIT_AVAILABLE:
            return
        
        try:
            # Reddit API credentials from environment
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = 'CrewAI Content Monitor 1.0'
            
            if client_id and client_secret:
                self.reddit_client = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                logging.info("Reddit client initialized")
            else:
                logging.warning("Reddit credentials not found in environment")
        
        except Exception as e:
            logging.error(f"Failed to initialize Reddit client: {e}")
    
    async def discover_relevant_subreddits(self, keywords: List[str], topics: List[str]) -> List[Dict[str, Any]]:
        """Discover relevant subreddits based on keywords and topics"""
        
        if not self.reddit_client:
            return []
        
        discovered_subreddits = []
        search_terms = keywords + topics
        
        for term in search_terms[:5]:  # Limit to avoid rate limiting
            try:
                # Search for subreddits
                subreddits = list(self.reddit_client.subreddits.search(term, limit=10))
                
                for subreddit in subreddits:
                    if subreddit.subscribers > 1000:  # Filter small subreddits
                        subreddit_info = {
                            'name': subreddit.display_name,
                            'full_name': subreddit.display_name_prefixed,
                            'subscribers': subreddit.subscribers,
                            'description': subreddit.description[:200] + "..." if len(subreddit.description) > 200 else subreddit.description,
                            'created': datetime.fromtimestamp(subreddit.created_utc),
                            'is_nsfw': subreddit.over18,
                            'search_term': term,
                            'relevance_score': self._calculate_subreddit_relevance(subreddit, search_terms)
                        }
                        discovered_subreddits.append(subreddit_info)
                
                # Add delay to respect rate limits
                await asyncio.sleep(1)
            
            except Exception as e:
                logging.error(f"Error searching subreddits for '{term}': {e}")
                continue
        
        # Remove duplicates and sort by relevance
        unique_subreddits = {}
        for sub in discovered_subreddits:
            if sub['name'] not in unique_subreddits or sub['relevance_score'] > unique_subreddits[sub['name']]['relevance_score']:
                unique_subreddits[sub['name']] = sub
        
        return sorted(unique_subreddits.values(), key=lambda x: x['relevance_score'], reverse=True)[:20]
    
    def _calculate_subreddit_relevance(self, subreddit, search_terms: List[str]) -> float:
        """Calculate relevance score for a subreddit"""
        
        score = 0.0
        text_to_search = f"{subreddit.display_name} {subreddit.description}".lower()
        
        # Check for exact matches
        for term in search_terms:
            if term.lower() in text_to_search:
                score += 1.0
        
        # Subscriber count factor (logarithmic)
        import math
        if subreddit.subscribers > 0:
            score += math.log10(subreddit.subscribers) / 10
        
        # Activity factor (more recent posts = higher score)
        try:
            recent_posts = list(subreddit.new(limit=10))
            if recent_posts:
                latest_post_age = time.time() - recent_posts[0].created_utc
                if latest_post_age < 86400:  # Less than a day
                    score += 0.5
        except:
            pass
        
        return score
    
    async def monitor_subreddits(self, subreddit_names: List[str], keywords: List[str], limit: int = 50) -> List[SocialMediaPost]:
        """Monitor specific subreddits for relevant content"""
        
        if not self.reddit_client:
            return []
        
        posts = []
        
        for subreddit_name in subreddit_names:
            try:
                subreddit = self.reddit_client.subreddit(subreddit_name)
                
                # Get recent posts
                recent_posts = list(subreddit.new(limit=limit))
                
                for post in recent_posts:
                    # Check relevance to keywords
                    post_text = f"{post.title} {post.selftext}".lower()
                    relevance = sum(1 for keyword in keywords if keyword.lower() in post_text)
                    
                    if relevance > 0:  # Only include relevant posts
                        social_post = SocialMediaPost(
                            platform='reddit',
                            post_id=post.id,
                            author=post.author.name if post.author else '[deleted]',
                            content=f"{post.title}\n\n{post.selftext[:500]}",
                            url=f"https://reddit.com{post.permalink}",
                            timestamp=datetime.fromtimestamp(post.created_utc),
                            engagement_metrics={
                                'upvotes': post.ups,
                                'downvotes': post.downs,
                                'score': post.score,
                                'comments': post.num_comments,
                                'upvote_ratio': post.upvote_ratio
                            },
                            relevance_score=relevance / len(keywords),
                            metadata={
                                'subreddit': subreddit_name,
                                'is_self_post': post.is_self,
                                'flair': post.link_flair_text,
                                'gilded': post.gilded,
                                'stickied': post.stickied
                            }
                        )
                        
                        posts.append(social_post)
                
                # Respect rate limits
                await asyncio.sleep(0.5)
            
            except Exception as e:
                logging.error(f"Error monitoring subreddit {subreddit_name}: {e}")
                continue
        
        return sorted(posts, key=lambda x: x.relevance_score, reverse=True)

class CrossPlatformSocialMonitor:
    """Monitor multiple social media platforms"""
    
    def __init__(self):
        self.reddit_gatherer = RedditIntelligenceGatherer()
        self.platform_handlers = {
            'reddit': self._handle_reddit,
            'twitter': self._handle_twitter,
            'youtube_comments': self._handle_youtube_comments,
            'tiktok': self._handle_tiktok,
            'instagram_comments': self._handle_instagram_comments
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    async def monitor_platforms(self, platforms: List[str], keywords: List[str], accounts: List[str] = None, limit: int = 100) -> Dict[str, List[SocialMediaPost]]:
        """Monitor multiple platforms for relevant content"""
        
        results = {}
        
        for platform in platforms:
            if platform in self.platform_handlers:
                try:
                    logging.info(f"Monitoring {platform} for keywords: {keywords}")
                    platform_posts = await self.platform_handlers[platform](keywords, accounts, limit)
                    results[platform] = platform_posts
                    logging.info(f"Found {len(platform_posts)} posts on {platform}")
                except Exception as e:
                    logging.error(f"Error monitoring {platform}: {e}")
                    results[platform] = []
            else:
                logging.warning(f"Platform {platform} not supported")
                results[platform] = []
        
        return results
    
    async def _handle_reddit(self, keywords: List[str], accounts: List[str] = None, limit: int = 100) -> List[SocialMediaPost]:
        """Handle Reddit monitoring"""
        
        # First, discover relevant subreddits
        relevant_subreddits = await self.reddit_gatherer.discover_relevant_subreddits(keywords, [])
        subreddit_names = [sub['name'] for sub in relevant_subreddits[:10]]  # Top 10 most relevant
        
        # Add any manually specified subreddits
        if accounts:
            subreddit_names.extend([acc.replace('r/', '') for acc in accounts if acc.startswith('r/')])
        
        # Monitor the subreddits
        return await self.reddit_gatherer.monitor_subreddits(subreddit_names, keywords, limit // len(subreddit_names) if subreddit_names else limit)
    
    async def _handle_twitter(self, keywords: List[str], accounts: List[str] = None, limit: int = 100) -> List[SocialMediaPost]:
        """Handle Twitter/X monitoring (requires API or scraping)"""
        
        # Placeholder for Twitter monitoring
        # In production, you would use Twitter API v2 or web scraping
        logging.info("Twitter monitoring not implemented (requires Twitter API access)")
        return []
    
    async def _handle_youtube_comments(self, keywords: List[str], accounts: List[str] = None, limit: int = 100) -> List[SocialMediaPost]:
        """Handle YouTube comments monitoring"""
        
        # Placeholder for YouTube comments
        # Would use YouTube Data API
        logging.info("YouTube comments monitoring not implemented (requires YouTube API)")
        return []
    
    async def _handle_tiktok(self, keywords: List[str], accounts: List[str] = None, limit: int = 100) -> List[SocialMediaPost]:
        """Handle TikTok monitoring"""
        
        # Placeholder for TikTok monitoring
        logging.info("TikTok monitoring not implemented (requires TikTok API or scraping)")
        return []
    
    async def _handle_instagram_comments(self, keywords: List[str], accounts: List[str] = None, limit: int = 100) -> List[SocialMediaPost]:
        """Handle Instagram comments monitoring"""
        
        # Placeholder for Instagram comments
        logging.info("Instagram comments monitoring not implemented")
        return []

class EnhancedFactChecker:
    """Enhanced fact-checking with multiple sources and AI verification"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.fact_check_apis = {
            'google_fact_check': self._check_google_fact_check,
            'politifact': self._check_politifact,
            'snopes': self._check_snopes,
            'factcheck_org': self._check_factcheck_org
        }
        self.academic_sources = self._initialize_academic_sources()
    
    def _initialize_academic_sources(self) -> Dict[str, str]:
        """Initialize academic and authoritative sources"""
        return {
            'pubmed': 'https://pubmed.ncbi.nlm.nih.gov/api',
            'google_scholar': 'https://scholar.google.com',
            'semantic_scholar': 'https://api.semanticscholar.org/graph/v1',
            'crossref': 'https://api.crossref.org',
            'arxiv': 'http://export.arxiv.org/api/query'
        }
    
    async def comprehensive_fact_check(self, claims: List[str], context: str = "", include_social_evidence: bool = True) -> List[FactCheckResult]:
        """Perform comprehensive fact-checking with multiple sources"""
        
        fact_check_results = []
        
        for claim in claims:
            logging.info(f"Fact-checking claim: {claim[:100]}...")
            
            try:
                # Step 1: Search existing fact-check databases
                existing_fact_checks = await self._search_fact_check_databases(claim)
                
                # Step 2: Search academic sources
                academic_evidence = await self._search_academic_sources(claim)
                
                # Step 3: Search news sources
                news_evidence = await self._search_news_sources(claim)
                
                # Step 4: Social media evidence (if requested)
                social_evidence = []
                if include_social_evidence:
                    social_evidence = await self._gather_social_media_evidence(claim)
                
                # Step 5: Combine and analyze evidence
                combined_result = await self._analyze_and_synthesize_evidence(
                    claim, context, existing_fact_checks, academic_evidence, 
                    news_evidence, social_evidence
                )
                
                fact_check_results.append(combined_result)
                
                # Rate limiting
                await asyncio.sleep(1)
            
            except Exception as e:
                logging.error(f"Error fact-checking claim '{claim[:50]}...': {e}")
                
                # Create error result
                error_result = FactCheckResult(
                    claim=claim,
                    verdict="unverified",
                    confidence=0.0,
                    sources=[],
                    evidence=[f"Error during fact-checking: {str(e)}"],
                    reasoning="Unable to complete fact-check due to technical error",
                    timestamp=datetime.now(),
                    fact_checker="enhanced_fact_checker"
                )
                fact_check_results.append(error_result)
        
        return fact_check_results
    
    async def _search_fact_check_databases(self, claim: str) -> List[Dict[str, Any]]:
        """Search existing fact-check databases"""
        
        results = []
        
        # Google Fact Check Tools API
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if google_api_key:
            try:
                url = 'https://factchecktools.googleapis.com/v1alpha1/claims:search'
                params = {
                    'key': google_api_key,
                    'query': claim[:100],  # Limit query length
                    'languageCode': 'en'
                }
                
                response = self.session.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for claim_review in data.get('claims', []):
                        for review in claim_review.get('claimReview', []):
                            results.append({
                                'source': 'google_fact_check',
                                'url': review.get('url'),
                                'publisher': review.get('publisher', {}).get('name'),
                                'title': review.get('title'),
                                'rating': review.get('textualRating'),
                                'date': review.get('reviewDate')
                            })
            
            except Exception as e:
                logging.warning(f"Google Fact Check API error: {e}")
        
        return results
    
    async def _search_academic_sources(self, claim: str) -> List[Dict[str, Any]]:
        """Search academic sources for evidence"""
        
        evidence = []
        
        # Semantic Scholar API
        try:
            query = self._extract_keywords_for_search(claim)
            url = f"https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                'query': query,
                'limit': 10,
                'fields': 'title,abstract,authors,year,citationCount,url'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for paper in data.get('data', []):
                    if paper.get('citationCount', 0) > 10:  # Filter for well-cited papers
                        evidence.append({
                            'source': 'academic_paper',
                            'title': paper.get('title'),
                            'abstract': paper.get('abstract', '')[:300],
                            'authors': [author['name'] for author in paper.get('authors', [])],
                            'year': paper.get('year'),
                            'citations': paper.get('citationCount'),
                            'url': paper.get('url'),
                            'relevance_score': self._calculate_relevance(claim, paper.get('title', '') + ' ' + paper.get('abstract', ''))
                        })
        
        except Exception as e:
            logging.warning(f"Academic search error: {e}")
        
        return sorted(evidence, key=lambda x: x['relevance_score'], reverse=True)[:5]
    
    async def _search_news_sources(self, claim: str) -> List[Dict[str, Any]]:
        """Search news sources for evidence"""
        
        evidence = []
        
        # Use Serply News Search if available
        serply_api_key = os.getenv('SERPLY_API_KEY')
        if serply_api_key:
            try:
                url = "https://api.serply.io/v1/news/search"
                headers = {
                    'X-API-KEY': serply_api_key,
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'q': self._extract_keywords_for_search(claim),
                    'location': 'US',
                    'hl': 'en',
                    'num': 10
                }
                
                response = self.session.post(url, headers=headers, json=payload, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('news_results', []):
                        evidence.append({
                            'source': 'news_article',
                            'title': article.get('title'),
                            'snippet': article.get('snippet'),
                            'url': article.get('link'),
                            'publisher': article.get('source'),
                            'date': article.get('date'),
                            'relevance_score': self._calculate_relevance(claim, article.get('title', '') + ' ' + article.get('snippet', ''))
                        })
            
            except Exception as e:
                logging.warning(f"News search error: {e}")
        
        return sorted(evidence, key=lambda x: x['relevance_score'], reverse=True)[:5]
    
    async def _gather_social_media_evidence(self, claim: str) -> List[Dict[str, Any]]:
        """Gather social media evidence and discussions"""
        
        # Extract keywords for social media search
        keywords = self._extract_keywords_for_search(claim).split()[:5]
        
        # Use social media monitor to find relevant discussions
        social_monitor = CrossPlatformSocialMonitor()
        social_results = await social_monitor.monitor_platforms(['reddit'], keywords, limit=20)
        
        evidence = []
        for platform, posts in social_results.items():
            for post in posts[:5]:  # Limit to top 5 posts per platform
                evidence.append({
                    'source': f'social_media_{platform}',
                    'content': post.content[:200],
                    'url': post.url,
                    'author': post.author,
                    'engagement': post.engagement_metrics,
                    'timestamp': post.timestamp.isoformat(),
                    'relevance_score': post.relevance_score
                })
        
        return evidence
    
    async def _analyze_and_synthesize_evidence(self, claim: str, context: str, existing_fact_checks: List[Dict], 
                                             academic_evidence: List[Dict], news_evidence: List[Dict], 
                                             social_evidence: List[Dict]) -> FactCheckResult:
        """Analyze all evidence and synthesize a comprehensive fact-check result"""
        
        # Analyze existing fact-checks
        existing_verdicts = [fc.get('rating', '').lower() for fc in existing_fact_checks if fc.get('rating')]
        
        # Count evidence types
        supporting_evidence = []
        contradicting_evidence = []
        neutral_evidence = []
        
        # Categorize evidence based on content analysis
        all_evidence = academic_evidence + news_evidence
        
        for evidence in all_evidence:
            evidence_text = evidence.get('title', '') + ' ' + evidence.get('abstract', '') + evidence.get('snippet', '')
            
            # Simple sentiment/stance detection (could be enhanced with NLP models)
            if self._supports_claim(claim, evidence_text):
                supporting_evidence.append(evidence)
            elif self._contradicts_claim(claim, evidence_text):
                contradicting_evidence.append(evidence)
            else:
                neutral_evidence.append(evidence)
        
        # Determine verdict based on evidence
        verdict, confidence = self._determine_verdict(existing_verdicts, supporting_evidence, contradicting_evidence)
        
        # Compile sources
        all_sources = existing_fact_checks + supporting_evidence + contradicting_evidence + neutral_evidence
        
        # Generate reasoning
        reasoning = self._generate_reasoning(claim, verdict, existing_verdicts, supporting_evidence, contradicting_evidence, social_evidence)
        
        # Compile evidence statements
        evidence_statements = []
        evidence_statements.extend([f"Existing fact-check: {fc.get('publisher', 'Unknown')} rated this as '{fc.get('rating', 'unknown')}'" for fc in existing_fact_checks[:3]])
        evidence_statements.extend([f"Academic source: {ev.get('title', 'Unknown paper')} ({ev.get('year', 'Unknown year')})" for ev in supporting_evidence[:3]])
        evidence_statements.extend([f"News source: {ev.get('title', 'Unknown article')} from {ev.get('publisher', 'Unknown publisher')}" for ev in news_evidence[:3]])
        
        return FactCheckResult(
            claim=claim,
            verdict=verdict,
            confidence=confidence,
            sources=all_sources[:10],  # Limit sources
            evidence=evidence_statements,
            reasoning=reasoning,
            timestamp=datetime.now(),
            fact_checker="enhanced_fact_checker",
            metadata={
                'context': context,
                'existing_fact_checks': len(existing_fact_checks),
                'academic_sources': len(academic_evidence),
                'news_sources': len(news_evidence),
                'social_evidence': len(social_evidence),
                'supporting_evidence': len(supporting_evidence),
                'contradicting_evidence': len(contradicting_evidence)
            }
        )
    
    def _extract_keywords_for_search(self, claim: str) -> str:
        """Extract keywords from claim for search"""
        
        # Remove common words and focus on key terms
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall', 'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'as', 'but', 'or', 'and', 'nor', 'so', 'yet', 'if', 'then', 'than', 'when', 'where', 'why', 'how', 'what', 'who', 'which', 'whose', 'whom'}
        
        words = re.findall(r'\b\w+\b', claim.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        return ' '.join(keywords[:10])  # Limit to 10 keywords
    
    def _calculate_relevance(self, claim: str, text: str) -> float:
        """Calculate relevance score between claim and text"""
        
        claim_words = set(re.findall(r'\b\w+\b', claim.lower()))
        text_words = set(re.findall(r'\b\w+\b', text.lower()))
        
        if not claim_words or not text_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(claim_words.intersection(text_words))
        union = len(claim_words.union(text_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _supports_claim(self, claim: str, evidence_text: str) -> bool:
        """Determine if evidence supports the claim (simplified)"""
        
        # Look for supporting language patterns
        supporting_patterns = ['confirms', 'supports', 'proves', 'demonstrates', 'shows', 'validates', 'corroborates']
        evidence_lower = evidence_text.lower()
        
        return any(pattern in evidence_lower for pattern in supporting_patterns)
    
    def _contradicts_claim(self, claim: str, evidence_text: str) -> bool:
        """Determine if evidence contradicts the claim (simplified)"""
        
        # Look for contradicting language patterns
        contradicting_patterns = ['refutes', 'disproves', 'contradicts', 'false', 'incorrect', 'debunks', 'myth']
        evidence_lower = evidence_text.lower()
        
        return any(pattern in evidence_lower for pattern in contradicting_patterns)
    
    def _determine_verdict(self, existing_verdicts: List[str], supporting_evidence: List[Dict], 
                          contradicting_evidence: List[Dict]) -> Tuple[str, float]:
        """Determine overall verdict and confidence"""
        
        # Analyze existing verdicts
        false_count = sum(1 for v in existing_verdicts if 'false' in v or 'pants on fire' in v)
        true_count = sum(1 for v in existing_verdicts if 'true' in v and 'false' not in v)
        mixed_count = sum(1 for v in existing_verdicts if 'partly' in v or 'half' in v or 'mixed' in v)
        
        # Weight evidence
        support_score = len(supporting_evidence) * 0.7  # Academic/news evidence weighted
        contradict_score = len(contradicting_evidence) * 0.7
        
        # Factor in existing fact-checks (higher weight)
        support_score += true_count * 1.5
        contradict_score += false_count * 1.5
        
        total_evidence = support_score + contradict_score + mixed_count
        
        if total_evidence == 0:
            return "unverified", 0.1
        
        # Determine verdict
        if support_score > contradict_score * 2:
            verdict = "true"
            confidence = min(0.95, 0.5 + (support_score / total_evidence) * 0.5)
        elif contradict_score > support_score * 2:
            verdict = "false"
            confidence = min(0.95, 0.5 + (contradict_score / total_evidence) * 0.5)
        elif mixed_count > 0 or abs(support_score - contradict_score) < 1:
            verdict = "partially_true"
            confidence = min(0.8, 0.3 + (total_evidence / 10) * 0.3)
        else:
            verdict = "unverified"
            confidence = min(0.6, total_evidence / 20)
        
        return verdict, confidence
    
    def _generate_reasoning(self, claim: str, verdict: str, existing_verdicts: List[str], 
                           supporting_evidence: List[Dict], contradicting_evidence: List[Dict], 
                           social_evidence: List[Dict]) -> str:
        """Generate human-readable reasoning for the verdict"""
        
        reasoning_parts = []
        
        # Summary
        reasoning_parts.append(f"Analysis of the claim: '{claim[:100]}{'...' if len(claim) > 100 else ''}'")
        
        # Existing fact-checks
        if existing_verdicts:
            reasoning_parts.append(f"Found {len(existing_verdicts)} existing fact-check(s) with verdicts: {', '.join(existing_verdicts[:3])}")
        
        # Evidence summary
        if supporting_evidence:
            reasoning_parts.append(f"Found {len(supporting_evidence)} sources that appear to support this claim")
        
        if contradicting_evidence:
            reasoning_parts.append(f"Found {len(contradicting_evidence)} sources that appear to contradict this claim")
        
        # Social media context
        if social_evidence:
            reasoning_parts.append(f"Social media analysis found {len(social_evidence)} relevant discussions")
        
        # Verdict explanation
        verdict_explanations = {
            "true": "The preponderance of evidence supports this claim",
            "false": "The evidence strongly contradicts this claim",
            "partially_true": "The claim contains both accurate and inaccurate elements",
            "unverified": "Insufficient reliable evidence was found to verify this claim"
        }
        
        reasoning_parts.append(f"Conclusion: {verdict_explanations.get(verdict, 'Unknown verdict')}")
        
        return ". ".join(reasoning_parts) + "."

class TruthScoringEngine:
    """Calculate and track truth scores for speakers"""
    
    def __init__(self):
        self.speaker_scores = {}
        self.scoring_algorithm = self._weighted_accuracy_algorithm
    
    def calculate_truth_score(self, speaker_id: str, fact_check_results: List[FactCheckResult]) -> TruthScore:
        """Calculate comprehensive truth score for a speaker"""
        
        # Count verdicts
        true_claims = sum(1 for result in fact_check_results if result.verdict == 'true')
        false_claims = sum(1 for result in fact_check_results if result.verdict == 'false')
        partially_true_claims = sum(1 for result in fact_check_results if result.verdict == 'partially_true')
        unverified_claims = sum(1 for result in fact_check_results if result.verdict == 'unverified')
        total_claims = len(fact_check_results)
        
        if total_claims == 0:
            overall_score = 0.5  # Neutral score with no data
            confidence = 0.0
        else:
            # Weighted scoring algorithm
            overall_score = self.scoring_algorithm(true_claims, false_claims, partially_true_claims, unverified_claims, total_claims, fact_check_results)
            
            # Confidence based on number of claims and their individual confidence scores
            avg_claim_confidence = sum(result.confidence for result in fact_check_results) / total_claims
            sample_size_factor = min(1.0, total_claims / 20)  # Full confidence with 20+ claims
            confidence = avg_claim_confidence * sample_size_factor
        
        # Create claim history
        claim_history = [
            {
                'claim': result.claim,
                'verdict': result.verdict,
                'confidence': result.confidence,
                'timestamp': result.timestamp.isoformat(),
                'sources_count': len(result.sources)
            }
            for result in sorted(fact_check_results, key=lambda x: x.timestamp, reverse=True)
        ]
        
        truth_score = TruthScore(
            speaker_id=speaker_id,
            total_claims=total_claims,
            true_claims=true_claims,
            false_claims=false_claims,
            partially_true_claims=partially_true_claims,
            unverified_claims=unverified_claims,
            overall_score=overall_score,
            confidence=confidence,
            last_updated=datetime.now(),
            claim_history=claim_history
        )
        
        # Store in cache
        self.speaker_scores[speaker_id] = truth_score
        
        return truth_score
    
    def _weighted_accuracy_algorithm(self, true_claims: int, false_claims: int, partially_true_claims: int, 
                                   unverified_claims: int, total_claims: int, fact_check_results: List[FactCheckResult]) -> float:
        """Sophisticated weighted accuracy algorithm"""
        
        # Base scoring
        true_score = true_claims * 1.0
        partially_true_score = partially_true_claims * 0.5
        false_score = false_claims * 0.0
        unverified_score = unverified_claims * 0.3  # Slight penalty for unverified claims
        
        # Weight by confidence scores
        weighted_score = 0.0
        total_weight = 0.0
        
        for result in fact_check_results:
            if result.verdict == 'true':
                weight = result.confidence
                score = 1.0
            elif result.verdict == 'partially_true':
                weight = result.confidence
                score = 0.5
            elif result.verdict == 'false':
                weight = result.confidence
                score = 0.0
            else:  # unverified
                weight = result.confidence * 0.5  # Reduced weight for unverified
                score = 0.3
            
            weighted_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            final_score = weighted_score / total_weight
        else:
            # Fallback to simple calculation
            final_score = (true_score + partially_true_score + unverified_score) / total_claims
        
        # Apply recency weighting (more recent claims have slightly higher weight)
        if len(fact_check_results) > 5:
            recent_results = sorted(fact_check_results, key=lambda x: x.timestamp, reverse=True)[:5]
            recent_score = sum(1.0 if r.verdict == 'true' else 0.5 if r.verdict == 'partially_true' else 0.0 for r in recent_results) / len(recent_results)
            
            # Blend recent performance with overall (80% overall, 20% recent)
            final_score = final_score * 0.8 + recent_score * 0.2
        
        return max(0.0, min(1.0, final_score))  # Ensure score is between 0 and 1
    
    def get_speaker_score(self, speaker_id: str) -> Optional[TruthScore]:
        """Get cached truth score for speaker"""
        return self.speaker_scores.get(speaker_id)
    
    def update_speaker_score(self, speaker_id: str, new_fact_check_results: List[FactCheckResult]) -> TruthScore:
        """Update truth score with new fact-check results"""
        
        # Get existing results if any
        existing_score = self.speaker_scores.get(speaker_id)
        if existing_score:
            # Combine with new results
            all_results = existing_score.claim_history + [
                {
                    'claim': result.claim,
                    'verdict': result.verdict,
                    'confidence': result.confidence,
                    'timestamp': result.timestamp.isoformat(),
                    'sources_count': len(result.sources)
                }
                for result in new_fact_check_results
            ]
            
            # Convert back to FactCheckResult objects for processing
            combined_results = []
            for item in all_results:
                if isinstance(item, dict):
                    # Convert from stored format
                    result = FactCheckResult(
                        claim=item['claim'],
                        verdict=item['verdict'],
                        confidence=item['confidence'],
                        sources=[],
                        evidence=[],
                        reasoning="",
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        fact_checker="cached"
                    )
                    combined_results.append(result)
            
            combined_results.extend(new_fact_check_results)
        else:
            combined_results = new_fact_check_results
        
        return self.calculate_truth_score(speaker_id, combined_results)

# CrewAI Tools Integration
class SocialMediaIntelligenceTool(BaseTool):
    """Social Media Intelligence Tool for CrewAI"""
    
    name: str = "Social Media Intelligence Tool"
    description: str = "Monitor and analyze social media platforms for discussions related to content creators and topics"
    
    def __init__(self):
        super().__init__()
        self.social_monitor = CrossPlatformSocialMonitor()
    
    def _run(self, keywords: List[str], platforms: List[str] = None, accounts: List[str] = None, limit: int = 50) -> str:
        """Monitor social media platforms for relevant content"""
        
        if platforms is None:
            platforms = ['reddit']  # Default to Reddit as it's most accessible
        
        try:
            # Run async monitoring
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self.social_monitor.monitor_platforms(platforms, keywords, accounts, limit)
            )
            
            # Format results
            formatted_results = {
                'timestamp': datetime.now().isoformat(),
                'keywords': keywords,
                'platforms_monitored': platforms,
                'total_posts_found': sum(len(posts) for posts in results.values()),
                'results': {}
            }
            
            for platform, posts in results.items():
                formatted_results['results'][platform] = [
                    {
                        'post_id': post.post_id,
                        'author': post.author,
                        'content': post.content[:200] + "..." if len(post.content) > 200 else post.content,
                        'url': post.url,
                        'timestamp': post.timestamp.isoformat(),
                        'engagement': post.engagement_metrics,
                        'relevance_score': post.relevance_score,
                        'platform': post.platform,
                        'metadata': post.metadata
                    }
                    for post in posts
                ]
            
            return json.dumps(formatted_results, indent=2)
        
        except Exception as e:
            logging.error(f"Social media intelligence error: {e}")
            return json.dumps({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

class EnhancedFactCheckingTool(BaseTool):
    """Enhanced Fact-Checking Tool for CrewAI"""
    
    name: str = "Enhanced Fact-Checking Tool"
    description: str = "Perform comprehensive fact-checking using multiple sources including academic papers, news articles, and social media evidence"
    
    def __init__(self):
        super().__init__()
        self.fact_checker = EnhancedFactChecker()
    
    def _run(self, claims: List[str], context: str = "", include_social_evidence: bool = True) -> str:
        """Perform comprehensive fact-checking"""
        
        try:
            # Run async fact-checking
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self.fact_checker.comprehensive_fact_check(claims, context, include_social_evidence)
            )
            
            # Format results
            formatted_results = {
                'timestamp': datetime.now().isoformat(),
                'total_claims_checked': len(claims),
                'context': context,
                'results': [
                    {
                        'claim': result.claim,
                        'verdict': result.verdict,
                        'confidence': result.confidence,
                        'sources_count': len(result.sources),
                        'evidence': result.evidence,
                        'reasoning': result.reasoning,
                        'timestamp': result.timestamp.isoformat(),
                        'metadata': result.metadata
                    }
                    for result in results
                ]
            }
            
            return json.dumps(formatted_results, indent=2)
        
        except Exception as e:
            logging.error(f"Fact-checking error: {e}")
            return json.dumps({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

class TruthScoringTool(BaseTool):
    """Truth Scoring Tool for CrewAI"""
    
    name: str = "Truth Scoring Tool"
    description: str = "Calculate and track truth scores for speakers based on fact-checking results"
    
    def __init__(self):
        super().__init__()
        self.truth_engine = TruthScoringEngine()
    
    def _run(self, speaker_id: str, fact_check_data: List[Dict[str, Any]]) -> str:
        """Calculate truth score for a speaker"""
        
        try:
            # Convert fact check data to FactCheckResult objects
            fact_check_results = []
            for data in fact_check_data:
                result = FactCheckResult(
                    claim=data.get('claim', ''),
                    verdict=data.get('verdict', 'unverified'),
                    confidence=data.get('confidence', 0.5),
                    sources=data.get('sources', []),
                    evidence=data.get('evidence', []),
                    reasoning=data.get('reasoning', ''),
                    timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                    fact_checker=data.get('fact_checker', 'unknown')
                )
                fact_check_results.append(result)
            
            # Calculate truth score
            truth_score = self.truth_engine.calculate_truth_score(speaker_id, fact_check_results)
            
            # Format result
            result = {
                'speaker_id': truth_score.speaker_id,
                'overall_score': truth_score.overall_score,
                'confidence': truth_score.confidence,
                'total_claims': truth_score.total_claims,
                'breakdown': {
                    'true_claims': truth_score.true_claims,
                    'false_claims': truth_score.false_claims,
                    'partially_true_claims': truth_score.partially_true_claims,
                    'unverified_claims': truth_score.unverified_claims
                },
                'last_updated': truth_score.last_updated.isoformat(),
                'claim_history_count': len(truth_score.claim_history)
            }
            
            return json.dumps(result, indent=2)
        
        except Exception as e:
            logging.error(f"Truth scoring error: {e}")
            return json.dumps({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Test social media intelligence
    social_tool = SocialMediaIntelligenceTool()
    result = social_tool._run(
        keywords=['artificial intelligence', 'AI', 'technology'],
        platforms=['reddit'],
        limit=10
    )
    
    print("Social Media Intelligence Result:")
    print(json.dumps(json.loads(result), indent=2))
    
    # Test fact-checking
    fact_check_tool = EnhancedFactCheckingTool()
    result = fact_check_tool._run(
        claims=['The Earth is round', 'Vaccines cause autism'],
        context="Testing fact-checking capabilities",
        include_social_evidence=False
    )
    
    print("\nFact-Checking Result:")
    print(json.dumps(json.loads(result), indent=2))