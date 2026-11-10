"""Real Sage transport tests for page snapshots and core point plots."""
import importlib.util
import json

from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rays_server', ROOT / 'code/web/server.py')
assert spec is not None and spec.loader is not None
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class SaveFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.runtime')
        self.directory = Path(self.temp.name)
        self.setting = patch.object(server, 'SAVES_DIR', self.directory, create=True)
        self.setting.start()

    def tearDown(self):
        self.setting.stop()
        self.temp.cleanup()

    def save(self, suffix, values):
        server.sage.all.save(values, str(self.directory / f'psi_coefficients_{suffix}.sobj'))


class SnapshotTests(SaveFixture):
    def test_numeric_winner_only_loaded_and_actual_count(self):
        self.save(9, [1])
        self.save(10, [1, 2, 3])
        self.save('bad', [1])
        (self.directory / 'psi_coefficients.sobj').write_bytes(b'not a save')
        with patch.dict(server.CORE, load_psi=Mock(wraps=server.CORE.get('load_psi'))):
            session = server.coefficient_session()
            self.assertEqual(session['coefficient_count'], 3)
            server.CORE['load_psi'].assert_called_once_with(self.directory / 'psi_coefficients_10.sobj')

    def test_snapshot_stable_and_new_page_sees_new_save(self):
        self.save(9, [1])
        first = server.coefficient_session()
        payload = dict(session_token=first['session_token'], expression='t + I', variable='t',
                       start=1, end=2, step=.25, curve_id='a', request_revision=1)
        before = server.parametric_curve(payload)
        self.save(9, [8, 9, 10])
        self.assertEqual(server.parametric_curve(payload), before)
        self.save(10, [2, 3])
        after = server.parametric_curve(payload)
        self.assertEqual(before, after)
        self.assertEqual(first['coefficient_count'], 1)
        self.assertEqual(server.coefficient_session()['coefficient_count'], 2)
        with self.assertRaisesRegex(ValueError, 'session'):
            server.parametric_curve(dict(payload, session_token='../anything.sobj'))

    def test_missing_and_corrupt_winner_do_not_fall_back(self):
        with self.assertRaisesRegex(ValueError, 'coefficient'):
            server.coefficient_session()
        self.save(9, [1])
        (self.directory / 'psi_coefficients_10.sobj').write_bytes(b'broken')
        with self.assertRaisesRegex(ValueError, 'coefficient'):
            server.coefficient_session()
        self.assertTrue(server.curves()['curves'])


class CurveTests(SaveFixture):
    def setUp(self):
        super().setUp()
        self.save(1, [server.sage.all.QQ(-1)/2, server.sage.all.QQ(1)/8])
        self.session = server.coefficient_session()
        self.payload = dict(session_token=self.session['session_token'], expression='r*exp(I*pi/4)',
                            variable='r', start=1, end=2, step=.25,
                            curve_id='curve-1', request_revision=2)

    def test_paired_primitives_match_core_and_render_with_sage(self):
        result = server.parametric_curve(self.payload)
        r = server.sage.all.var('r')
        expression = r * server.sage.all.exp(server.sage.all.I * server.sage.all.pi/4)
        psi, _ = server.CORE['load_psi'](self.directory / 'psi_coefficients_1.sobj')
        for plane, helper, extra in [('source', 'plot_parametric', {}),
                                      ('image', 'plot_external_rays', {'psi': psi})]:
            graphics = server.CORE[helper](server.Graphics(), expression, parametric_variable=r,
                                           sample_range=(1., 2.), step_size=.25, **extra)
            graphics.save(str(ROOT / '.runtime' / f'rays-{plane}.png'))
            primitives = result[plane]
            self.assertEqual(len(primitives), len(graphics))
            for actual, expected in zip(primitives, graphics):
                self.assertEqual(actual['geometry'], 'points')
                self.assertEqual(actual['points'], [dict(real=float(x), imag=float(y))
                                                   for x, y in zip(expected.xdata, expected.ydata)])
                self.assertEqual(actual['style']['rgbcolor'], list(server.to_mpl_color(expected.options()['rgbcolor'])))
                self.assertEqual(actual['style']['size'], float(expected.options()['size']))
        self.assertEqual(result['curve_id'], 'curve-1')
        self.assertEqual(result['request_revision'], 2)
        self.assertEqual(result['session_token'], self.session['session_token'])
        json.dumps(result, allow_nan=False)

    def test_safe_symbolic_expressions_and_validation_without_work_caps(self):
        for changes in ({'expression': '__import__("os")'}, {'expression': 'r.real()'},
                        {'expression': 'x+r'}, {'variable': 'pi'}, {'variable': '__x'},
                        {'start': float('nan')}, {'end': float('inf')}, {'step': 0},
                        {'step': -1}, {'start': 2}, {'expression': '[r]'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                server.parametric_curve(dict(self.payload, **changes))
        self.assertEqual(server.parametric_curve(dict(self.payload, start=1000001,
                         end=1000002, step=2))['source'], [])
        self.assertTrue(server.parametric_curve(dict(self.payload, expression='sqrt(r)+sin(r)+I'))['image'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
