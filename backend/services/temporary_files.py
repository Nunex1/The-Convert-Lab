import shutil
import time
from contextlib import suppress
from pathlib import Path
from backend.config import TEMP_ROOT


def cleanup_job(path: Path):
    shutil.rmtree(path, ignore_errors=True)


def cleanup_stale():
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    for path in TEMP_ROOT.glob('job-*'):
        # A response may finish and delete its job between discovery and stat.
        with suppress(FileNotFoundError):
            if path.is_dir() and not path.is_symlink() and time.time() - path.stat().st_mtime > 3600:
                cleanup_job(path)
