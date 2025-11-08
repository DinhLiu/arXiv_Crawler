"""
Archive processing utilities for extracting and cleaning LaTeX source files.
"""
import tarfile
import os
import shutil
from typing import List
from .config import KEEP_FILES
from .logger import logger


def process_source_archive(tar_path: str, output_tex_dir: str) -> bool:
    """
    Extract tar.gz archive, remove image files, and organize into output directory.
    
    Args:
        tar_path: Path to the .tar.gz file
        output_tex_dir: Destination directory for extracted TeX files
        
    Returns:
        True if successful, else False
    """
    temp_extract_dir = os.path.join(os.path.dirname(tar_path), "temp_extract")

    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)

    os.makedirs(temp_extract_dir)

    logger.info(f"  [Processing] Extracting {tar_path} to {temp_extract_dir}")
    
    # Check if file is a valid archive
    if not tarfile.is_tarfile(tar_path):
        logger.warning(f"  [Processing] Warning: {tar_path} is not a valid tar archive")
        
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        
        if os.path.exists(tar_path):
            os.remove(tar_path)
        
        return False
    
    try:
        with tarfile.open(tar_path) as tar:
            tar.extractall(path=temp_extract_dir)
    except Exception as e:
        logger.error(f"  [Processing] Extraction error: {e}")

        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        
        if os.path.exists(tar_path):
            os.remove(tar_path)

        return False
    
    logger.info("  [Processing] Finding and removing image files...")

    for root, dirs, files in os.walk(temp_extract_dir):
        for file in files:
            if not any(file.lower().endswith(ext) for ext in KEEP_FILES):
                file_path = os.path.join(root, file)

                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"  [Processing] Warning: Could not remove {file_path}: {e}")

    logger.info(f"  [Processing] Moving source files to {output_tex_dir}")

    if os.path.exists(output_tex_dir):
        shutil.rmtree(output_tex_dir)
    
    shutil.move(temp_extract_dir, output_tex_dir)

    if os.path.exists(tar_path):
        os.remove(tar_path)

    logger.info(f"  [Processing] Processing complete. Removed {tar_path}.")

    return True