import asyncio
import json
import logging
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.responses import FileResponse
from backend.config import FORMATS, MIMES, MAX_FILE_SIZE, MAX_FILE_SIZE_MB, MAX_PAGES, MAX_CONCURRENT, CONVERSION_TIMEOUT, TEMP_ROOT
from backend.services.file_detector import detect_extension, output_name
from backend.services.errors import ConversionError
from backend.services.temporary_files import cleanup_job

router = APIRouter(prefix='/api')
slots = asyncio.Semaphore(MAX_CONCURRENT)
logger = logging.getLogger('convertlab')


class TemporaryFileResponse(FileResponse):
    def __init__(self, *args, job: Path, **kwargs):
        super().__init__(*args, **kwargs)
        self.job = job

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            cleanup_job(self.job)


@router.get('/formats')
def formats():
    return FORMATS


@router.get('/config')
def config():
    return {'max_file_size_mb': MAX_FILE_SIZE_MB, 'max_pdf_pages': MAX_PAGES, 'timeout_seconds': CONVERSION_TIMEOUT}


@router.get('/health')
def health():
    return {'status': 'ok'}


@router.post('/convert')
async def convert(file: UploadFile = File(...), output_format: str = Form(...)):
    job = None
    process = None
    acquired = False
    response_owns_job = False
    started = time.monotonic()
    try:
        input_format = detect_extension(file.filename or '')
        if output_format not in FORMATS[input_format]:
            raise HTTPException(400, 'Esta combinação de formatos não é suportada.')
        try:
            await asyncio.wait_for(slots.acquire(), timeout=0.1)
            acquired = True
        except TimeoutError:
            raise HTTPException(429, 'Todos os conversores estão ocupados. Tente novamente em alguns instantes.') from None
        job = TEMP_ROOT / ('job-' + uuid.uuid4().hex)
        job.mkdir(parents=True)
        size = 0
        with (job / ('input.' + input_format)).open('wb') as destination:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(413, f'O arquivo excede o limite de {MAX_FILE_SIZE_MB} MB.')
                destination.write(chunk)
        (job / 'request.json').write_text(json.dumps({'input': input_format, 'output': output_format, 'mime': file.content_type}), encoding='utf-8')
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'backend.worker', str(job),
            cwd=str(Path(__file__).resolve().parents[2]),
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            await asyncio.wait_for(process.wait(), timeout=CONVERSION_TIMEOUT)
        except TimeoutError:
            raise HTTPException(504, 'Este documento demorou demais para converter. Tente um arquivo menor.') from None
        status_path = job / 'status.json'
        if process.returncode != 0 or not status_path.exists():
            raise HTTPException(422, 'Não foi possível processar este documento. Tente uma versão menor ou simplificada.')
        status = json.loads(status_path.read_text(encoding='utf-8'))
        if not status['ok']:
            logger.info('conversion status=error type=%s code=%s', input_format, status['code'])
            raise HTTPException(422, status['message'])
        logger.info('conversion status=ok type=%s output=%s bytes=%d seconds=%.2f', input_format, output_format, size, time.monotonic() - started)
        response = TemporaryFileResponse(
            job / ('result.' + output_format), job=job,
            media_type=MIMES[output_format], filename=output_name(file.filename or 'documento', output_format),
            headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'X-Conversion-Warnings': quote(json.dumps(status['warnings'], ensure_ascii=False))},
        )
        response_owns_job = True
        return response
    except ConversionError as error:
        raise HTTPException(400, str(error)) from None
    finally:
        if process and process.returncode is None:
            process.kill()
            await process.wait()
        await file.close()
        if acquired:
            slots.release()
        if job and not response_owns_job:
            cleanup_job(job)
