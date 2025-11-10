"""Monitoring helpers: clean implementation.

This module provides:
- RamSampler: samples the current process memory (RSS) and basic stats at a
  configurable interval and returns a list of samples. Each sample is a dict
  containing pid, ppid, process_name, timestamp, rss_bytes, proc_mem_percent,
  system_mem_percent.
- dir_size(path): compute directory size in bytes.
- append_disk_stats(...): append disk stats to `processing_stats.jsonl` in repo root.
- append_ram_stats(record): append RAM stats record to `ram_stats.jsonl` in repo root.

All writes are append-only JSONL at the repository root (parent of `src`).
"""

from typing import List, Dict, Any, Optional
import os
import time
import threading
import json

try:
    import psutil
except Exception:
    psutil = None


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _append_jsonl(filename: str, obj: Dict[str, Any]):
    path = os.path.join(repo_root(), filename)
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, default=str) + "\n")
    except Exception as e:
        # Log to stderr so we can debug write failures
        import sys
        print(f"[monitor] Failed to append to {path}: {e}", file=sys.stderr)


def dir_size(path: str) -> int:
    total = 0
    if not os.path.exists(path):
        return 0
    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                fp = os.path.join(root, f)
                total += os.path.getsize(fp)
            except Exception:
                continue
    return total


class RamSampler:
    """Sample memory usage for the current process in a background thread.

    Samples are dicts with keys: pid, ppid, process_name, timestamp, rss_bytes,
    proc_mem_percent, system_mem_percent.
    """

    def __init__(self, sample_interval: float = 0.5):
        self.sample_interval = float(sample_interval)
        self._samples: List[Dict[str, Any]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _collect_sample(self) -> Dict[str, Any]:
        ts = time.time()
        pid = os.getpid()
        try:
            proc = psutil.Process(pid) if psutil else None
            name = proc.name() if proc else None
            ppid = proc.ppid() if proc else None
            rss = proc.memory_info().rss if proc else 0
            proc_pct = proc.memory_percent() if proc else 0.0
            sys_pct = psutil.virtual_memory().percent if psutil else 0.0
        except Exception:
            name = None
            ppid = None
            rss = 0
            proc_pct = 0.0
            sys_pct = 0.0

        return {
            "timestamp": ts,
            "pid": pid,
            "ppid": ppid,
            "process_name": name,
            "rss_bytes": rss,
            "proc_mem_percent": proc_pct,
            "system_mem_percent": sys_pct,
        }

    def _sample_loop(self):
        while self._running:
            sample = self._collect_sample()
            self._samples.append(sample)
            time.sleep(self.sample_interval)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def get_samples(self) -> List[Dict[str, Any]]:
        return list(self._samples)

    def save_to_root(self, paper_id: str):
        obj = {
            "type": "ram",
            "paper_id": paper_id,
            "sample_interval": self.sample_interval,
            "sample_count": len(self._samples),
            "samples": self._samples,
            "timestamp": time.time(),
        }
        _append_jsonl("ram_stats.jsonl", obj)


def append_disk_stats(paper_folder_id: str, tar_path: str, size_before: int, images_removed_size: int, size_after: int):
    obj = {
        "type": "disk",
        "paper_folder_id": paper_folder_id,
        "tar_path": tar_path,
        "size_before_bytes": size_before,
        "images_removed_bytes": images_removed_size,
        "size_after_bytes": size_after,
        "timestamp": time.time(),
    }
    _append_jsonl("processing_stats.jsonl", obj)

