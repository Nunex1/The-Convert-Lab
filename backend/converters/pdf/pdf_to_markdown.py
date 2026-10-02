from pathlib import Path
import pymupdf
import pymupdf4llm
from backend.services.errors import ConversionError


def convert(source: Path, target: Path) -> list[str]:
    with pymupdf.open(source) as doc:
        if any(len(page.get_text().strip()) < 12 and page.get_images() for page in doc):
            raise ConversionError('Este documento parece ter páginas digitalizadas. OCR ainda não está disponível para Markdown; envie um PDF com camada de texto.')
        result = pymupdf4llm.to_markdown(doc, show_progress=False, embed_images=True, use_ocr=False)
    if not result.strip():
        raise ConversionError('Não foi possível extrair texto deste PDF.')
    target.write_text(result, encoding='utf-8')
    return []
