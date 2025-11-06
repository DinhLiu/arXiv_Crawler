"""
Main orchestrator for arXiv paper crawling and processing.
"""
import os
import time
from typing import Dict, Any
from .arxiv_client import get_all_versions, get_paper_metadata, get_bibtex
from .scholar_client import fetch_references
from .output_manager import save_json, save_text
from .utils import generate_id_list, format_paper_folder_id
from .config import BASE_DATA_DIR, ARXIV_API_DELAY


def process_paper_references(paper_id: str, paper_dir: str) -> Dict[str, Any]:
    """
    Fetch and process references from Semantic Scholar for a given paper.
    
    Args:
        paper_id: Base arXiv ID
        paper_dir: Directory to save references
        
    Returns:
        Dictionary of processed references
    """
    print(f"\n--- Fetching Semantic Scholar references for {paper_id} ---")
    raw_references = fetch_references(paper_id)
    crawled_references = {}

    if raw_references:
        print(f"Found {len(raw_references)} raw references. Filtering and crawling...")
        
        for ref in raw_references:
            if ref and ref.get('externalIds') and ref['externalIds'].get('ArXiv'):
                ref_arxiv_id = ref['externalIds']['ArXiv'].split('v')[0]
                
                if ref_arxiv_id == paper_id or ref_arxiv_id in crawled_references:
                    continue
                
                try:
                    ref_metadata = get_paper_metadata(ref_arxiv_id)
                    
                    if ref_metadata:
                        ref_folder_id = format_paper_folder_id(ref_arxiv_id)
                        crawled_references[ref_folder_id] = ref_metadata
                        time.sleep(ARXIV_API_DELAY)
                except Exception as e:
                    print(f"  [Ref] Error processing reference {ref_arxiv_id}: {e}")
                    continue
        
        save_json(crawled_references, os.path.join(paper_dir, "references.json"))
        print(f"Processed and saved {len(crawled_references)} references.")
    else:
        print(f"No references found for {paper_id}.")
    
    return crawled_references


def process_single_paper(paper_id: str) -> bool:
    """
    Complete processing pipeline for a single paper.
    
    Args:
        paper_id: Base arXiv ID to process
        
    Returns:
        True if processing was successful, False otherwise
    """
    print(f"\n===== PROCESSING PAPER: {paper_id} =====")
    
    paper_folder_id = format_paper_folder_id(paper_id)
    paper_dir = os.path.join(BASE_DATA_DIR, paper_folder_id)
    
    get_all_versions(paper_id, paper_dir)

    print("\n--- Fetching Metadata (for metadata.json) ---")
    metadata = get_paper_metadata(paper_id)
    if metadata:
        save_json(metadata, os.path.join(paper_dir, "metadata.json"))

    print("\n--- Fetching BibTeX (for references.bib) ---")
    bibtex = get_bibtex(paper_id)
    if bibtex:
        save_text(bibtex, os.path.join(paper_dir, "references.bib"))

    process_paper_references(paper_id, paper_dir)

    print(f"===== COMPLETED PAPER: {paper_id} =====")
    time.sleep(ARXIV_API_DELAY)
    return True
if __name__ == "__main__":
    id_list = generate_id_list("2411", 245, 5221)
    
    print(f"--- STARTING CRAWL PROCESS WITH {len(id_list)} IDs ---")
    print(f"--- DATA WILL BE SAVED TO: {BASE_DATA_DIR} ---")

    for paper_id in id_list:
        process_single_paper(paper_id)
    
    print("\n--- ALL PROCESSING COMPLETE ---")