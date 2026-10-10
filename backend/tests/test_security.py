import asyncio
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import unquote
import zipfile

import httpx
import pymupdf
import pytest
from starlette.datastructures import UploadFile
from starlette.requests import Request
from fastapi import HTTPException

from backend.api import routes
from backend.config import FORMATS, MIMES, TEMP_ROOT
from backend.main import app
from backend.services import file_validator, temporary_files
from backend.tests.test_initial_flows import convert


def test_get_contracts(client):
    assert client.get('/api/health').json() == {'status': 'ok'}
    assert client.get('/api/formats').json() == FORMATS
    config = client.get('/api/config').json()
    assert config['max_file_size_mb'] > 0 and config['max_pdf_pages'] > 0 and config['timeout_seconds'] > 0


@pytest.mark.parametrize('filename,data,mime,output,code,detail', [
    ('empty.pdf', b'', 'application/pdf', 'pptx', 422, 'vazio'),
    ('bad.pdf', b'not pdf', 'application/pdf', 'pptx', 422, 'assinatura'),
    ('broken.pdf', b'%PDF-1.7\nbroken', 'application/pdf', 'pptx', 422, 'corrompido'),
    ('bad.docx', b'PKinvalid', 'application/zip', 'md', 422, 'corrompido'),
    ('bad.mht', b'<html>not MIME</html>', 'message/rfc822', 'xlsx', 422, 'válido'),
    ('bad.txt', b'hello', 'text/plain', 'md', 400, 'suportado'),
    ('input.docx', b'irrelevant', 'application/zip', 'pptx', 400, 'combinação'),
])
def test_invalid_documents(client, filename, data, mime, output, code, detail):
    response = client.post('/api/convert', files={'file': (filename, data, mime)}, data={'output_format': output})
    assert response.status_code == code
    assert detail in response.json()['detail']
    assert not list(TEMP_ROOT.glob('job-*'))


def test_wrong_mime(client, pdf):
    response = convert(client, pdf, 'pptx', 'image/png')
    assert response.status_code == 422 and 'conteúdo' in response.json()['detail']


def test_password_pdf(client, tmp_path):
    path = tmp_path / 'locked.pdf'
    with pymupdf.open() as document:
        document.new_page().insert_text((40, 40), 'Protected test')
        document.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw='owner', user_pw='test')
    response = convert(client, path, 'pptx', 'application/pdf')
    assert response.status_code == 422 and 'senha' in response.json()['detail']


def test_page_limit_in_subprocess(client, tmp_path, monkeypatch):
    monkeypatch.setenv('MAX_PDF_PAGES', '1')
    path = tmp_path / 'pages.pdf'
    with pymupdf.open() as document:
        document.new_page()
        document.new_page()
        document.save(path)
    response = convert(client, path, 'pptx', 'application/pdf')
    assert response.status_code == 422 and '1 páginas' in response.json()['detail']


def test_upload_limit(client, monkeypatch):
    monkeypatch.setattr(routes, 'MAX_FILE_SIZE', 10)
    response = client.post('/api/convert', files={'file': ('large.pdf', b'x' * 11, 'application/pdf')}, data={'output_format': 'pptx'})
    assert response.status_code == 413
    assert not list(TEMP_ROOT.glob('job-*'))


def test_worker_size_limit(client, pdf, monkeypatch):
    monkeypatch.setenv('MAX_FILE_SIZE_MB', '0')
    response = convert(client, pdf, 'pptx', 'application/pdf')
    assert response.status_code == 422 and 'limite' in response.json()['detail']


@pytest.mark.parametrize('name,xml', [('../outside.xml', '<root/>'), ('word/vbaProject.bin', ''), ('word/evil.xml', '<!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><a>&x;</a>')])
def test_unsafe_docx(client, name, xml):
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('[Content_Types].xml', '<Types/>')
        archive.writestr('word/document.xml', '<document/>')
        archive.writestr(name, xml)
    response = client.post('/api/convert', files={'file': ('bad.docx', stream.getvalue(), 'application/zip')}, data={'output_format': 'md'})
    assert response.status_code == 422


def test_zip_expansion_limit(client):
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', '<Types/>')
        archive.writestr('word/document.xml', '<document/>')
        archive.writestr('word/media/oversized.bin', b'0' * (50 * 1024 * 1024 + 1))
    response = client.post('/api/convert', files={'file': ('large.docx', stream.getvalue(), 'application/zip')}, data={'output_format': 'md'})
    assert response.status_code == 422 and 'grande' in response.json()['detail']


def test_download_headers(client, pdf):
    response = client.post('/api/convert', files={'file': ('../Relatório.pdf', pdf.read_bytes(), 'application/pdf')}, data={'output_format': 'pptx'})
    assert response.status_code == 200
    assert response.headers['content-type'] == MIMES['pptx']
    assert unquote(response.headers['content-disposition']) == "attachment; filename*=utf-8''Relatório.pptx"
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert isinstance(json.loads(unquote(response.headers['x-conversion-warnings'])), list)
    assert int(response.headers['content-length']) == len(response.content)


def test_cors(client):
    response = client.options('/api/convert', headers={'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'Content-Type'})
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://localhost:3000'


def test_parallel_conversions_are_isolated(pdf):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            responses = await asyncio.gather(*[
                client.post('/api/convert', files={'file': (f'job-{index}.pdf', pdf.read_bytes(), 'application/pdf')}, data={'output_format': 'pptx'})
                for index in range(2)
            ])
        assert all(r.status_code == 200 for r in responses)
        assert responses[0].headers['content-disposition'] != responses[1].headers['content-disposition']
    asyncio.run(run())
    assert not list(TEMP_ROOT.glob('job-*'))


def test_busy_returns_429(client, pdf, monkeypatch):
    monkeypatch.setattr(routes, 'slots', asyncio.Semaphore(0))
    assert convert(client, pdf, 'pptx', 'application/pdf').status_code == 429


def test_timeout_kills_real_subprocess(client, pdf, monkeypatch):
    processes = []
    original = asyncio.create_subprocess_exec
    async def stalled(*args, **kwargs):
        process = await original(sys.executable, '-c', 'import time; time.sleep(30)', **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(routes.asyncio, 'create_subprocess_exec', stalled)
    monkeypatch.setattr(routes, 'CONVERSION_TIMEOUT', .1)
    response = convert(client, pdf, 'pptx', 'application/pdf')
    assert response.status_code == 504
    assert processes[0].returncode is not None
    assert not list(TEMP_ROOT.glob('job-*'))


@pytest.mark.parametrize('mode', ['disconnect', 'cancel', 'cancel_while_spawning'])
def test_cancellation_kills_worker_and_cleans_job(pdf, monkeypatch, mode):
    processes = []
    original = asyncio.create_subprocess_exec
    async def stalled(*args, **kwargs):
        process = await original(sys.executable, '-c', 'import time; time.sleep(30)', **kwargs)
        processes.append(process)
        if mode == 'cancel_while_spawning':
            await asyncio.sleep(.1)
        return process
    monkeypatch.setattr(routes.asyncio, 'create_subprocess_exec', stalled)
    async def run():
        async def receive():
            if mode == 'disconnect':
                return {'type': 'http.disconnect'}
            await asyncio.Event().wait()
        upload = UploadFile(BytesIO(pdf.read_bytes()), filename='test.pdf')
        task = asyncio.create_task(routes.convert(Request({'type': 'http'}, receive), upload, 'pptx'))
        if mode.startswith('cancel'):
            while not processes:
                await asyncio.sleep(.01)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            with pytest.raises(HTTPException) as error:
                await task
            assert error.value.status_code == 499
        assert upload.file.closed
        assert processes[0].returncode is not None
    asyncio.run(run())
    assert not list(TEMP_ROOT.glob('job-*'))


def test_response_transport_failure_cleans_job(tmp_path):
    job = tmp_path / 'job-response'
    job.mkdir()
    result = job / 'result.md'
    result.write_text('test')
    response = routes.TemporaryFileResponse(result, job=job)
    async def fail(message):
        raise ConnectionError('closed')
    with pytest.raises(ConnectionError):
        asyncio.run(response({'type': 'http', 'method': 'GET', 'headers': []}, None, fail))
    assert not job.exists()


def test_cleanup_stale_preserves_recent(tmp_path, monkeypatch):
    monkeypatch.setattr(temporary_files, 'TEMP_ROOT', tmp_path)
    old, recent = tmp_path / 'job-old', tmp_path / 'job-recent'
    old.mkdir()
    recent.mkdir()
    os.utime(old, (time.time() - 7200,) * 2)
    temporary_files.cleanup_stale()
    assert not old.exists() and recent.exists()


@pytest.mark.parametrize('payload,exit_code', [('{', 0), ('{}', 0), ('{"ok":true,"warnings":[]}', 1), ('{"ok":false,"code":"INTERNAL_ERROR","message":"SECRET"}', 2)])
def test_broken_worker_contract_does_not_leak_or_return_success(client, pdf, monkeypatch, payload, exit_code):
    async def broken(*args, **kwargs):
        job = Path(args[-1])
        (job / 'status.json').write_text(payload)
        class Process:
            returncode = exit_code
            async def wait(self):
                return self.returncode
        return Process()
    monkeypatch.setattr(routes.asyncio, 'create_subprocess_exec', broken)
    response = convert(client, pdf, 'pptx', 'application/pdf')
    assert response.status_code == 422 and 'SECRET' not in response.text
    assert not list(TEMP_ROOT.glob('job-*'))


@pytest.mark.parametrize('with_length', [True, False])
def test_body_limit_including_chunked_upload(monkeypatch, with_length):
    import backend.main as main
    monkeypatch.setattr(main, 'MAX_FILE_SIZE', 10)
    async def run():
        boundary = b'--test\r\nContent-Disposition: form-data; name="file"; filename="a.pdf"\r\nContent-Type: application/pdf\r\n\r\n'
        body = boundary + b'x' * (1024 * 1024 + 100) + b'\r\n--test--\r\n'
        async def chunks():
            for index in range(0, len(body), 65536):
                yield body[index:index + 65536]
        headers = {'Content-Type': 'multipart/form-data; boundary=test'}
        if with_length:
            headers['Content-Length'] = str(len(body))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            response = await client.post('/api/convert', content=chunks(), headers=headers)
        assert response.status_code == 413
    asyncio.run(run())
