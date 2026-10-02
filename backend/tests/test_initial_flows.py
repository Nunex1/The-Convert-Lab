from io import BytesIO
from openpyxl import load_workbook
from backend.config import TEMP_ROOT


def convert(client, path, target, mime):
    return client.post('/api/convert', files={'file': (path.name, path.read_bytes(), mime)}, data={'output_format': target})


def test_01_pdf_markdown(client, pdf):
    response = convert(client, pdf, 'md', 'application/pdf')
    assert response.status_code == 200, response.text
    assert 'Relatorio financeiro' in response.text
    assert '1250' in response.text
    assert '.md' in response.headers['content-disposition']
    assert not list(TEMP_ROOT.glob('job-*'))


def test_02_docx_markdown(client, docx):
    response = convert(client, docx, 'md', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    assert response.status_code == 200, response.text
    assert '# Objetivos' in response.text
    assert '**Destaque**' in response.text
    assert 'ConvertLab' in response.text
    assert not list(TEMP_ROOT.glob('job-*'))


def test_03_mht_excel(client, mht):
    response = convert(client, mht, 'xlsx', 'message/rfc822')
    assert response.status_code == 200, response.text
    workbook = load_workbook(BytesIO(response.content))
    sheet = workbook['Financeiro']
    assert sheet['B2'].value == 1250.5
    assert sheet['B3'].value == .25
    assert sheet['A3'].data_type == 's'
    assert sheet['C2'].value.year == 2026
    assert sheet.freeze_panes == 'A2'
    assert not list(TEMP_ROOT.glob('job-*'))
