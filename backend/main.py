import asyncio
import contextlib
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.routes import router
from backend.config import MAX_FILE_SIZE, MAX_FILE_SIZE_MB
from backend.services.temporary_files import cleanup_stale


@asynccontextmanager
async def lifespan(app):
    cleanup_stale()
    async def sweeper():
        while True:
            await asyncio.sleep(600)
            cleanup_stale()
    task = asyncio.create_task(sweeper())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


class RequestTooLarge(HTTPException):
    def __init__(self):
        super().__init__(413, f'O arquivo excede o limite de {MAX_FILE_SIZE_MB} MB.')


class BodyLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        limit = MAX_FILE_SIZE + 1024 * 1024  # bounded multipart overhead
        count = 0
        async def limited_receive():
            nonlocal count
            message = await receive()
            count += len(message.get('body', b''))
            if count > limit:
                raise RequestTooLarge()
            return message
        headers = dict(scope.get('headers', []))
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            length = 0
        if length > limit:
            return await JSONResponse({'detail': f'O arquivo excede o limite de {MAX_FILE_SIZE_MB} MB.'}, 413)(scope, receive, send)
        await self.app(scope, limited_receive, send)


app = FastAPI(title='ConvertLab API', version='1.0.0', lifespan=lifespan)
app.add_middleware(BodyLimitMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=[v.strip() for v in os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',') if v.strip()], allow_methods=['GET', 'POST'], allow_headers=['Content-Type'], expose_headers=['Content-Disposition', 'X-Conversion-Warnings'])


@app.exception_handler(RequestTooLarge)
async def too_large(request: Request, error: RequestTooLarge):
    return JSONResponse({'detail': f'O arquivo excede o limite de {MAX_FILE_SIZE_MB} MB.'}, 413)


app.include_router(router)
