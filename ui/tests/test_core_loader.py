"""Real-Sage checks for the shared source-loading entry point."""
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CoreLoaderTests(unittest.TestCase):
    def load_into(self, namespace):
        from sage.repl.load import load
        entry = ROOT / 'load_core.sage'
        self.assertTrue(entry.is_file(), 'Shared load_core.sage entry point is missing')
        load(str(entry), namespace)

    def test_loads_entire_core_and_preserves_caller_paths(self):
        from sage.all import CC
        caller = str(ROOT / 'tests/math/example.py')
        namespace = {'__file__': caller, 'root': 'caller-owned root'}
        self.load_into(namespace)
        for name in ('get_fixed_points', 'plot_external_rays', 'addMandelBrotSoFar',
                     'add_points', 'complex_label', 'analysis_vector_field_rect'):
            self.assertTrue(callable(namespace[name]), name)
        self.assertEqual(namespace['INFINITY'], 1000)
        self.assertEqual(namespace['__file__'], caller)
        self.assertEqual(namespace['root'], 'caller-owned root')
        self.assertEqual(namespace['quadratic'](CC(2), CC(1)), CC(5))

    def test_loading_does_not_depend_on_working_directory(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                namespace = {'__file__': str(ROOT.parent / 'run_code/explore_rays.sage')}
                self.load_into(namespace)
                self.assertTrue(callable(namespace['get_fixed_points']))
            finally:
                os.chdir(original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
