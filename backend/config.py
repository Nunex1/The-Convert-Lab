import os
from pathlib import Path

MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '25'))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_PAGES = int(os.getenv('MAX_PDF_PAGES', '150'))
CONVERSION_TIMEOUT = int(os.getenv('CONVERSION_TIMEOUT_SECONDS', '120'))
MAX_CONCURRENT = int(os.getenv('MAX_CONCURRENT_CONVERSIONS', '2'))
TEMP_ROOT = Path(os.getenv('TEMP_DIR', str(Path(__import__('tempfile').gettempdir()) / 'convertlab'))).resolve()
FORMATS = {'pdf': ['md', 'docx', 'xlsx', 'pptx'], 'docx': ['md'], 'mht': ['xlsx'], 'mhtml': ['xlsx']}
MIMES = {'md': 'text/markdown; charset=utf-8', 'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'}
