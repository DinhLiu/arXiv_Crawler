"""
Utility functions for ID generation and formatting.
"""
from typing import List


def generate_id_list(month_prefix: str, start_id: int, end_id: int) -> List[str]:
    """
    Generate a list of arXiv IDs from parameters.
    
    Args:
        month_prefix: Month prefix (e.g., "2411")
        start_id: Starting ID number
        end_id: Ending ID number
        
    Returns:
        List of arXiv IDs
    """
    id_list = []
    for i in range(start_id, end_id + 1):
        arxiv_id = f"{month_prefix}.{i:05d}"
        id_list.append(arxiv_id)
    print(f'id_list: {id_list}')
    return id_list


def format_paper_folder_id(paper_id: str) -> str:
    """
    Format paper ID into folder name format: "yyyymm-id"
    Handles both modern format (2411.00222) and old format (math/0610595)
    
    Args:
        paper_id: Full arXiv ID (e.g., "2411.00222" or "math/0610595")
        
    Returns:
        Formatted folder ID (e.g., "2411-00222" or "math-0610595")
    """
    # Defensive: if paper_id is None or not a string, return a placeholder
    if paper_id is None:
        return "unknown-id"

    # Handle old format with category prefix (e.g., math/0610595)
    if '/' in paper_id:
        category, number = paper_id.split('/')
        return f"{category}-{number}"
    
    # Handle modern format (e.g., 2411.00222)
    parts = paper_id.split('.')
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    
    # Fallback for unexpected formats
    return paper_id.replace('.', '-').replace('/', '-')
