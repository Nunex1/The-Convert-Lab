"""Alternate baseline/current runs to reduce host-load bias. Prepare baseline with git archive."""
import json
import os
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import uuid
from verification.benchmark import measure

root = Path.cwd()
before = root / 'verification/local/baseline'
assert (before / 'backend/worker.py').is_file()
with tempfile.TemporaryDirectory(prefix='convertlab-paired-') as folder:
    folder = Path(folder)
    env = dict(os.environ, TEMP_DIR=str(folder))
    from docx import Document
    doc = Document()
    for i in range(100):
        doc.add_paragraph(f'Linha {i}: informação sintética para medição.')
    doc.save(folder / 'sample.docx')
    cases = {}
    for case in ('worker_import', 'docx_md'):
        cases[case] = {'before': [], 'after': []}
        for index in range(10):
            for label, cwd in ([('before', before), ('after', root)] if index % 2 == 0 else [('after', root), ('before', before)]):
                if case == 'worker_import':
                    result = measure([sys.executable, '-c', 'import backend.worker'], env, cwd)
                else:
                    job = folder / ('job-' + uuid.uuid4().hex)
                    job.mkdir()
                    shutil.copyfile(folder / 'sample.docx', job / 'input.docx')
                    (job / 'request.json').write_text(json.dumps({'input': 'docx', 'output': 'md'}))
                    result = measure([sys.executable, '-m', 'backend.worker', str(job)], env, cwd)
                    result['output_bytes'] = (job / 'result.md').stat().st_size
                    shutil.rmtree(job)
                cases[case][label].append(result)
    report = {'method': '10 alternating paired runs; same Python, host, source and sampler', 'cases': cases,
              'summary': {case: {label: {'median_seconds': statistics.median(r['seconds'] for r in rows),
                                      'p95_seconds': max(r['seconds'] for r in rows),
                                      'peak_rss_mb': max(r['peak_rss_mb'] for r in rows)}
                                 for label, rows in groups.items()} for case, groups in cases.items()}}
    (root / 'verification/paired-performance.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report['summary'], indent=2))
