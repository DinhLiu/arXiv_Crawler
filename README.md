# arXiv Paper Crawler

A Python-based crawler for downloading and processing arXiv papers, including metadata, LaTeX sources, and reference information.

## Features

- Download all versions of arXiv papers
- Extract and clean LaTeX source files (removes images)
- Fetch paper metadata from arXiv API
- Fetch BibTeX citations
- Crawl paper references via Semantic Scholar API
- Organized output structure

## Project Structure

```
23120260/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main orchestrator
│   ├── config.py            # Configuration settings
│   ├── arxiv_client.py      # arXiv API client
│   ├── scholar_client.py    # Semantic Scholar API client
│   ├── output_manager.py    # File saving utilities
│   ├── processing.py        # Archive processing
│   └── utils.py             # Utility functions
├── 23120260/                # Output directory
│   └── yyyymm-id/          # Paper folders
│       ├── metadata.json
│       ├── references.bib
│       ├── references.json
│       └── tex/
│           └── v1/         # LaTeX sources by version
└── requirements.txt
```

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```

## Usage

Run the crawler from the project root:

```bash
python -m src.main
```

Edit `src/main.py` to configure:
- ID range to crawl: `generate_id_list("2411", 222, 227)`
- Student ID (changes output directory)

## Configuration

Edit `src/config.py` to adjust:
- `STUDENT_ID`: Your student ID (affects output directory)
- `ARXIV_API_DELAY`: Delay between arXiv API calls (seconds)
- `SEMANTIC_SCHOLAR_API_DELAY`: Delay between Semantic Scholar calls
- `IMAGE_EXTENSIONS`: File types to remove from LaTeX sources

## Output Format

Each paper is saved in format `yyyymm-id/`:
- `metadata.json`: Paper title, authors, dates, venue
- `references.bib`: BibTeX citation
- `references.json`: Crawled references with metadata
- `tex/v1/`, `tex/v2/`, etc.: LaTeX sources for each version

## API Rate Limiting

The crawler includes built-in delays to respect API rate limits:
- arXiv API: 3 seconds between requests
- Semantic Scholar: 3 seconds between requests, 60s wait on 429 errors

## Notes

- Large ID ranges may take considerable time
- Images are automatically removed from LaTeX sources to save space
- Failed downloads are logged but don't stop the crawler
