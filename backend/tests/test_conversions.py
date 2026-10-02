from io import BytesIO
import json
from urllib.parse import unquote
import pymupdf
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
from backend.tests.test_initial_flows import convert


def test_pdf_word(client, pdf):
    response = convert(client, pdf, 'docx', 'application/pdf')
    assert response.status_code == 200, response.text
    document = Document(BytesIO(response.content))
    text = '\n'.join(p.text for p in document.paragraphs)
    text += '\n'.join(c.text for t in document.tables for r in t.rows for c in r.cells)
    assert 'Relatorio financeiro' in text
    assert '1250' in text


def test_pdf_excel(client, pdf):
    response = convert(client, pdf, 'xlsx', 'application/pdf')
    assert response.status_code == 200, response.text
    workbook = load_workbook(BytesIO(response.content))
    sheet = workbook.active
    assert sheet['A2'].value == 'Receita'
    assert sheet['B2'].value == 1250.5


def test_pdf_pptx_visual_fallback(client, pdf):
    response = convert(client, pdf, 'pptx', 'application/pdf')
    assert response.status_code == 200, response.text
    presentation = Presentation(BytesIO(response.content))
    assert len(presentation.slides) == 1
    assert any(s.shape_type == 13 for s in presentation.slides[0].shapes)
    assert 'imagem' in json.loads(unquote(response.headers['X-Conversion-Warnings']))[0]


def test_pdf_pptx_editable(client, tmp_path):
    path = tmp_path / 'text.pdf'
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((70, 90), 'Texto editavel', fontsize=20)
        document.save(path)
    response = convert(client, path, 'pptx', 'application/pdf')
    assert response.status_code == 200, response.text
    presentation = Presentation(BytesIO(response.content))
    assert 'Texto editavel' in ' '.join(s.text for s in presentation.slides[0].shapes if s.has_text_frame)


def test_mhtml(client, mht):
    path = mht.with_suffix('.mhtml')
    path.write_bytes(mht.read_bytes())
    response = convert(client, path, 'xlsx', 'application/octet-stream')
    assert response.status_code == 200
    assert load_workbook(BytesIO(response.content)).active['B2'].value == 1250.5
