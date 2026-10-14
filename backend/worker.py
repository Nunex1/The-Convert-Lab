"""One isolated conversion. Exit 0: success, 1: rejected document, 2: worker fault."""

import json
import os
from pathlib import Path
import re
import sys
import time

BOOT_STARTED = time.perf_counter()

from backend.config import FORMATS, TEMP_ROOT
from backend.converters.registry import get_converter
from backend.services.errors import ConversionError
from backend.services.file_validator import validate_file
from backend.services.result_validator import validate_result

INTERNAL_MESSAGE = 'Não foi possível processar este documento. Tente uma versão menor ou simplificada.'


def job_directory(argument: str) -> Path:
    path = Path(argument).absolute()
    if (not re.fullmatch(r'job-[0-9a-f]{32}', path.name)
            or path.parent != TEMP_ROOT or not path.is_dir()
            or path.is_symlink() or path.resolve() != path):
        raise ValueError('Invalid job directory')
    return path


def regular_file(path: Path) -> bool:
    return (path.is_file() and not path.is_symlink()
            and path.resolve() == path and path.stat().st_nlink == 1)


def write_status(job: Path, status: dict) -> None:
    temporary = job / 'status.tmp'
    # Exclusive creation avoids following a pre-existing link.
    with temporary.open('x', encoding='utf-8') as handle:
        json.dump(status, handle, ensure_ascii=False)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(job / 'status.json')


def run(job: Path) -> int:
    target = None
    timings = {'worker_import': (time.perf_counter() - BOOT_STARTED) * 1000}
    try:
        request_path = job / 'request.json'
        if not regular_file(request_path) or request_path.stat().st_size > 4096:
            raise ConversionError('A solicitação de conversão é inválida.')
        try:
            request = json.loads(request_path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError):
            raise ConversionError('A solicitação de conversão é inválida.') from None
        if not isinstance(request, dict):
            raise ConversionError('A solicitação de conversão é inválida.')
        source_format, output_format = request.get('input'), request.get('output')
        mime = request.get('mime')
        if (not isinstance(source_format, str) or source_format not in FORMATS
                or not isinstance(output_format, str) or (output_format not in FORMATS[source_format]
                and not (source_format == 'xlsx' and output_format == 'xlsb' and os.getenv('ENABLE_XLSB') == '1'))):
            raise ConversionError('Esta combinação de formatos não é suportada.')
        if mime is not None and not isinstance(mime, str):
            raise ConversionError('O tipo de conteúdo informado é inválido.')
        source = job / ('input.' + source_format)
        if not regular_file(source):
            raise ConversionError('O arquivo de entrada não está disponível.')
        candidate = job / ('result.' + output_format)
        if candidate.exists() or candidate.is_symlink():
            raise ConversionError('A solicitação de conversão já possui um resultado.')
        target = candidate
        stage = time.perf_counter()
        validate_file(source, source_format, mime)
        timings['input_validation'] = (time.perf_counter() - stage) * 1000
        stage = time.perf_counter()
        converter = get_converter(source_format, output_format)
        timings['converter_import'] = (time.perf_counter() - stage) * 1000
        stage = time.perf_counter()
        if source_format == 'xlsx' and output_format == 'csv':
            warnings = converter(source, target, request.get('csv_options'))
        else:
            warnings = converter(source, target)
        timings['conversion'] = (time.perf_counter() - stage) * 1000
        stage = time.perf_counter()
        if output_format == 'csv':
            validate_result(target, output_format, delimiter=(request.get('csv_options') or {}).get('delimiter', ';'))
        else:
            validate_result(target, output_format)
        timings['result_validation'] = (time.perf_counter() - stage) * 1000
        if not isinstance(warnings, list) or not all(isinstance(w, str) for w in warnings):
            raise TypeError('Invalid converter warnings')
        status, exit_code = {'ok': True, 'warnings': warnings, 'timings_ms': timings}, 0
    except ConversionError as error:
        status, exit_code = {'ok': False, 'code': 'CONVERSION_ERROR', 'message': str(error)}, 1
    except Exception as error:
        # Never log document content, exception messages or server paths.
        print('conversion worker fault: ' + type(error).__name__, file=sys.stderr)
        status, exit_code = {'ok': False, 'code': 'INTERNAL_ERROR', 'message': INTERNAL_MESSAGE}, 2
    if exit_code and target is not None:
        target.unlink(missing_ok=True)
    write_status(job, status)
    return exit_code


def main(argv=None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        return 2
    try:
        return run(job_directory(arguments[0]))
    except Exception as error:
        print('conversion worker fault: ' + type(error).__name__, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
