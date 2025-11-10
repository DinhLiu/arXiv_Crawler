"""
ArXiv API client for fetching papers and metadata.

(Đã sửa đổi để tự động thử lại (retry) nếu gặp lỗi API)
"""
import arxiv
import time
import re
import os
from typing import Optional, Dict, List
from . import processing
from .config import ARXIV_API_DELAY
from .logger import logger

# --- CẤU HÌNH THỬ LẠI (RETRY) ---
MAX_RETRIES = 3  # Thử lại tối đa 3 lần
RETRY_DELAY = 7  # Chờ 5 giây giữa các lần thử
# ---------------------------------


def get_all_versions(base_id: str, paper_dir: str) -> List[dict]:
    """
    Find and process all versions of a base arXiv ID. Returns a list of disk-stat
    dictionaries (one per processed version) so callers can aggregate stats.
    """
    logger.info(f"--- Finding all versions for ID: {base_id} ---")
    client = arxiv.Client()
    
    latest_paper = None
    
    # --- THỬ LẠI (RETRY) CHO VIỆC TÌM KIẾM BAN ĐẦU ---
    for attempt in range(MAX_RETRIES):
        try:
            search_latest = arxiv.Search(id_list=[base_id])
            latest_paper = next(client.results(search_latest))
            break  # Thành công, thoát khỏi vòng lặp thử lại
        except StopIteration:
            logger.warning(f"Notice: Paper not found with ID: {base_id}")
            return []  # Không tìm thấy, không cần thử lại
        except Exception as e:
            logger.warning(f"  [Retry {attempt + 1}/{MAX_RETRIES}] Error finding latest version for {base_id}: {e}. Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            
    if latest_paper is None:
        logger.error(f"Failed to find latest version for {base_id} after {MAX_RETRIES} attempts. Skipping.")
        return []
    # --------------------------------------------------

    version_match = re.search(r'v(\d+)$', latest_paper.entry_id)
    max_version = int(version_match.group(1)) if version_match else 1

    logger.info(f"Found total of {max_version} versions. Processing each version...")

    disk_stats_list: List[dict] = []
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

                logger.info(f"  Downloading source to {output_dir}/{output_filename}...")
                paper.download_source(dirpath=output_dir, filename=output_filename)
                logger.info(f"  Download complete for {version_id}!")

                # Format version folder name
                version_folder = f"{base_id.replace('.', '-')}v{v_num}"
                final_tex_dir = os.path.join(paper_dir, "tex", version_folder)
                
                try:
                    stats = processing.process_source_archive(tar_path, final_tex_dir)
                    if isinstance(stats, dict):
                        disk_stats_list.append(stats)
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
                time.sleep(RETRY_DELAY)
        
        if not success:
            logger.error(f"Failed to process {version_id} after {MAX_RETRIES} attempts. Skipping.")
        # ------------------------------------------------

    return disk_stats_list


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