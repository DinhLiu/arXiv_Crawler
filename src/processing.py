"""
Archive processing utilities for extracting and cleaning LaTeX source files.
"""
import tarfile
import os
import shutil
import json
from typing import List, Dict, Any
from .config import KEEP_FILES
from .logger import logger


def process_source_archive(tar_path: str, output_tex_dir: str) -> Dict[str, Any]:
    """
    Extract tar.gz archive, remove image files, and organize into output directory.
    
    Args:
        tar_path: Path to the .tar.gz file
        output_tex_dir: Destination directory for extracted TeX files
        
    Returns:
        True if successful, else False
    """
    temp_extract_dir = os.path.join(os.path.dirname(tar_path), "temp_extract")
    
    # Get tar.gz size before processing
    tar_size_bytes = 0
    try:
        if os.path.exists(tar_path):
            tar_size_bytes = os.path.getsize(tar_path)
            logger.info(f"  [Processing] Tar.gz size: {tar_size_bytes:,} bytes ({tar_size_bytes / 1024 / 1024:.2f} MB)")
    except Exception as e:
        logger.warning(f"  [Processing] Could not get tar size: {e}")

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
        
        return {"error": "not a valid tar archive"}
    
    try:
        with tarfile.open(tar_path) as tar:
            tar.extractall(path=temp_extract_dir)
    except Exception as e:
        logger.error(f"  [Processing] Extraction error: {e}")

        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        
        if os.path.exists(tar_path):
            os.remove(tar_path)

        return {"error": str(e)}
    
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

    # Rename any .bib file to references.bib (use the first one found if multiple exist)
    try:
        bib_files = []
        for root, dirs, files in os.walk(output_tex_dir):
            for file in files:
                if file.lower().endswith('.bib'):
                    bib_files.append(os.path.join(root, file))
        
        if bib_files:
            # Use the first .bib file found
            source_bib = bib_files[0]
            target_bib = os.path.join(output_tex_dir, "references.bib")
            
            # If source is not already named references.bib, rename it
            if source_bib != target_bib:
                # If references.bib already exists, remove it first
                if os.path.exists(target_bib):
                    os.remove(target_bib)
                shutil.move(source_bib, target_bib)
                logger.info(f"  [BibTeX] Renamed {os.path.basename(source_bib)} to references.bib")
            else:
                logger.info(f"  [BibTeX] references.bib already exists")
        else:
            logger.info(f"  [BibTeX] No .bib file found in archive")
    except Exception as e:
        logger.warning(f"  [BibTeX] Failed to rename .bib file: {e}")

    if os.path.exists(tar_path):
        os.remove(tar_path)

    # Calculate final directory size
    final_size_bytes = 0
    try:
        for root, dirs, files in os.walk(output_tex_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    final_size_bytes += os.path.getsize(file_path)
        logger.info(f"  [Processing] Final size: {final_size_bytes:,} bytes ({final_size_bytes / 1024 / 1024:.2f} MB)")
        if tar_size_bytes > 0:
            reduction_pct = ((tar_size_bytes - final_size_bytes) / tar_size_bytes) * 100
            logger.info(f"  [Processing] Size reduction: {reduction_pct:.1f}%")
    except Exception as e:
        logger.warning(f"  [Processing] Could not calculate final size: {e}")

    logger.info(f"  [Processing] Processing complete. Removed {tar_path}.")

    return {
        "success": True,
        "tar_size_bytes": tar_size_bytes,
        "final_size_bytes": final_size_bytes
    }