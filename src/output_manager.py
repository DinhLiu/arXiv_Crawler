"""
File output manager for saving JSON and text files.
"""
import os
import json
from typing import Dict, Any
from .logger import logger


def save_json(data: Dict[str, Any], filepath: str) -> bool:
    """
    Save data as JSON file.
    
    Args:
        data: Dictionary to save as JSON
        filepath: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"  [Save] Saved: {filepath}")
        return True
    except Exception as e:
        logger.error(f"  [Save] Error saving JSON: {e}")
        return False


def save_text(data: str, filepath: str) -> bool:
    """
    Save data as text file (e.g., .bib files).
    
    Args:
        data: Text content to save
        filepath: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data)
        logger.info(f"  [Save] Saved: {filepath}")
        return True
    except Exception as e:
        logger.error(f"  [Save] Error saving text: {e}")
        return False
