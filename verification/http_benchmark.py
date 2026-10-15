"""Measures a real local HTTP upload/download with httpcore trace boundaries."""
import json
from pathlib import Path
import statistics
import time
import httpx

observations = []
with httpx.Client(base_url='http://127.0.0.1:8000', timeout=180) as client:
    start = time.perf_counter()
    client.get('/api/health').raise_for_status()
    health = (time.perf_counter() - start) * 1000
    for _ in range(5):
        events = {}
        def trace(name, info):
            events[name] = time.perf_counter()
        with Path('verification/local/browser.xlsx').open('rb') as source:
            start = time.perf_counter()
            with client.stream('POST', '/api/convert', files={'file': ('sample.xlsx', source)},
                               data={'output_format': 'csv'}, extensions={'trace': trace}) as response:
                first_byte = time.perf_counter()
                response.raise_for_status()
                payload = response.read()
                end = time.perf_counter()
                observations.append({'total_ms': (end - start) * 1000,
                                     'headers_ms': (first_byte - start) * 1000,
                                     'result_transfer_ms': (end - first_byte) * 1000,
                                     'upload_ms': (events['http11.send_request_body.complete'] - events['http11.send_request_body.started']) * 1000,
                                     'server_timing': response.headers.get('server-timing'), 'bytes': len(payload)})
report = {'environment': 'Windows localhost, warm API, synthetic 2-sheet workbook, 5 sequential requests',
          'initial_health_ms': health, 'median_total_ms': statistics.median(r['total_ms'] for r in observations),
          'observations': observations}
Path('verification/http-performance.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
