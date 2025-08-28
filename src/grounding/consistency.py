from __future__ import annotations

"""Consistency checks for grounded answers to detect contradictions."""

import re
from typing import List, Set, Tuple

from .schema import AnswerContract, Evidence


def check(contract: AnswerContract) -> List[str]:
    """Return a list of contradiction messages."""
    contradictions = []
    
    # Extract statements and sentiments from the answer text
    statements = _extract_statements(contract.answer_text)
    
    # Check for contradictions between evidence sources
    evidence_contradictions = _check_evidence_contradictions(contract.citations)
    contradictions.extend(evidence_contradictions)
    
    # Check for logical inconsistencies in the answer itself
    text_contradictions = _check_text_contradictions(statements)
    contradictions.extend(text_contradictions)
    
    # Check if evidence contradicts the answer
    answer_evidence_contradictions = _check_answer_evidence_alignment(contract.answer_text, contract.citations)
    contradictions.extend(answer_evidence_contradictions)
    
    return contradictions


def _extract_statements(text: str) -> List[str]:
    """Extract individual statements from text."""
    # Split by sentence-ending punctuation
    statements = re.split(r'[.!?]+', text)
    return [s.strip() for s in statements if s.strip() and len(s.strip()) > 3]


def _check_evidence_contradictions(citations: List[Evidence]) -> List[str]:
    """Check for contradictions between different evidence sources."""
    contradictions = []
    
    # Look for opposing statements in evidence quotes
    quotes = [cite.quote for cite in citations if cite.quote]
    
    for i, quote1 in enumerate(quotes):
        for j, quote2 in enumerate(quotes[i+1:], i+1):
            if _are_contradictory(quote1, quote2):
                contradictions.append(
                    f"Evidence sources {i+1} and {j+1} contain contradictory statements: "
                    f"'{quote1[:50]}...' vs '{quote2[:50]}...'"
                )
    
    return contradictions


def _check_text_contradictions(statements: List[str]) -> List[str]:
    """Check for logical contradictions within the answer text itself."""
    contradictions = []
    
    for i, stmt1 in enumerate(statements):
        for j, stmt2 in enumerate(statements[i+1:], i+1):
            if _are_contradictory(stmt1, stmt2):
                contradictions.append(
                    f"Answer contains contradictory statements: "
                    f"'{stmt1}' contradicts '{stmt2}'"
                )
    
    return contradictions


def _check_answer_evidence_alignment(answer_text: str, citations: List[Evidence]) -> List[str]:
    """Check if the answer contradicts the supporting evidence."""
    contradictions = []
    
    # Extract key claims from answer
    answer_lower = answer_text.lower()
    
    # Check each piece of evidence
    for i, citation in enumerate(citations):
        if not citation.quote:
            continue
            
        quote_lower = citation.quote.lower()
        
        # Simple contradiction detection patterns
        if _contains_opposing_claims(answer_lower, quote_lower):
            contradictions.append(
                f"Answer contradicts evidence source {i+1}: "
                f"Answer claims something that evidence source {i+1} disputes"
            )
    
    return contradictions


def _are_contradictory(text1: str, text2: str) -> bool:
    """Simple heuristic to detect if two texts contradict each other."""
    text1_lower = text1.lower()
    text2_lower = text2.lower()
    
    # Look for explicit contradictions like "not", "never", "false" vs affirmative statements
    contradiction_patterns = [
        # Negation patterns
        (r'\b(is|are|was|were)\b', r'\b(is not|are not|was not|were not|isn\'t|aren\'t|wasn\'t|weren\'t)\b'),
        (r'\bdoes\b', r'\bdoes not|doesn\'t\b'),
        (r'\bwill\b', r'\bwill not|won\'t\b'),
        (r'\bcan\b', r'\bcannot|can\'t\b'),
        (r'\btrue\b', r'\bfalse\b'),
        (r'\byes\b', r'\bno\b'),
        (r'\bincreasing?\b', r'\bdecreasing?\b'),
        (r'\bhigher\b', r'\blower\b'),
        (r'\bgood\b', r'\bbad\b'),
    ]
    
    for positive_pattern, negative_pattern in contradiction_patterns:
        if re.search(positive_pattern, text1_lower) and re.search(negative_pattern, text2_lower):
            return True
        if re.search(negative_pattern, text1_lower) and re.search(positive_pattern, text2_lower):
            return True
    
    # Also check for opposing terms directly
    opposing_pairs = [
        ('increasing', 'decreasing'),
        ('rising', 'falling'), 
        ('growing', 'shrinking'),
        ('more', 'less'),
        ('higher', 'lower'),
        ('improving', 'worsening'),
        ('successful', 'failed'),
        ('effective', 'ineffective'),
        ('up', 'down'),
        ('positive', 'negative'),
    ]
    
    for term1, term2 in opposing_pairs:
        if term1 in text1_lower and term2 in text2_lower:
            return True
        if term2 in text1_lower and term1 in text2_lower:
            return True
    
    return False


def _contains_opposing_claims(answer: str, evidence: str) -> bool:
    """Check if answer contains claims that oppose the evidence."""
    # This is a simplified implementation - in production you'd want more sophisticated NLP
    opposing_pairs = [
        ('increasing', 'decreasing'),
        ('rising', 'falling'),
        ('growing', 'shrinking'),
        ('more', 'less'),
        ('higher', 'lower'),
        ('improving', 'worsening'),
        ('successful', 'failed'),
        ('effective', 'ineffective'),
    ]
    
    for term1, term2 in opposing_pairs:
        if term1 in answer and term2 in evidence:
            return True
        if term2 in answer and term1 in evidence:
            return True
    
    return False


__all__ = ["check"]
