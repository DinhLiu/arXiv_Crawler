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
from .monitor import dir_size, append_disk_stats


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
        
        return {
            "tar_path": tar_path,
            "output_tex_dir": output_tex_dir,
            "size_before": 0,
            "size_after": 0,
            "deleted_bytes": 0,
            "error": "not a valid tar archive"
        }
    
    try:
        with tarfile.open(tar_path) as tar:
            tar.extractall(path=temp_extract_dir)
    except Exception as e:
        logger.error(f"  [Processing] Extraction error: {e}")

        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        
        if os.path.exists(tar_path):
            os.remove(tar_path)

        return {
            "tar_path": tar_path,
            "output_tex_dir": output_tex_dir,
            "size_before": 0,
            "size_after": 0,
            "deleted_bytes": 0,
            "error": str(e)
        }
    
    logger.info("  [Processing] Finding and removing image files...")

    # Record disk usage before removing non-TeX files
    try:
        size_before = dir_size(temp_extract_dir)
    except Exception:
        size_before = 0

    for root, dirs, files in os.walk(temp_extract_dir):
        for file in files:
            if not any(file.lower().endswith(ext) for ext in KEEP_FILES):
                file_path = os.path.join(root, file)

                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"  [Processing] Warning: Could not remove {file_path}: {e}")

    # Record disk usage after removing image files
    try:
        size_after = dir_size(temp_extract_dir)
    except Exception:
        size_after = 0

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

    # Append disk stats into root-level processing_stats.jsonl (do not write into data dirs)
    try:
        paper_folder_id = os.path.basename(output_tex_dir.rstrip(os.path.sep))
        images_removed = max(0, size_before - size_after)
        append_disk_stats(paper_folder_id, tar_path, size_before, images_removed, size_after)
        logger.info(f"  [Stats] Wrote disk stats for {paper_folder_id}")
    except Exception as e:
        logger.warning(f"  [Stats] Failed to write disk stats: {e}")

    if os.path.exists(tar_path):
        os.remove(tar_path)

    logger.info(f"  [Processing] Processing complete. Removed {tar_path}.")

    # Return a dict with disk stats so the caller can also accumulate them in-memory
    disk_stats = {
        "tar_path": tar_path,
        "output_tex_dir": output_tex_dir,
        "size_before": size_before,
        "size_after": size_after,
        "deleted_bytes": max(0, size_before - size_after),
    }

    return disk_stats