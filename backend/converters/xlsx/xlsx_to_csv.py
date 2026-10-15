"""Streaming CSV export. Formulas are never evaluated or emitted as executable text."""
import csv
from datetime import date, datetime, time, timedelta
import re

from openpyxl import load_workbook
from backend.services.errors import ConversionError
from backend.services.csv_options import normalize_options


def convert(source, target, options=None):
    options = normalize_options(options)
    workbook = load_workbook(source, read_only=True, data_only=True, keep_links=False)
    protected = 0
    try:
        if not workbook.worksheets:
            raise ConversionError('A planilha não contém uma aba de dados.')
        if options['sheet'] and options['sheet'] not in [s.title for s in workbook.worksheets]:
            raise ConversionError('A aba informada não existe. Informe o nome exato ou deixe vazio para usar a primeira.')
        sheet = workbook[options['sheet']] if options['sheet'] else workbook.worksheets[0]
        # Do not trust stale or malicious dimension metadata.
        sheet.reset_dimensions()
        count = 0
        wrote_record = False
        with target.open('w', encoding='utf-8-sig' if options['bom'] else 'utf-8', newline='') as stream:
            writer = csv.writer(stream, delimiter=options['delimiter'], lineterminator='\r\n')
            for row in sheet.iter_rows():
                count += len(row)
                if count > 5_000_000:
                    raise ConversionError('A área exportada excede cinco milhões de células, incluindo vazias.')
                values = []
                for cell in row:
                    value = cell.value
                    if value is None:
                        value = ''
                    elif isinstance(value, bool):
                        value = 'TRUE' if value else 'FALSE'
                    elif isinstance(value, (datetime, date, time)):
                        value = value.isoformat()
                    elif isinstance(value, timedelta):
                        value = str(value.total_seconds())
                    elif isinstance(value, (int, float)) and re.fullmatch(r'0{2,}', cell.number_format or '') and value >= 0 and int(value) == value:
                        value = str(int(value)).zfill(len(cell.number_format))
                    elif isinstance(value, str) and (value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n'))):
                        if options['protect_formulas']:
                            value = "'" + value
                            protected += 1
                    values.append(value)
                writer.writerow(values)
                wrote_record = True
                if stream.tell() > 150 * 1024 * 1024:
                    raise ConversionError('O CSV excede o limite de 150 MB.')
            # Keep the chosen encoding/BOM even for an entirely empty worksheet.
            if not wrote_record:
                writer.writerow([])
        warnings = [f'Aba exportada: {sheet.title}. {len(workbook.worksheets) - 1} outra(s) aba(s) não incluída(s).',
                    'CSV não preserva estilos, mesclagens, gráficos ou fórmulas. Fórmulas usam o valor calculado salvo; sem cache, a célula fica vazia. O servidor não recalcula.',
                    'Datas usam ISO 8601, números usam ponto decimal e durações usam segundos. Máscaras simples de zeros são preservadas; importe colunas de códigos como texto no Excel.']
        if protected:
            warnings.append(f'{protected} texto(s) receberam apóstrofo inicial para proteção contra fórmulas. Essa proteção modifica o texto exportado.')
        if not options['protect_formulas']:
            warnings.append('Proteção contra fórmulas desativada por escolha explícita. Textos foram preservados; importe como texto para evitar execução em planilhas.')
        return warnings
    finally:
        workbook.close()
