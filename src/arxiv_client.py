"""
ArXiv API client for fetching papers, metadata, and BibTeX entries.
"""
import arxiv
import time
import re
import os
import requests
from typing import Optional, Dict, List
from . import processing
from . import output_manager
from .config import ARXIV_API_DELAY
from .logger import logger


def get_all_versions(base_id: str, paper_dir: str) -> None:
    """
    Find and process all versions of a base arXiv ID.
    
    Args:
        base_id: Base arXiv ID (e.g., "2411.00222")
        paper_dir: Directory to save paper files
    """
    logger.info(f"--- Finding all versions for ID: {base_id} ---")
    client = arxiv.Client()
    
    try:
        search_latest = arxiv.Search(id_list=[base_id])
        latest_paper = next(client.results(search_latest))
    except StopIteration:
        logger.warning(f"Notice: Paper not found with ID: {base_id}")
        return
    except Exception as e:
        logger.error(f"Error finding latest version for {base_id}: {e}")
        return

    version_match = re.search(r'v(\d+)$', latest_paper.entry_id)
    max_version = int(version_match.group(1)) if version_match else 1
        
    logger.info(f"Found total of {max_version} versions. Processing each version...")

    for v_num in range(1, max_version + 1):
        version_id = f"{base_id}v{v_num}"
        
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
            processing.process_source_archive(tar_path, final_tex_dir)
            
            # Fetch and save BibTeX for this version
            logger.info(f"  Fetching BibTeX for {version_id}...")
            bibtex = get_bibtex(version_id)
            if bibtex:
                bib_path = os.path.join(final_tex_dir, "references.bib")
                output_manager.save_text(bibtex, bib_path)
                logger.info(f"  BibTeX saved to {bib_path}")
            
            logger.info("-" * 20)
            time.sleep(ARXIV_API_DELAY)
            
        except StopIteration:
            logger.error(f"Error: Specific version not found: {version_id}")
        except Exception as e:
            logger.error(f"Error processing {version_id}: {e}")


def get_paper_metadata(base_id: str, fetch_all_versions: bool = True) -> Optional[Dict[str, any]]:
    """
    Fetch and format metadata for a paper.
    
    Args:
        base_id: Base arXiv ID (e.g., "2411.00222")
        fetch_all_versions: If True, fetch dates from all versions. If False, only fetch latest version.
        
    Returns:
        Dictionary containing paper metadata, or None if fetch fails
    """
    logger.info(f"  [Meta] Fetching metadata for: {base_id}")
    try:
        client = arxiv.Client()
        
        # Get the latest version
        search_latest = arxiv.Search(id_list=[base_id])
        latest_paper = next(client.results(search_latest))
        
        paper_title = latest_paper.title
        authors = [author.name for author in latest_paper.authors]
        publication_venue = latest_paper.journal_ref
        
        if not fetch_all_versions:
            # Simple metadata with only published and updated dates
            submission_date = latest_paper.published.isoformat().split('T')[0]
            updated_date = latest_paper.updated.isoformat().split('T')[0]
            
            revised_dates = []
            if updated_date != submission_date:
                revised_dates.append(updated_date)
            
            metadata = {
                "paper_title": paper_title,
                "authors": authors,
                "publication_venue": publication_venue if publication_venue else None,
                "submission_date": submission_date,
                "revised_dates": revised_dates
            }
            return metadata
        
        # Fetch all versions for detailed revision history
        version_match = re.search(r'v(\d+)$', latest_paper.entry_id)
        max_version = int(version_match.group(1)) if version_match else 1
        
        # Collect all revised dates from all versions
        revised_dates = []
        submission_date = None
        
        logger.info(f"  [Meta] Found {max_version} versions, fetching dates for each...")
        
        for v_num in range(1, max_version + 1):
            version_id = f"{base_id}v{v_num}"
            try:
                search_version = arxiv.Search(id_list=[version_id])
                version_paper = next(client.results(search_version))
                
                version_date = version_paper.updated.isoformat().split('T')[0]
                
                # First version is submission date
                if v_num == 1:
                    submission_date = version_date
                else:
                    # Add to revised dates if different from submission
                    if version_date not in revised_dates:
                        revised_dates.append(version_date)
                
                time.sleep(0.5)  # Small delay between version requests
                
            except Exception as e:
                logger.warning(f"  [Meta] Warning: Could not fetch metadata for {version_id}: {e}")
                continue
        
        metadata = {
            "paper_title": paper_title,
            "authors": authors,
            "publication_venue": publication_venue if publication_venue else None,
            "submission_date": submission_date,
            "revised_dates": sorted(revised_dates)
        }
        return metadata
    except StopIteration:
        logger.error(f"  [Meta] Error: Metadata not found for {base_id}")
        return None
    except Exception as e:
        logger.error(f"  [Meta] Error fetching metadata: {e}")
        return None


def get_bibtex(base_id: str) -> Optional[str]:
    """
    Fetch BibTeX entry for a paper from arXiv.
    
    Args:
        base_id: Base arXiv ID (e.g., "2411.00222")
        
    Returns:
        BibTeX string, or None if fetch fails
    """
    logger.info(f"  [BibTeX] Fetching BibTeX for: {base_id}")
    try:
        url = f"https://arxiv.org/bibtex/{base_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"  [BibTeX] Error fetching BibTeX: {e}")
        return None
