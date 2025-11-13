"""
Configuration settings for the arXiv crawler.
"""
import os
import dotenv

dotenv.load_dotenv()

STUDENT_ID = "23120260"
BASE_DATA_DIR = f"./{STUDENT_ID}"

# Semantic Scholar API Key (set your key here or use environment variable)
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

# API rate limiting delays (in seconds)
ARXIV_API_DELAY = 0.3
SEMANTIC_SCHOLAR_API_DELAY = 1.5
SEMANTIC_SCHOLAR_RATE_LIMIT_WAIT = 8

# File extensions to remove from extracted archives
KEEP_FILES = ['.json', '.bib', '.tex']

# Ensure base directory exists
os.makedirs(BASE_DATA_DIR, exist_ok=True)
