"""Optional licensed engine. No evaluation output ever enters the download path."""
import os
from pathlib import Path
import tempfile
import zipfile

from backend.services.errors import ConversionError


def licensed_engine():
    if os.getenv('ENABLE_XLSB') != '1' or not os.getenv('ASPOSE_CELLS_LICENSE_PATH'):
        raise ConversionError('Conversão XLSB indisponível: motor licenciado não habilitado.')
    try:
        from aspose.cells import License, Workbook, SaveFormat
        license = License()
        license.set_license(os.environ['ASPOSE_CELLS_LICENSE_PATH'])
        if not Workbook().is_licensed:
            raise ValueError('unlicensed')
        return Workbook, SaveFormat
    except Exception:
        raise ConversionError('Conversão XLSB indisponível: não foi possível validar a licença do motor.') from None


def validate_xlsb(path):
    from pyxlsb import open_workbook
    with zipfile.ZipFile(path) as archive:
        if 'xl/workbook.bin' not in archive.namelist() or 'xl/workbook.xml' in archive.namelist():
            raise ConversionError('O resultado não é uma planilha binária XLSB autêntica.')
    with open_workbook(str(path)) as workbook:
        if not workbook.sheets:
            raise ConversionError('O XLSB gerado não contém abas.')
        for name in workbook.sheets:
            with workbook.get_sheet(name) as sheet:
                for _ in sheet.rows():
                    pass


def convert(source, target):
    Workbook, SaveFormat = licensed_engine()
    workbook = Workbook(str(source))
    if not workbook.is_licensed:
        raise ConversionError('A licença XLSB não está ativa.')
    # No calculate_formula / external data refresh: preserve saved formulas and caches.
    workbook.save(str(target), SaveFormat.XLSB)
    from pyxlsb import open_workbook
    with open_workbook(str(target)) as result:
        if result.sheets != [sheet.name for sheet in workbook.worksheets]:
            raise ConversionError('A conversão XLSB alterou a organização das abas.')
    return ['XLSB preserva os recursos suportados pelo motor Aspose.Cells. Fórmulas não são recalculadas; recursos avançados exigem conferência no aplicativo de destino.']


def probe():
    Workbook, SaveFormat = licensed_engine()
    with tempfile.TemporaryDirectory(prefix='convertlab-xlsb-check-') as folder:
        target = Path(folder) / 'probe.xlsb'
        workbook = Workbook()
        workbook.worksheets[0].cells.get('A1').put_value('ConvertLab')
        workbook.save(str(target), SaveFormat.XLSB)
        validate_xlsb(target)
        from pyxlsb import open_workbook
        with open_workbook(str(target)) as result, result.get_sheet(1) as sheet:
            if next(sheet.rows())[0].v != 'ConvertLab':
                raise ValueError('XLSB round trip failed')


if __name__ == '__main__':
    try:
        probe()
    except Exception:
        raise SystemExit(1)
