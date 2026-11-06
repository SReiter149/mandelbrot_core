"""Transport regression checks plus real live-core batching checks."""
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.request import Request, urlopen

spec = importlib.util.spec_from_file_location('stream_server', Path(__file__).resolve().parents[1] / 'code/web/server.py')
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)
PAYLOAD = dict(c=dict(real=0, imag=.25), bounds=dict(xmin=-1, xmax=1, ymin=-1, ymax=1), spacing=.1,
               convergence_threshold=.001, vector_length=.05, classification_iterations=5, grid_generation=1)

class StreamingTests(unittest.TestCase):
    def test_real_core_emits_multiple_bounded_batches(self):
        messages = list(server_module.grid_messages(server_module.rebuild(PAYLOAD)))
        for kind in ('vector_batch', 'classification_batch'):
            batches = [m for m in messages if m['type'] == kind]
            self.assertGreater(len(batches), 1, kind)
            self.assertTrue(all(len(m['samples']) <= 128 for m in batches))
        self.assertEqual(messages[-1]['type'], 'complete')

    def test_first_line_arrives_before_generator_finishes(self):
        # Controlled generator isolates HTTP buffering, not mathematical behavior.
        release = threading.Event()
        received = threading.Event()
        original = server_module.grid_messages
        def controlled(config):
            yield {'type': 'accepted', 'point_count': 1}
            release.wait(3)
            yield {'type': 'complete'}
        server_module.grid_messages = controlled
        server = server_module.HTTPServer(('127.0.0.1', 0), server_module.Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        errors = []
        def read():
            try:
                req = Request(f'http://127.0.0.1:{server.server_port}/api/rebuild', data=json.dumps(PAYLOAD).encode(), headers={'Content-Type':'application/json'})
                with urlopen(req, timeout=5) as response:
                    self.assertEqual(json.loads(response.readline())['type'], 'accepted')
                    received.set()
                    self.assertEqual(json.loads(response.readline())['type'], 'complete')
            except Exception as exc:
                errors.append(exc)
        client = threading.Thread(target=read, daemon=True)
        client.start()
        try:
            self.assertTrue(received.wait(1), 'first line buffered until computation finished')
        finally:
            release.set()
            client.join(5)
            server.shutdown()
            server.server_close()
            worker.join()
            server_module.grid_messages = original
        self.assertFalse(errors, errors)

if __name__ == '__main__':
    unittest.main(verbosity=2)
