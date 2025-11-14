# arXiv Paper Crawler

A Python-based crawler for downloading and processing arXiv papers, including metadata, LaTeX sources, and reference information.

## Features

- Download all versions of arXiv papers
- Extract and clean LaTeX source files (keeps only .tex, .json, .bib files)
- Fetch paper metadata from arXiv API
- Fetch BibTeX citations from extracted sources
- Crawl paper references via Semantic Scholar API
- Multiprocessing support for parallel paper processing
- RAM usage monitoring and statistics collection
- Retry logic for robust API calls
- Organized output structure
- Comprehensive logging to file and console

## Project Structure

```
arXiv_Crawler/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main orchestrator with multiprocessing
│   ├── runner.py            # Worker functions for parallel processing
│   ├── config.py            # Configuration settings
│   ├── logger.py            # Logging configuration
│   ├── arxiv_client.py      # arXiv API client with retry logic
│   ├── scholar_client.py    # Semantic Scholar API client
│   ├── output_manager.py    # File saving utilities
│   ├── processing.py        # Archive processing and cleaning
│   ├── monitor.py           # RAM monitoring utilities
│   ├── utils.py             # Utility functions
│   └── requirements.txt     # Python dependencies
├── 23120260/                # Output directory (based on STUDENT_ID)
│   └── yyyymm-id/           # Paper folders
│       ├── metadata.json    # Paper metadata
│       ├── references.json  # Crawled references
│       └── tex/             # LaTeX sources by version
│           ├── yyyymm-idv1/ # Version 1 (cleaned .tex/.bib/.json only)
│           │   └── references.bib (if found in archive)
│           └── yyyymm-idv2/ # Version 2
├── ram_stats.jsonl          # RAM monitoring data
├── disk_stats.jsonl         # Disk size statistics
└── README.md
└──log.log                   # Log file
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
4. (Optional) Create a `.env` file in the project root for Semantic Scholar API key:
   ```
   SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
   ```

## Usage

### Basic Usage (Single Process)

Run the crawler from the project root:

```bash
python -m src.main
```

### Multiprocessing Mode

Use the `--workers` flag to enable parallel processing:

```bash
python -m src.main --workers 4
```

### Configuration

Edit `src/main.py` to configure:
- ID range to crawl: `generate_id_list("2411", 2499, 2500)`

Edit `src/config.py` to configure:
- `STUDENT_ID`: Your student ID (affects output directory)
- API delays and other settings (see Configuration section below)

## Configuration

Edit `src/config.py` to adjust:
- `STUDENT_ID`: Your student ID (affects output directory)
- `SEMANTIC_SCHOLAR_API_KEY`: Set via environment variable or `.env` file
- `ARXIV_API_DELAY`: Delay between arXiv API calls (default: 0.3s)
- `SEMANTIC_SCHOLAR_API_DELAY`: Delay between Semantic Scholar calls (default: 1.5s)
- `SEMANTIC_SCHOLAR_RATE_LIMIT_WAIT`: Wait time on rate limit (default: 8s)
- `KEEP_FILES`: File extensions to keep from LaTeX sources (default: .json, .bib, .tex)

## Output Format

Each paper is saved in format `yyyymm-id/`:
- `metadata.json`: Paper title, authors, submission date, revised dates, venue
- `references.json`: Crawled references with full metadata
- `tex/yyyymm-idv1/`, `tex/yyyymm-idv2/`, etc.: Cleaned LaTeX sources for each version
  - Contains only .tex, .bib, and .json files (images removed)
  - Any .bib file found is renamed to `references.bib`

Root-level statistics files:
- `ram_stats.jsonl`: RAM usage samples for each processed paper
- `disk_stats.jsonl`: Disk size statistics (tar.gz size, processed size, total directory size)

## API Rate Limiting & Retry Logic

The crawler includes built-in delays and retry logic:
- arXiv API: 0.3s delay between requests, 3 retries with 7s delay on failures
- Semantic Scholar: 1.5s delay between requests, 8s wait on rate limit (429) errors
- Automatic retry on transient network errors
- API key support for Semantic Scholar (higher rate limits)

## Notes

- Large ID ranges may take considerable time (use `--workers` for faster processing)
- Only .tex, .bib, and .json files are kept from LaTeX sources (all other files removed)
- Failed downloads are retried up to 3 times before skipping
- All operations are logged to timestamped log files in `{STUDENT_ID}/logs/`
- Log files include detailed timestamps and error tracking
- RAM usage is monitored and saved to `ram_stats.jsonl` at the repository root
- Multiprocessing mode: each worker respects API delays independently

## Monitoring

The crawler monitors RAM usage during processing:
- Samples are collected every 0.5 seconds
- Statistics are saved per-paper to `ram_stats.jsonl`
- Each entry includes: timestamp, PID, process name, RSS bytes, memory percentages
