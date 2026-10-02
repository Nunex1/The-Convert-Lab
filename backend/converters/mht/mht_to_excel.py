from pathlib import Path
from bs4 import BeautifulSoup
from backend.services.file_validator import read_mime_html
from backend.services.table_detector import write_tables
from backend.services.errors import ConversionError


def expand_table(table):
    grid = {}
    row_number = 0
    for tr in table.find_all('tr'):
        if tr.find_parent('table') != table:
            continue
        column = 0
        for cell in tr.find_all(['td', 'th'], recursive=False):
            while (row_number, column) in grid:
                column += 1
            try:
                rowspan = max(1, min(1000, int(cell.get('rowspan', 1))))
                colspan = max(1, min(200, int(cell.get('colspan', 1))))
            except ValueError:
                rowspan = colspan = 1
            if len(grid) + rowspan * colspan > 500_000:
                raise ConversionError('A tabela HTML excede o limite de processamento.')
            for r in range(rowspan):
                for c in range(colspan):
                    grid[row_number + r, column + c] = cell.get_text(' ', strip=True) if r == 0 and c == 0 else None
            column += colspan
        row_number += 1
    if not grid:
        return []
    height, width = max(r for r, c in grid) + 1, max(c for r, c in grid) + 1
    if height * width > 500_000:
        raise ConversionError('A tabela HTML excede o limite de processamento.')
    return [[grid.get((r, c)) for c in range(width)] for r in range(height)]


def convert(source: Path, target: Path) -> list[str]:
    soup = BeautifulSoup(read_mime_html(source), 'html.parser')
    for element in soup(['script', 'style', 'iframe', 'object']):
        element.decompose()
    tables = []
    for table in soup.find_all('table'):
        # Leaf tables carry data; avoid duplicating nested layout tables.
        if table.find('table'):
            continue
        caption = table.find('caption')
        title = caption.get_text(' ', strip=True) if caption else f'Tabela {len(tables) + 1}'
        tables.append((title, expand_table(table)))
    write_tables(tables, target)
    return []
