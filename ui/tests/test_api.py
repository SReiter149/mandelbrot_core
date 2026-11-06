"""Real Sage + real HTTP integration tests; no substitute math."""
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]

class APITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('ui_server', ROOT / 'code/web/server.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.server = cls.module.HTTPServer(('127.0.0.1', 0), cls.module.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, path, payload=None, headers=None):
        req = Request(self.base + path, data=None if payload is None else json.dumps(payload).encode(),
                      headers=headers or {'Content-Type': 'application/json'})
        try:
            with urlopen(req) as response:
                return response.status, response.read().decode()
        except HTTPError as error:
            return error.code, error.read().decode()

    def test_health_live_core(self):
        status, body = self.request('/api/health')
        self.assertEqual(status, 200)
        self.assertEqual(Path(json.loads(body)['core']), ROOT.parent / 'core_code')

    def test_curves_are_users_graphics(self):
        status, body = self.request('/api/mandelbrot')
        self.assertEqual(status, 200)
        curves = json.loads(body)['curves']
        original = self.module.MANDELBROT_GRAPHICS
        self.assertEqual(len(curves), len(original))
        for curve, primitive in zip(curves, original):
            self.assertEqual(curve, [{'real': float(x), 'imag': float(y)} for x, y in zip(primitive.xdata, primitive.ydata)])

    def test_curve_styles_preserve_live_sage_options(self):
        status, body = self.request('/api/mandelbrot')
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertIn('styles', result)
        for style, primitive in zip(result['styles'], self.module.MANDELBROT_GRAPHICS):
            options = primitive.options()
            self.assertEqual(style['linestyle'], options.get('linestyle', '-'))
            self.assertEqual(style['marker'], options.get('marker', None))
            self.assertEqual(style['markersize'], float(options.get('markersize', 6)))
            self.assertEqual(style['rgbcolor'], list(self.module.to_mpl_color(options['rgbcolor'])))

    def test_curves_include_period_three_basin(self):
        status, body = self.request('/api/mandelbrot')
        self.assertEqual(status, 200)
        # One cardioid, one period-two circle, and the core's three new branches.
        self.assertEqual(len(json.loads(body)['curves']), 5)

    def test_sage_point_expressions(self):
        for expression, expected in (
            ('sqrt(2) * I / pi', self.module.CORE['sqrt'](2) * self.module.CORE['I'] / self.module.CORE['pi']),
            ('3*I + 4', self.module.CC(4, 3)),
            ('I^2', -1),
        ):
            status, body = self.request('/api/point', {'expression': expression})
            self.assertEqual(status, 200, body)
            self.assertEqual(json.loads(body)['point'], self.module.point_payload(self.module.CC(expected)))

    def test_point_expressions_reject_code_and_invalid_values(self):
        for expression in ('', 'unknown + I', '__import__("os")', 'sqrt.__globals__',
                           '[1, 2]', '1/0', 'Infinity', 'open("file")', 'x = 2'):
            status, body = self.request('/api/point', {'expression': expression})
            self.assertEqual(status, 422, body)

    def test_orbits_match_live_get_path(self):
        for c in ({'real': 0, 'imag': 0}, {'real': -1, 'imag': 0}, {'real': .1, 'imag': .2}, {'real': 2, 'imag': 0}):
            payload = dict(c=c, start={'real': 0, 'imag': 0}, steps=30,
                           trajectory_id='selection-1', trajectory_generation=1, request_revision=2)
            status, body = self.request('/api/trajectory', payload)
            self.assertEqual(status, 200)
            result = json.loads(body)
            value = self.module.CC(c['real'], c['imag'])
            expected = self.module.CORE['get_path'](self.module.CC(0), lambda z: self.module.CORE['quadratic'](z, value), iterations=30)
            self.assertEqual(result['points'], [self.module.point_payload(p) for p in expected])
            self.assertEqual(result['request_revision'], 2)

    def test_vector_field_and_explicit_core_error(self):
        status, body = self.request('/api/rebuild', dict(grid_generation=1, c={'real': 0, 'imag': .25},
            bounds=dict(xmin=-1, xmax=1, ymin=-1, ymax=1), spacing=.5,
            classification_iterations=10, convergence_threshold=.001, vector_length=.1))
        self.assertEqual(status, 200)
        messages = [json.loads(line) for line in body.splitlines()]
        self.assertTrue(any(m['type'] == 'vector_batch' and m['samples'] for m in messages))
        self.assertEqual(messages[-1]['type'], 'complete')
        self.assertTrue(any(m['type'] == 'classification_batch' for m in messages))

    def test_validation_and_safety(self):
        for payload in ([], {}, {'c': {'real': 'NaN', 'imag': 0}, 'steps': 10}, {'c': {'real': 0, 'imag': 0}, 'steps': 1001}):
            self.assertEqual(self.request('/api/trajectory', payload)[0], 422)
        self.assertEqual(self.request('/api/trajectory', {}, {'Content-Type': 'application/json', 'Origin': 'https://example.com'})[0], 403)
        self.assertEqual(self.request('/api/trajectory', {}, {'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.request('/static/../../AGENTS.md')[0], 404)

    def test_frontend_entrypoint(self):
        status, body = self.request('/')
        self.assertEqual(status, 200)
        self.assertIn('Mandelbrot explorer', body)
        self.assertIn('Vector field', body)

if __name__ == '__main__':
    unittest.main(verbosity=2)
