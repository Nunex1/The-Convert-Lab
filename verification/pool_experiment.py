"""Trusted synthetic jobs only: measures reuse, NOT a production pool implementation."""
from concurrent.futures import ProcessPoolExecutor
import json
import multiprocessing
import os
from pathlib import Path
import statistics
import tempfile
import time
import uuid


def run_job(path):
    import psutil
    from backend.worker import run
    assert run(Path(path)) == 0
    return psutil.Process().memory_info().rss / 1024**2


def main():
    from docx import Document
    with tempfile.TemporaryDirectory(prefix='convertlab-pool-') as folder:
        os.environ['TEMP_DIR'] = folder
        folder = Path(folder)
        document = Document()
        for i in range(100):
            document.add_paragraph(f'Linha {i}: informação sintética para medição.')
        source = folder / 'source.docx'
        document.save(source)
        runs = []
        with ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context('spawn')) as pool:
            for _ in range(10):
                job = folder / ('job-' + uuid.uuid4().hex)
                job.mkdir()
                (job / 'input.docx').write_bytes(source.read_bytes())
                (job / 'request.json').write_text(json.dumps({'input': 'docx', 'output': 'md'}))
                started = time.perf_counter()
                rss = pool.submit(run_job, str(job)).result(timeout=120)
                runs.append({'seconds': time.perf_counter() - started, 'resident_mb': rss})
        report = {'warning': 'Experimental reuse has NO per-job hard cancellation, memory reset or fault containment. Not used by API.',
                  'runs': runs, 'first_seconds': runs[0]['seconds'],
                  'warm_median_seconds': statistics.median(r['seconds'] for r in runs[1:]),
                  'warm_p95_seconds': max(r['seconds'] for r in runs[1:])}
        Path('verification/pool-performance.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
