"""Discovery fixtures test launcher selection, not Sage functionality."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / '.runtime/tests'
TMP.mkdir(parents=True, exist_ok=True)

class DiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TMP)
        self.base = Path(self.temp.name)
        self.env = dict(os.environ, HOME=str(self.base), PATH='/usr/bin:/bin')
        for key in ('SAGE', 'SAGE_ROOT', 'CONDA_PREFIX', 'VIRTUAL_ENV', 'MAMBA_ROOT_PREFIX'):
            self.env.pop(key, None)

    def tearDown(self):
        self.temp.cleanup()

    def fake(self, path, ok=True):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#!/bin/bash\nexit '+('0' if ok else '1')+'\n')
        path.chmod(0o755)
        return str(path)

    def discover(self):
        # Restrict default system roots so tests never depend on host installations.
        script = 'source scripts/find_sage.sh; SAGE_SYSTEM_DIRS=("$HOME/global"); SAGE_APP_DIRS=("$HOME/Applications"); discover_sage'
        return subprocess.run(['/bin/bash', '-c', script], cwd=ROOT, env=self.env, text=True, capture_output=True)

    def test_explicit_sage_wins_and_paths_with_spaces_work(self):
        sage = self.fake(self.base/'my sage/bin/sage')
        self.env['SAGE'] = sage
        result = self.discover()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), sage)

    def test_invalid_explicit_override_is_not_silently_ignored(self):
        self.env['SAGE'] = '/not/installed/sage'
        self.assertNotEqual(self.discover().returncode, 0)

    def test_environment_then_path(self):
        sage = self.fake(self.base/'active/bin/sage')
        self.env['CONDA_PREFIX'] = str(self.base/'active')
        self.env['PATH'] = str(self.base/'other') + ':/usr/bin:/bin'
        self.fake(self.base/'other/sage')
        self.assertEqual(self.discover().stdout.strip(), sage)
        self.env.pop('CONDA_PREFIX')
        self.assertEqual(self.discover().stdout.strip(), str(self.base/'other/sage'))

    def test_broken_path_candidate_falls_back_to_global(self):
        self.fake(self.base/'other/sage', False)
        self.env['PATH'] = str(self.base/'other') + ':/usr/bin:/bin'
        sage = self.fake(self.base/'global/sage')
        self.assertEqual(self.discover().stdout.strip(), sage)

    def test_current_macos_bundle_layout(self):
        sage = self.fake(self.base/'Applications/SageMath-10-9.app/Contents/Frameworks/Sage.framework/Versions/Current/venv/bin/sage')
        self.assertEqual(self.discover().stdout.strip(), sage)

    def test_user_micromamba_environment(self):
        sage = self.fake(self.base/'micromamba/envs/math/bin/sage')
        self.assertEqual(self.discover().stdout.strip(), sage)

    def test_missing_sage_has_install_help(self):
        result = self.discover()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('brew install --cask sage', result.stderr)

if __name__ == '__main__':
    unittest.main(verbosity=2)
