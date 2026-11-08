"""Portable config tests: all files stay inside temporary directories."""
import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'macos_service.py'


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SCRIPT.exists():
            spec = importlib.util.spec_from_file_location('macos_service', SCRIPT)
            cls.service = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.service)

    def setUp(self):
        self.assertTrue(SCRIPT.exists(), 'deployment/macos_service.py must exist')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'checkout with spaces'
        self.server = self.root / 'ui/code/web/server.py'
        self.server.parent.mkdir(parents=True)
        self.server.touch()
        (self.root / 'core_code').mkdir()
        self.home = self.base / 'home'
        self.credentials = self.base / 'credentials.json'
        self.credentials.write_text('SECRET SENTINEL: DO NOT READ')
        self.kw = dict(root=self.root, home=self.home, python=Path(sys.executable),
                       cloudflared=Path(sys.executable),
                       tunnel_id='12345678-1234-1234-1234-123456789abc',
                       credentials_file=self.credentials, hostname='samreiter.com', port=8124)

    def test_root_discovery_uses_layout_not_cwd(self):
        self.assertEqual(self.service.find_root(self.server), self.root.resolve())
        with self.assertRaises(ValueError):
            self.service.find_root(self.base / 'missing.py')

    def test_configuration_roundtrips_and_contains_no_credentials_content(self):
        plists, config_path, config = self.service.generate_config(**self.kw)
        self.assertEqual(config_path, self.home / '.cloudflared/mandelbrot.yml')
        tunnel = json.loads(config)  # JSON is a YAML subset; no YAML dependency.
        self.assertEqual(tunnel['tunnel'], self.kw['tunnel_id'])
        self.assertEqual(tunnel['credentials-file'], str(self.credentials))
        self.assertEqual(tunnel['ingress'], [
            {'hostname': 'samreiter.com', 'service': 'http://127.0.0.1:8124'},
            {'service': 'http_status:404'}])
        self.assertEqual(set(plists), {'app', 'tunnel'})
        for name, plist in plists.items():
            self.assertEqual(plistlib.loads(plistlib.dumps(plist)), plist)
            self.assertTrue(plist['RunAtLoad'])
            self.assertTrue(plist['KeepAlive'])
            self.assertTrue(plist['StandardOutPath'].startswith(str(self.root / '.runtime')))
            self.assertNotIn('SECRET SENTINEL', str(plist) + config)
        app = plists['app']
        self.assertEqual(app['ProgramArguments'], [str(Path(sys.executable).absolute()), '-u', str(self.server), '--port', '8124'])
        self.assertEqual(app['WorkingDirectory'], str(self.root))
        self.assertEqual(app['EnvironmentVariables']['PUBLIC_ORIGIN'], 'https://samreiter.com')
        self.assertEqual(app['EnvironmentVariables']['HOME'], str(self.home))
        self.assertEqual(plists['tunnel']['ProgramArguments'], [str(Path(sys.executable).absolute()), 'tunnel', '--config', str(config_path), 'run', self.kw['tunnel_id']])

    def test_sage_environment_path_and_python_symlink_are_preserved(self):
        python = self.base / 'sage environment/bin/python'
        python.parent.mkdir(parents=True)
        python.symlink_to(sys.executable)
        plists, _, _ = self.service.generate_config(**dict(self.kw, python=python))
        app = plists['app']
        self.assertEqual(app['ProgramArguments'][0], str(python))
        self.assertEqual(app['EnvironmentVariables']['PATH'].split(':')[0], str(python.parent))
        self.assertIn('/usr/bin', app['EnvironmentVariables']['PATH'].split(':'))

    def test_custom_origin_and_port(self):
        plists, _, config = self.service.generate_config(**dict(self.kw, hostname='Test.Example.org', port=9001))
        self.assertEqual(plists['app']['EnvironmentVariables']['PUBLIC_ORIGIN'], 'https://test.example.org')
        self.assertEqual(plists['app']['ProgramArguments'][-1], '9001')
        self.assertEqual(json.loads(config)['ingress'][0]['service'], 'http://127.0.0.1:9001')

    def test_start_loaded_agent_does_not_replace_running_process(self):
        with patch.object(self.service.sys, 'platform', 'darwin'), patch.object(self.service.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([], 0)
            self.service.control('start', 'app', home=self.home)
            self.assertEqual(run.call_args_list[-1].args[0][1], 'kickstart')
            self.assertNotIn('-k', run.call_args_list[-1].args[0])

    def test_invalid_inputs_rejected(self):
        for key, value in [('port', 0), ('port', 65536), ('hostname', 'https://bad.example'),
                           ('hostname', 'bad\nexample'), ('tunnel_id', 'not-a-uuid')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.service.generate_config(**dict(self.kw, **{key: value}))

    def test_install_verifies_sage_without_reading_credentials_or_launching(self):
        real_open = Path.open
        def guarded_open(path, *args, **kwargs):
            if path == self.credentials:
                self.fail('credentials must never be opened')
            return real_open(path, *args, **kwargs)
        with patch.object(Path, 'open', guarded_open), patch.object(self.service.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([], 0)
            paths = self.service.install(**self.kw)
        run.assert_called_once_with([str(Path(sys.executable).absolute()), '-c', 'import sage.all'],
                                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.assertEqual(len(paths), 3)
        for path in paths:
            self.assertTrue(path.is_file())
            if path.suffix == '.plist':
                with path.open('rb') as stream:
                    plistlib.load(stream)
                if sys.platform == 'darwin':
                    subprocess.run(['/usr/bin/plutil', '-lint', str(path)], check=True, capture_output=True)
        self.assertEqual(paths[-1].stat().st_mode & 0o777, 0o600)
        self.assertTrue((self.root / '.runtime/logs').is_dir())
        self.assertTrue((self.root / '.runtime/cache').is_dir())

    def test_failed_sage_check_writes_nothing(self):
        with patch.object(self.service.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'python')):
            with self.assertRaises(ValueError):
                self.service.install(**self.kw)
        self.assertFalse(self.home.exists())
        self.assertFalse((self.root / '.runtime').exists())

    def test_missing_executable_or_credentials_writes_nothing(self):
        for key in ('python', 'cloudflared', 'credentials_file'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.service.install(**dict(self.kw, **{key: self.base / 'missing'}))
        self.assertFalse(self.home.exists())

    def test_lifecycle_targets_gui_domain_and_only_requested_service(self):
        with patch.object(self.service.sys, 'platform', 'darwin'), patch.object(self.service.os, 'getuid', return_value=501), patch.object(self.service.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([], 0)
            self.service.control('restart', 'app', home=self.home)
            self.assertEqual(run.call_args_list[-1].args[0], ['/bin/launchctl', 'kickstart', '-k', 'gui/501/' + self.service.LABELS['app']])
            self.assertFalse(any(self.service.LABELS['tunnel'] in str(call) for call in run.call_args_list))
            run.reset_mock()
            self.service.control('stop', 'tunnel', home=self.home)
            self.assertEqual(run.call_args_list[-1].args[0], ['/bin/launchctl', 'bootout', 'gui/501/' + self.service.LABELS['tunnel']])

    def test_start_bootstraps_unloaded_service_and_status_reports_absent(self):
        with patch.object(self.service.sys, 'platform', 'darwin'), patch.object(self.service.os, 'getuid', return_value=501), patch.object(self.service.subprocess, 'run') as run:
            run.side_effect = [subprocess.CompletedProcess([], 1), subprocess.CompletedProcess([], 0)]
            self.service.control('start', 'app', home=self.home)
            self.assertEqual(run.call_args_list[-1].args[0], ['/bin/launchctl', 'bootstrap', 'gui/501', str(self.home / 'Library/LaunchAgents' / (self.service.LABELS['app'] + '.plist'))])
            run.side_effect = None
            run.return_value = subprocess.CompletedProcess([], 1)
            self.assertEqual(self.service.control('status', 'app', home=self.home), 1)

    def test_platform_guard_prevents_launchctl(self):
        with patch.object(self.service.sys, 'platform', 'linux'), patch.object(self.service.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                self.service.control('start', 'all', home=self.home)
            run.assert_not_called()

    def test_cli_help(self):
        for args in (['--help'], ['install', '--help'], ['restart', '--help']):
            result = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('usage:', result.stdout)


if __name__ == '__main__':
    unittest.main()
