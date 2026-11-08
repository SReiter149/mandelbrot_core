"""Portable launcher tests; fake Python checks transport argv, not Sage mathematics."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PythonLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.log = self.base / 'argv.txt'
        self.python = self.base / 'environment with spaces' / 'bin' / 'python'
        self.python.parent.mkdir(parents=True)
        self.python.write_text('#!/bin/bash\nif [[ "$1" == "-c" ]]; then exit 0; fi\nprintf "%s\\n" "$@" > "$LAUNCH_TEST_LOG"\n')
        self.python.chmod(0o755)
        self.env = dict(os.environ, SAGE_PYTHON=str(self.python), SAGE='/not/a/sage',
                        LAUNCH_TEST_LOG=str(self.log), PORT='8199')
        self.env.pop('EXPLORER_CHECK_ONLY', None)

    def run_launcher(self):
        return subprocess.run(['/bin/bash', str(ROOT / 'launch.sh')],
                              cwd=self.base, env=self.env, capture_output=True, text=True)

    def test_python_override_starts_server_with_correct_argv(self):
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(),
                         [str(ROOT / 'code/web/server.py'), '--port', '8199'])

    def test_invalid_override_never_falls_back(self):
        self.env['SAGE_PYTHON'] = '/not/a/python'
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SAGE_PYTHON', result.stderr)
        self.assertFalse(self.log.exists())

    def test_python_without_sage_is_rejected(self):
        self.python.write_text('#!/bin/bash\nexit 1\n')
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SAGE_PYTHON', result.stderr)

    def test_check_only_does_not_start_server(self):
        self.env['EXPLORER_CHECK_ONLY'] = '1'
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.log.exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
