"""Bounded OOXML inspection before any spreadsheet engine sees untrusted input."""
from pathlib import PurePosixPath
import re
import zipfile
from defusedxml import ElementTree
from backend.services.errors import ConversionError

MAX_EXPANDED = 150 * 1024 * 1024


def validate_xlsx(path):
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        names = [item.filename for item in members]
        if len(members) > 5000 or len(names) != len(set(names)):
            raise ConversionError('A planilha contém partes duplicadas ou em excesso.')
        if not {'[Content_Types].xml', 'xl/workbook.xml', 'xl/_rels/workbook.xml.rels'} <= set(names):
            raise ConversionError('O arquivo não possui a estrutura XLSX válida.')
        if sum(i.file_size for i in members) > MAX_EXPANDED:
            raise ConversionError('A planilha descompactada excede 150 MB.')
        cells = 0
        for item in members:
            name = item.filename
            if (item.flag_bits & 1 or item.file_size > 100 * 1024 * 1024
                    or item.file_size / max(item.compress_size, 1) > 1000
                    or PurePosixPath(name).is_absolute() or '..' in name.split('/')
                    or '\\' in name or ':' in name
                    or any(p in name.lower() for p in ('vbaproject', 'macrosheets/', 'externallinks/', 'embeddings/', 'connections.xml', 'querytables/'))):
                raise ConversionError('A planilha contém conteúdo protegido, externo ou excede os limites de segurança.')
            # Shared strings and styles are eagerly loaded even in openpyxl read_only mode.
            if name in ('xl/sharedStrings.xml', 'xl/styles.xml') and item.file_size > 16 * 1024 * 1024:
                raise ConversionError('O dicionário de textos ou estilos excede o limite de 16 MB.')
            if not name.endswith(('.xml', '.rels')):
                continue
            with archive.open(item) as stream:
                stack = []
                for event, element in ElementTree.iterparse(stream, events=('start', 'end'), forbid_dtd=True):
                    if event == 'start':
                        stack.append(element)
                        if len(stack) > 100:
                            raise ConversionError('A estrutura XML da planilha é muito profunda.')
                        continue
                    tag = element.tag.rsplit('}', 1)[-1]
                    if tag == 'sheetProtection' or (tag == 'workbookProtection' and any(
                            'password' in key.lower() or 'hashvalue' in key.lower()
                            or (key.startswith('lock') and value.lower() in ('true', '1'))
                            for key, value in element.attrib.items())):
                        raise ConversionError('Envie uma cópia da planilha sem proteção.')
                    if tag == 'Relationship' and element.get('TargetMode', '').lower() == 'external':
                        raise ConversionError('Planilhas com referências externas não são aceitas.')
                    if tag == 'Override' and ('macroEnabled' in element.get('ContentType', '') or 'binary' in element.get('ContentType', '')):
                        raise ConversionError('Envie um XLSX sem macros, não um arquivo renomeado.')
                    if tag == 'c':
                        coordinate = re.fullmatch(r'([A-Z]{1,3})([1-9][0-9]{0,6})', element.get('r', 'A1'))
                        if coordinate:
                            column = 0
                            for letter in coordinate[1]:
                                column = column * 26 + ord(letter) - 64
                            if column > 16384 or int(coordinate[2]) > 1048576:
                                coordinate = None
                        if coordinate is None:
                            raise ConversionError('A planilha contém coordenadas de células inválidas.')
                        cells += 1
                        if cells > 5_000_000:
                            raise ConversionError('A planilha excede o limite de cinco milhões de células.')
                    if tag == 'row' and element.get('r') is not None and (not element.get('r', '').isdigit() or not 1 <= int(element.get('r', '0')) <= 1048576):
                        raise ConversionError('A planilha contém índices de linhas inválidos.')
                    if tag in ('f', 'definedName'):
                        formula = element.text or ''
                        # Ignore quoted literal text when recognizing callable functions.
                        callable_text = re.sub(r'"(?:[^"]|"")*"', '', formula)
                        if (re.search(r'\b(?:WEBSERVICE|HYPERLINK|RTD|DDE|CALL|EXEC|REGISTER\.ID)\s*\(', callable_text, re.I)
                                or re.search(r'\[[^\]]+\.(?:xlsx?|xlsm|xlsb)\]', formula, re.I)
                                or re.search(r'\|[^!]*!', callable_text)):
                            raise ConversionError('A planilha contém fórmulas com referências externas ou comandos não permitidos.')
                    stack.pop()
                    if stack:
                        stack[-1].remove(element)
                    element.clear()
