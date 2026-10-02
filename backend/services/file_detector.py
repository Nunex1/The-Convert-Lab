import re
import unicodedata
from pathlib import PurePosixPath
from backend.config import FORMATS
from backend.services.errors import ConversionError


def detect_extension(filename: str) -> str:
    extension = PurePosixPath(filename.replace('\\', '/')).suffix.lower().lstrip('.')
    if extension not in FORMATS:
        raise ConversionError('Este formato ainda não é suportado. Use PDF, DOCX, MHT ou MHTML.')
    return extension


def output_name(filename: str, extension: str) -> str:
    basename = PurePosixPath(filename.replace('\\', '/')).stem
    basename = unicodedata.normalize('NFC', basename)
    basename = re.sub(r'[\x00-\x1f\x7f<>:"/\\|?*]', '_', basename).strip(' .')[:140]
    return f'{basename or "documento"}.{extension}'
