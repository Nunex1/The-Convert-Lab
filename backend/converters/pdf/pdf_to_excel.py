from pathlib import Path
import pymupdf
from backend.services.table_detector import write_tables
from backend.services.errors import ConversionError


def convert(source: Path, target: Path) -> list[str]:
    tables = []
    with pymupdf.open(source) as document:
        for page_number, page in enumerate(document, 1):
            if len(page.get_text().strip()) < 12 and page.get_images():
                raise ConversionError('Este documento parece ter páginas digitalizadas. Para extrair tabelas, envie um PDF com camada de texto. OCR ainda não está disponível.')
            detected = page.find_tables()
            if not detected.tables:
                detected = page.find_tables(strategy='text', min_words_vertical=3, min_words_horizontal=1)
            for table in detected.tables:
                rows = table.extract()
                if table.col_count >= 2 and len(rows) >= 2:
                    tables.append((f'Página {page_number} - Tabela {len(tables) + 1}', rows))
    if not tables:
        raise ConversionError('Não foi possível identificar tabelas neste PDF.')
    write_tables(tables, target)
    return ['Confira a estrutura e os valores extraídos, especialmente em tabelas sem bordas ou com células mescladas.']
