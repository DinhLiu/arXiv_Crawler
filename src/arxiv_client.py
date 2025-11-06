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
from .config import ARXIV_API_DELAY


def get_all_versions(base_id: str, paper_dir: str) -> None:
    """
    Find and process all versions of a base arXiv ID.
    
    Args:
        base_id: Base arXiv ID (e.g., "2411.00222")
        paper_dir: Directory to save paper files
    """
    print(f"--- Finding all versions for ID: {base_id} ---")
    client = arxiv.Client()
    
    try:
        search_latest = arxiv.Search(id_list=[base_id])
        latest_paper = next(client.results(search_latest))
    except StopIteration:
        print(f"Notice: Paper not found with ID: {base_id}")
        return
    except Exception as e:
        print(f"Error finding latest version for {base_id}: {e}")
        return

    version_match = re.search(r'v(\d+)$', latest_paper.entry_id)
    max_version = int(version_match.group(1)) if version_match else 1
        
    print(f"Found total of {max_version} versions. Processing each version...")

    for v_num in range(1, max_version + 1):
        version_id = f"{base_id}v{v_num}"
        
        try:
            search_version = arxiv.Search(id_list=[version_id])
            paper = next(client.results(search_version))
            
            print(f"  Processing version: {version_id}")

            output_dir = paper_dir
            output_filename = f"{version_id}.tar.gz"
            tar_path = os.path.join(output_dir, output_filename)

            os.makedirs(output_dir, exist_ok=True)
            
            print(f"  Downloading source to {output_dir}/{output_filename}...")
            paper.download_source(dirpath=output_dir, filename=output_filename)
            print(f"  Download complete for {version_id}!")
            
            version_name = f"v{v_num}"
            final_tex_dir = os.path.join(paper_dir, "tex", version_name)
            processing.process_source_archive(tar_path, final_tex_dir)
            
            print("-" * 20)
            time.sleep(ARXIV_API_DELAY)
            
        except StopIteration:
            print(f"Error: Specific version not found: {version_id}")
        except Exception as e:
            print(f"Error processing {version_id}: {e}")


def get_paper_metadata(base_id: str) -> Optional[Dict[str, any]]:
    """
    Fetch and format metadata for a paper.
    
    Args:
        base_id: Base arXiv ID (e.g., "2411.00222")
        
    Returns:
        Dictionary containing paper metadata, or None if fetch fails
    """
    print(f"  [Meta] Fetching metadata for: {base_id}")
    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[base_id])
        paper = next(client.results(search))

        submission_date = paper.published.isoformat()
        updated_date = paper.updated.isoformat()
        
        revised_dates = []
        if updated_date != submission_date:
            revised_dates.append(updated_date)

        metadata = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "submission_date": submission_date,
            "revised_dates": revised_dates,
            "publication_venue": paper.journal_ref
        }
        return metadata
    except StopIteration:
        print(f"  [Meta] Error: Metadata not found for {base_id}")
        return None
    except Exception as e:
        print(f"  [Meta] Error fetching metadata: {e}")
        return None


def get_bibtex(base_id: str) -> Optional[str]:
    """
    Fetch BibTeX entry for a paper from arXiv.
    
    Args:
        base_id: Base arXiv ID (e.g., "2411.00222")
        
    Returns:
        BibTeX string, or None if fetch fails
    """
    print(f"  [BibTeX] Fetching BibTeX for: {base_id}")
    try:
        url = f"https://arxiv.org/bibtex/{base_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  [BibTeX] Error fetching BibTeX: {e}")
        return None
