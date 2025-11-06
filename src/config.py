"""
Configuration settings for the arXiv crawler.
"""
import os

STUDENT_ID = "23120260"
BASE_DATA_DIR = f"./{STUDENT_ID}"

# Semantic Scholar API Key (set your key here or use environment variable)
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

# API rate limiting delays (in seconds)
ARXIV_API_DELAY = 3
SEMANTIC_SCHOLAR_API_DELAY = 1.5
SEMANTIC_SCHOLAR_RATE_LIMIT_WAIT = 15

# File extensions to remove from extracted archives
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.eps', '.svg']

# Ensure base directory exists
os.makedirs(BASE_DATA_DIR, exist_ok=True)
