"""
Worker functions for processing a single paper. Kept in a separate module so it can be
imported by worker processes (pickleable on Windows).
"""
import os
import time
from typing import Dict, Any

from .arxiv_client import get_all_versions, get_paper_metadata
from .scholar_client import fetch_references
from .output_manager import save_json
from .utils import format_paper_folder_id
from .config import BASE_DATA_DIR, ARXIV_API_DELAY
from .logger import logger
from .monitor import RamSampler, save_disk_stats, get_directory_size
from .monitor import repo_root


def process_paper_references(paper_id: str, paper_dir: str) -> Dict[str, Any]:
    """
    Fetch and process references from Semantic Scholar for a given paper.
    Kept as a helper inside this module so workers have everything they need.
    """
    logger.info(f"\n--- Fetching Semantic Scholar references for {paper_id} ---")
    raw_references = fetch_references(paper_id)
    crawled_references = {}

    if raw_references:
        logger.info(f"Found {len(raw_references)} raw references. Filtering and crawling...")

        for ref in raw_references:
            if ref and ref.get('externalIds') and ref['externalIds'].get('ArXiv'):
                ref_arxiv_id = ref['externalIds']['ArXiv'].split('v')[0]

                if ref_arxiv_id == paper_id or ref_arxiv_id in crawled_references:
                    continue

                try:
                    ref_metadata = get_paper_metadata(ref_arxiv_id, fetch_all_versions=False)

                    if ref_metadata:
                        ref_folder_id = format_paper_folder_id(ref_arxiv_id)
                        crawled_references[ref_folder_id] = ref_metadata
                        time.sleep(ARXIV_API_DELAY)
                except Exception as e:
                    logger.error(f"  [Ref] Error processing reference {ref_arxiv_id}: {e}")
                    continue

        save_json(crawled_references, os.path.join(paper_dir, "references.json"))
        logger.info(f"Processed and saved {len(crawled_references)} references.")
    else:
        logger.info(f"No references found for {paper_id}.")

    return crawled_references


def process_single_paper_task(paper_id: str) -> dict:
    """
    Complete processing pipeline for a single paper.

    This function is intentionally top-level so it can be pickled and used by
    ProcessPoolExecutor on Windows.
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"PROCESSING PAPER: {paper_id}")
    logger.info(f"{'='*80}")

    # Defensive: ensure paper_id is valid
    if not paper_id:
        logger.error("process_single_paper_task called with empty paper_id")
        return {"paper_id": paper_id, "success": False, "error": "empty paper_id"}

    paper_folder_id = format_paper_folder_id(paper_id)
    paper_dir = os.path.join(BASE_DATA_DIR, paper_folder_id)
    os.makedirs(paper_dir, exist_ok=True)

    # Start RAM monitoring
    sampler = RamSampler(sample_interval=0.5)
    sampler.start()

    # Download and process all versions
    processing_stats = {}
    try:
        result = get_all_versions(paper_id, paper_dir)
        if not result.get("success"):
            raise Exception(result.get("error", "Failed to download versions"))
        processing_stats = result
    except Exception as e:
        logger.error(f"Error downloading versions for {paper_id}: {e}")
        sampler.stop()
        try:
            sampler.save_to_root(paper_folder_id)
        except Exception:
            pass
        return {
            "paper_id": paper_id,
            "success": False,
            "error": str(e)
        }

    logger.info("\n--- Fetching Metadata (for metadata.json) ---")
    try:
        metadata = get_paper_metadata(paper_id)
        if metadata:
            save_json(metadata, os.path.join(paper_dir, "metadata.json"))
    except Exception as e:
        logger.error(f"Error fetching metadata for {paper_id}: {e}")

    try:
        process_paper_references(paper_id, paper_dir)
    except Exception as e:
        logger.error(f"Error processing references for {paper_id}: {e}")

    # Stop sampler and save RAM timeseries
    try:
        sampler.stop()
        # save RAM timeseries to root-level JSONL instead of per-paper data dir
        sampler.save_to_root(paper_folder_id)
    except Exception as e:
        logger.warning(f"Failed to save RAM stats: {e}")

    # Save processing statistics
    try:
        total_tar_size = sum(v.get("tar_size_bytes", 0) for v in processing_stats.get("version_stats", []))
        total_final_size = sum(v.get("final_size_bytes", 0) for v in processing_stats.get("version_stats", []))
        paper_dir_size = get_directory_size(paper_dir)
        
        stats = {
            "total_versions": processing_stats.get("total_versions", 0),
            "total_tar_size_bytes": total_tar_size,
            "total_processed_size_bytes": total_final_size,
            "paper_directory_size_bytes": paper_dir_size,
            "version_details": processing_stats.get("version_stats", [])
        }
        save_disk_stats(paper_folder_id, stats)
        logger.info(f"  [Stats] Saved disk statistics: tar={total_tar_size:,} bytes, processed={total_final_size:,} bytes, total_dir={paper_dir_size:,} bytes")
    except Exception as e:
        logger.warning(f"Failed to save processing stats: {e}")

    logger.info(f"{'='*80}")
    logger.info(f"COMPLETED PAPER: {paper_id}")
    logger.info(f"{'='*80}\n")

    # Sleep to respect arXiv API delay, note: when running parallel workers this is per-worker.
    time.sleep(ARXIV_API_DELAY)

    return {
        "paper_id": paper_id,
        "success": True
    }
