import asyncio
import contextlib
import json
import logging
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from starlette.responses import FileResponse
from backend.config import FORMATS, MIMES, MAX_FILE_SIZE, MAX_FILE_SIZE_MB, MAX_PAGES, MAX_CONCURRENT, CONVERSION_TIMEOUT, TEMP_ROOT
from backend.services.file_detector import detect_extension, output_name
from backend.services.errors import ConversionError
from backend.services.temporary_files import cleanup_job
from backend.services.capabilities import available_formats

router = APIRouter(prefix='/api')
slots = asyncio.Semaphore(MAX_CONCURRENT)
logger = logging.getLogger('convertlab')


async def wait_for_worker(process, request):
    async def disconnected():
        while True:
            if (await request.receive())['type'] == 'http.disconnect':
                return

    finished = asyncio.create_task(process.wait())
    disconnect = asyncio.create_task(disconnected())
    try:
        done, _ = await asyncio.wait(
            {finished, disconnect}, timeout=CONVERSION_TIMEOUT,
            return_when=asyncio.FIRST_COMPLETED,
        )
        if not done:
            raise HTTPException(504, 'Este documento demorou demais para converter. Tente um arquivo menor.')
        if disconnect in done:
            raise HTTPException(499, 'Conversão cancelada.')
        await finished
    finally:
        for task in (finished, disconnect):
            task.cancel()
        await asyncio.gather(finished, disconnect, return_exceptions=True)


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
    return available_formats()


@router.get('/config')
def config():
    return {'max_file_size_mb': MAX_FILE_SIZE_MB, 'max_pdf_pages': MAX_PAGES, 'timeout_seconds': CONVERSION_TIMEOUT}


@router.get('/health')
def health():
    return {'status': 'ok'}


@router.post('/convert')
async def convert(request: Request, file: UploadFile = File(...), output_format: str = Form(...), csv_options: str = Form('{}')):
    job = None
    process = None
    acquired = False
    response_owns_job = False
    started = time.monotonic()
    timings = {}
    try:
        input_format = detect_extension(file.filename or '')
        if output_format not in available_formats()[input_format]:
            raise HTTPException(400, 'Esta combinação de formatos não é suportada.')
        options = None
        if output_format == 'csv':
            from backend.services.csv_options import normalize_options
            try:
                if len(csv_options) > 1024:
                    raise ValueError()
                options = normalize_options(json.loads(csv_options))
            except (ValueError, TypeError):
                raise HTTPException(400, 'As opções de exportação CSV são inválidas.') from None
        try:
            await asyncio.wait_for(slots.acquire(), timeout=0.1)
            acquired = True
            timings['capacity_wait'] = (time.monotonic() - started) * 1000
        except TimeoutError:
            raise HTTPException(429, 'Todos os conversores estão ocupados. Tente novamente em alguns instantes.') from None
        job = TEMP_ROOT / ('job-' + uuid.uuid4().hex)
        job.mkdir(parents=True)
        size = 0
        stage = time.monotonic()
        with (job / ('input.' + input_format)).open('wb') as destination:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(413, f'O arquivo excede o limite de {MAX_FILE_SIZE_MB} MB.')
                destination.write(chunk)
        timings['upload_copy'] = (time.monotonic() - stage) * 1000
        (job / 'request.json').write_text(json.dumps({'input': input_format, 'output': output_format, 'mime': file.content_type, 'csv_options': options}), encoding='utf-8')
        stage = time.monotonic()
        spawning = asyncio.create_task(asyncio.create_subprocess_exec(
            sys.executable, '-m', 'backend.worker', str(job),
            cwd=str(Path(__file__).resolve().parents[2]),
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        ))
        try:
            process = await asyncio.shield(spawning)
        except asyncio.CancelledError:
            # Acquire the handle even if cancellation races with process creation.
            process = await spawning
            raise
        timings['spawn'] = (time.monotonic() - stage) * 1000
        await wait_for_worker(process, request)
        timings['worker_wall'] = (time.monotonic() - stage) * 1000
        status_path = job / 'status.json'
        if process.returncode not in (0, 1) or not status_path.is_file():
            raise HTTPException(422, 'Não foi possível processar este documento. Tente uma versão menor ou simplificada.')
        try:
            status = json.loads(status_path.read_text(encoding='utf-8'))
            valid = isinstance(status, dict) and (
                (process.returncode == 0 and status.get('ok') is True
                 and isinstance(status.get('warnings'), list)
                 and all(isinstance(w, str) for w in status['warnings'])
                 and (job / ('result.' + output_format)).is_file())
                or (process.returncode == 1 and status.get('ok') is False
                    and status.get('code') == 'CONVERSION_ERROR'
                    and isinstance(status.get('message'), str))
            )
        except (ValueError, OSError):
            valid = False
        if not valid:
            raise HTTPException(422, 'Não foi possível processar este documento. Tente uma versão menor ou simplificada.')
        if not status['ok']:
            logger.info('conversion status=error type=%s code=%s', input_format, status['code'])
            raise HTTPException(422, status['message'])
        logger.info('conversion status=ok type=%s output=%s bytes=%d seconds=%.2f', input_format, output_format, size, time.monotonic() - started)
        timings.update({key: value for key, value in status.get('timings_ms', {}).items()
                        if key in {'worker_import', 'input_validation', 'converter_import', 'conversion', 'result_validation'}
                        and isinstance(value, (int, float)) and 0 <= value < 1e9})
        response = TemporaryFileResponse(
            job / ('result.' + output_format), job=job,
            media_type=MIMES[output_format], filename=output_name(file.filename or 'documento', output_format),
            headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'X-Conversion-Warnings': quote(json.dumps(status['warnings'], ensure_ascii=False)),
                     'Server-Timing': ', '.join(f'{key};dur={value:.2f}' for key, value in timings.items())},
        )
        response_owns_job = True
        return response
    except ConversionError as error:
        raise HTTPException(400, str(error)) from None
    finally:
        if process and process.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                process.kill()
            await process.wait()
        await file.close()
        if acquired:
            slots.release()
        if job and not response_owns_job:
            cleanup_job(job)
