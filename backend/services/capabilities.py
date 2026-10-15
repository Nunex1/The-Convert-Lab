from functools import lru_cache
import os
from pathlib import Path
import subprocess
import sys
from backend.config import FORMATS


@lru_cache(maxsize=1)
def available_formats():
    formats = {name: outputs.copy() for name, outputs in FORMATS.items()}
    if os.getenv('ENABLE_XLSB') == '1' and os.getenv('ASPOSE_CELLS_LICENSE_PATH'):
        try:
            result = subprocess.run([sys.executable, '-m', 'backend.converters.xlsx.xlsx_to_xlsb'],
                                    cwd=Path(__file__).resolve().parents[2], timeout=30,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                formats['xlsx'].append('xlsb')
        except (OSError, subprocess.TimeoutExpired):
            pass  # Fail closed. Restart the service after license/config changes.
    return formats
