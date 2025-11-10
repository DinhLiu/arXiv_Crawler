"""
Main orchestrator for arXiv paper crawling and processing.
"""
import os
import time
from typing import Dict, Any
from .arxiv_client import get_all_versions, get_paper_metadata
from .output_manager import save_json
from .utils import generate_id_list
from .config import BASE_DATA_DIR, ARXIV_API_DELAY
from .logger import logger
from .runner import process_single_paper_task
import argparse
import concurrent.futures


# Note: per-paper processing is implemented in `src/runner.py` as
# `process_single_paper_task` which is picklable for ProcessPoolExecutor on Windows.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="arXiv crawler - optional multiprocessing")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (default: 1)")
    args = parser.parse_args()

    id_list = generate_id_list("2411", 222, 5223)

    logger.info(f"{'='*80}")
    logger.info(f"STARTING CRAWL PROCESS WITH {len(id_list)} IDs")
    logger.info(f"DATA WILL BE SAVED TO: {BASE_DATA_DIR}")
    logger.info(f"Using workers: {args.workers}")
    logger.info(f"{'='*80}\n")

    if args.workers and args.workers > 1:
        logger.info("Running in parallel with ProcessPoolExecutor")
        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as ex:
                # map will preserve order and collect results
                results = list(ex.map(process_single_paper_task, id_list))
                logger.info(f"Processed {len(results)} papers with {args.workers} workers")
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt received, shutting down workers")
        except Exception as e:
            logger.error(f"Error running parallel workers: {e}")
    else:
        for paper_id in id_list:
            result = process_single_paper_task(paper_id)

    logger.info(f"\n{'='*80}")
    logger.info("ALL PROCESSING COMPLETE")
    logger.info(f"{'='*80}")