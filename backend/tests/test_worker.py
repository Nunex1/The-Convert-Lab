import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest
from pptx import Presentation

from backend.config import TEMP_ROOT
from backend import worker
from backend.services.errors import ConversionError
from backend.services.temporary_files import cleanup_job


@pytest.fixture
def job(pdf):
    path = TEMP_ROOT / ('job-' + uuid.uuid4().hex)
    path.mkdir(parents=True)
    (path / 'input.pdf').write_bytes(pdf.read_bytes())
    (path / 'request.json').write_text(json.dumps({'input': 'pdf', 'output': 'pptx', 'mime': 'application/pdf'}))
    yield path
    cleanup_job(path)


def execute(job):
    result = subprocess.run([sys.executable, '-m', 'backend.worker', str(job)], capture_output=True, timeout=30)
    status = json.loads((job / 'status.json').read_text(encoding='utf-8'))
    assert not (job / 'status.tmp').exists()
    return result, status


def test_direct_module_success(job):
    result, status = execute(job)
    assert result.returncode == 0
    assert status['ok'] is True and isinstance(status['warnings'], list)
    assert len(Presentation(job / 'result.pptx').slides) == 1


@pytest.mark.parametrize('payload', ['{', '[]', '{}', '{"input":[],"output":"pptx"}', '{"input":"pdf","output":"../../secret"}', '{"input":"pdf","output":"pptx","mime":[]}'])
def test_invalid_request(job, payload):
    (job / 'request.json').write_text(payload)
    result, status = execute(job)
    assert result.returncode == 1
    assert status['ok'] is False and status['code'] == 'CONVERSION_ERROR'
    assert not list(job.glob('result.*'))


@pytest.mark.parametrize('missing', ['request.json', 'input.pdf'])
def test_missing_input(job, missing):
    (job / missing).unlink()
    result, status = execute(job)
    assert result.returncode == 1 and status['ok'] is False


@pytest.mark.parametrize('arguments', [[], ['one', 'two'], ['..']])
def test_invalid_cli(arguments):
    result = subprocess.run([sys.executable, '-m', 'backend.worker', *arguments], capture_output=True, timeout=30)
    assert result.returncode == 2
    assert b'Traceback' not in result.stderr


def test_external_job_is_not_touched(tmp_path):
    outside = tmp_path / ('job-' + uuid.uuid4().hex)
    outside.mkdir()
    assert worker.main([str(outside)]) == 2
    assert not list(outside.iterdir())


def test_input_hardlink_rejected(job, pdf):
    (job / 'input.pdf').unlink()
    os.link(pdf, job / 'input.pdf')
    result, status = execute(job)
    assert result.returncode == 1 and status['ok'] is False
    assert pdf.is_file()


@pytest.mark.parametrize('expected', [True, False])
def test_failures_remove_partial_output_and_hide_internal_details(job, monkeypatch, expected):
    def fail(source, target):
        target.write_bytes(b'partial file')
        if expected:
            raise ConversionError('Mensagem segura.')
        raise RuntimeError('SECRET /server/private/document.pdf')
    monkeypatch.setattr(worker, 'get_converter', lambda *_: fail)
    assert worker.run(job) == (1 if expected else 2)
    status = json.loads((job / 'status.json').read_text(encoding='utf-8'))
    assert status['message'] == ('Mensagem segura.' if expected else worker.INTERNAL_MESSAGE)
    assert not (job / 'result.pptx').exists()


def test_invalid_generated_office_document_is_not_success(job, monkeypatch):
    def invalid(source, target):
        target.write_bytes(b'not a powerpoint')
        return []
    monkeypatch.setattr(worker, 'get_converter', lambda *_: invalid)
    assert worker.run(job) == 2
    assert json.loads((job / 'status.json').read_text())['ok'] is False
    assert not (job / 'result.pptx').exists()


def test_status_is_published_after_validation(job, monkeypatch):
    original = worker.validate_result
    def validate(path, extension):
        assert not (job / 'status.json').exists()
        original(path, extension)
    monkeypatch.setattr(worker, 'validate_result', validate)
    assert worker.run(job) == 0
