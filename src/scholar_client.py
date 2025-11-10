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
from .logger import logger


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
    headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY
        logger.info(f"  [Scholar] Calling Semantic Scholar API (with API key) for: {arxiv_id}")
    else:
        logger.info(f"  [Scholar] Calling Semantic Scholar API (without key) for: {arxiv_id}")

    time.sleep(SEMANTIC_SCHOLAR_API_DELAY)
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 429:
            logger.warning(f"  [Scholar] Rate limit reached. Waiting {SEMANTIC_SCHOLAR_RATE_LIMIT_WAIT} seconds...")
            time.sleep(SEMANTIC_SCHOLAR_RATE_LIMIT_WAIT)
            response = requests.get(url, params=params, headers=headers, timeout=30)
        
        response.raise_for_status()
        data = response.json()
        return data.get("references", [])
    except requests.RequestException as e:
        logger.error(f"  [Scholar] Error calling API: {e}")
        return []