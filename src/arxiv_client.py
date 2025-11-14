"""
ArXiv API client for fetching papers and metadata with retry logic.
"""
import arxiv
import requests
import time
import re
import os
from typing import Optional, Dict, List, Any

from . import processing
from .config import ARXIV_API_DELAY
from .logger import logger

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 7


def get_all_versions(base_id: str, paper_dir: str) -> Dict[str, Any]:
    """
    Find and process all versions of a base arXiv ID.
    
    Args:
        base_id: The base arXiv ID (e.g., "2411.00222")
        paper_dir: Directory to save downloaded files
        
    Returns:
        True if successful, False otherwise
    """
    if not base_id or base_id is None:
        logger.error(f"get_all_versions called with invalid base_id: {base_id}")
        return False
    
    logger.info(f"--- Finding all versions for ID: {base_id} ---")
    client = arxiv.Client()
    latest_paper = None
    
    # Retry logic for finding the latest version
    for attempt in range(MAX_RETRIES):
        try:
            search_latest = arxiv.Search(id_list=[base_id])
            latest_paper = next(client.results(search_latest))
            break
        except StopIteration:
            logger.warning(f"Notice: Paper not found with ID: {base_id}")
            return {"success": False, "error": "paper not found"}
        except Exception as e:
            logger.warning(f"  [Retry {attempt + 1}/{MAX_RETRIES}] Error finding latest version for {base_id}: {e}. Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            
    if latest_paper is None:
        logger.error(f"Failed to find latest version for {base_id} after {MAX_RETRIES} attempts. Skipping.")
        return {"success": False, "error": "failed to find latest version"}

    version_match = re.search(r'v(\d+)$', latest_paper.entry_id)
    max_version = int(version_match.group(1)) if version_match else 1

    logger.info(f"Found total of {max_version} versions. Processing each version...")

    # Track processing statistics
    version_stats = []

    # Process each version
    for v_num in range(1, max_version + 1):
        version_id = f"{base_id}v{v_num}"
        success = False

        # --- THỬ LẠI (RETRY) CHO TỪNG PHIÊN BẢN ---
        for attempt in range(MAX_RETRIES):
            try:
                search_version = arxiv.Search(id_list=[version_id])
                paper = next(client.results(search_version))

                logger.info(f"  Processing version: {version_id}")

                output_dir = paper_dir
                output_filename = f"{version_id}.tar.gz"
                tar_path = os.path.join(output_dir, output_filename)

                os.makedirs(output_dir, exist_ok=True)

                # Workaround for arxiv library bug: pdf_url property sometimes returns None
                # even when PDF link exists in links list
                if paper.pdf_url is not None:
                    # Normal case: use library's download method
                    logger.info(f"  Downloading source to {output_dir}/{output_filename}...")
                    paper.download_source(dirpath=output_dir, filename=output_filename)
                    logger.info(f"  Download complete for {version_id}!")
                else:
                    # Workaround: manually construct source URL from links
                    logger.info(f"  [Workaround] pdf_url is None, manually constructing source URL...")
                    pdf_link = None
                    for link in paper.links:
                        if '/pdf/' in link.href:
                            pdf_link = link.href
                            break
                    
                    if not pdf_link:
                        logger.warning(f"  [Skip] No PDF link found for {version_id}")
                        break
                    
                    source_url = pdf_link.replace('/pdf/', '/src/')
                    logger.info(f"  Downloading source from {source_url} to {tar_path}...")
                    
                    import requests
                    response = requests.get(source_url, stream=True)
                    
                    if response.status_code == 200:
                        with open(tar_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        logger.info(f"  Download complete for {version_id}!")
                    else:
                        logger.warning(f"  [Skip] Failed to download source for {version_id}: HTTP {response.status_code}")
                        break

                # Format version folder name
                version_folder = f"{str(base_id).replace('.', '-')}v{v_num}"
                final_tex_dir = os.path.join(paper_dir, "tex", version_folder)
                
                try:
                    result = processing.process_source_archive(tar_path, final_tex_dir)
                    if result.get("success"):
                        version_stats.append({
                            "version": v_num,
                            "version_id": version_id,
                            "tar_size_bytes": result.get("tar_size_bytes", 0),
                            "final_size_bytes": result.get("final_size_bytes", 0)
                        })
                except Exception as e:
                    logger.warning(f"  [Processing] Warning: process_source_archive failed for {version_id}: {e}")

                logger.info("-" * 20)
                time.sleep(ARXIV_API_DELAY)
                
                success = True
                break  # Thành công, thoát khỏi vòng lặp thử lại
                
            except StopIteration:
                logger.error(f"Error: Specific version not found: {version_id}")
                break  # Không tìm thấy, không cần thử lại
            except Exception as e:
                logger.warning(f"  [Retry {attempt + 1}/{MAX_RETRIES}] Error processing {version_id}: {e}. Retrying in {RETRY_DELAY}s...")
                if attempt == 0:  # Log full traceback only on first error
                    logger.exception(f"  Full traceback for {version_id}:")
                time.sleep(RETRY_DELAY)
        
        if not success:
            logger.error(f"Failed to process {version_id} after {MAX_RETRIES} attempts. Skipping.")

    return {
        "success": True,
        "total_versions": max_version,
        "version_stats": version_stats
    }


def get_paper_metadata(base_id: str, fetch_all_versions: bool = True) -> Optional[Dict[str, any]]:
    """
    Fetch and format metadata for a paper.
    """
    logger.info(f"  [Meta] Fetching metadata for: {base_id}")
    
    latest_paper = None
    client = arxiv.Client()

    # --- THỬ LẠI (RETRY) CHO VIỆC TÌM KIẾM METADATA BAN ĐẦU ---
    for attempt in range(MAX_RETRIES):
        try:
            search_latest = arxiv.Search(id_list=[base_id])
            latest_paper = next(client.results(search_latest))
            break  # Thành công
        except StopIteration:
            logger.error(f"  [Meta] Error: Metadata not found for {base_id}")
            return None  # Không tìm thấy, không thử lại
        except Exception as e:
            logger.warning(f"  [Meta] [Retry {attempt + 1}/{MAX_RETRIES}] Error fetching metadata for {base_id}: {e}. Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)

    if latest_paper is None:
        logger.error(f"  [Meta] Failed to fetch metadata for {base_id} after {MAX_RETRIES} attempts.")
        return None
    # --------------------------------------------------------

    # (Phần code bên dưới này là logic gốc của bạn)
    paper_title = latest_paper.title
    authors = [author.name for author in latest_paper.authors]
    publication_venue = latest_paper.journal_ref

    if not fetch_all_versions:
        # ... (logic gốc của bạn) ...
        submission_date = latest_paper.published.isoformat().split('T')[0]
        updated_date = latest_paper.updated.isoformat().split('T')[0]
        revised_dates = []
        if updated_date != submission_date:
            revised_dates.append(updated_date)
        metadata = {
            "paper_title": paper_title, "authors": authors,
            "publication_venue": publication_venue if publication_venue else None,
            "submission_date": submission_date, "revised_dates": revised_dates
        }
        return metadata

    # Fetch all versions for detailed revision history
    version_match = re.search(r'v(\d+)$', latest_paper.entry_id)
    max_version = int(version_match.group(1)) if version_match else 1

    revised_dates = []
    submission_date = None
    logger.info(f"  [Meta] Found {max_version} versions, fetching dates for each...")

    for v_num in range(1, max_version + 1):
        version_id = f"{base_id}v{v_num}"
        version_paper = None
        
        # --- THỬ LẠI (RETRY) CHO VIỆC LẤY METADATA TỪNG PHIÊN BẢN ---
        for attempt in range(MAX_RETRIES):
            try:
                search_version = arxiv.Search(id_list=[version_id])
                version_paper = next(client.results(search_version))
                break # Thành công
            except Exception as e:
                logger.warning(f"  [Meta] [Retry {attempt + 1}/{MAX_RETRIES}] Warning: Could not fetch metadata for {version_id}: {e}. Retrying...")
                time.sleep(RETRY_DELAY)
        
        if version_paper is None:
            logger.error(f"  [Meta] Failed to fetch metadata for {version_id} after {MAX_RETRIES} attempts. Skipping version.")
            continue # Bỏ qua phiên bản này
        # ------------------------------------------------------------

        version_date = version_paper.updated.isoformat().split('T')[0]
        
        if v_num == 1:
            submission_date = version_date
        else:
            if version_date not in revised_dates:
                revised_dates.append(version_date)
        
        time.sleep(0.5)  # Small delay between version requests

    metadata = {
        "paper_title": paper_title,
        "authors": authors,
        "publication_venue": publication_venue if publication_venue else None,
        "submission_date": submission_date,
        "revised_dates": sorted(revised_dates)
    }
    return metadata