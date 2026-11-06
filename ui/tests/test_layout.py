"""Single-checkout layout regressions; no Sage installation required."""
import ast
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LayoutTests(unittest.TestCase):
    def test_server_resolves_core_in_combined_checkout(self):
        tree = ast.parse((ROOT / 'code/web/server.py').read_text())
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == 'CORE_DIR'
                                  for target in node.targets))
        actual = eval(compile(ast.Expression(assignment.value), '<CORE_DIR>', 'eval'), {'ROOT': ROOT})
        self.assertEqual(actual, ROOT.parent / 'core_code')
        self.assertTrue((actual / 'mandelbrot.sage').is_file())

    def test_launcher_finds_combined_core_before_invoking_server(self):
        runtime = ROOT / '.runtime/tests'
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as directory:
            fake = Path(directory) / 'sage'
            fake.write_text('#!/bin/bash\nif [[ "$1" == "-python" && "$2" != "-c" ]]; then printf "SERVER:%s\\n" "$2"; fi\n')
            fake.chmod(0o755)
            env = dict(os.environ, SAGE=str(fake), EXPLORER_CHECK_ONLY='0')
            result = subprocess.run(['bash', str(ROOT / 'launch.sh')], env=env,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('SERVER:' + str(ROOT / 'code/web/server.py'), result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
