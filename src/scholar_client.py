"""
Semantic Scholar API client for fetching paper references.
"""
import time
import requests
from typing import List, Dict
from .config import (
    SEMANTIC_SCHOLAR_API_DELAY,
    SEMANTIC_SCHOLAR_RATE_LIMIT_WAIT,
    SEMANTIC_SCHOLAR_API_KEY
)


API_URL = "https://api.semanticscholar.org/graph/v1/paper/arxiv:"


def fetch_references(arxiv_id: str) -> List[Dict]:
    """
    Fetch references from Semantic Scholar API for a given arXiv ID.
    Uses API key if available for higher rate limits.
    
    Args:
        arxiv_id: arXiv ID to fetch references for
        
    Returns:
        List of reference dictionaries
    """
    url = f"{API_URL}{arxiv_id}"
    params = {
        "fields": "references,references.externalIds,references.title"
    }
    
    # Add API key to headers if available
    headers = {}
    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY
        print(f"  [Scholar] Calling Semantic Scholar API (with API key) for: {arxiv_id}")
    else:
        print(f"  [Scholar] Calling Semantic Scholar API (without key) for: {arxiv_id}")
    
    time.sleep(SEMANTIC_SCHOLAR_API_DELAY)
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 429:
            print(f"  [Scholar] Rate limit reached. Waiting {SEMANTIC_SCHOLAR_RATE_LIMIT_WAIT} seconds...")
            time.sleep(SEMANTIC_SCHOLAR_RATE_LIMIT_WAIT)
            response = requests.get(url, params=params, headers=headers, timeout=30)
        
        response.raise_for_status()
        data = response.json()
        return data.get("references", [])
    except requests.RequestException as e:
        print(f"  [Scholar] Error calling API: {e}")
        return []