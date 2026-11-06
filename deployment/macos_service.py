#!/usr/bin/env python3
"""Generate user LaunchAgents; activate only via an explicit lifecycle command."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import sys
from uuid import UUID

LABELS = {'app': 'org.mandelbrot.app', 'tunnel': 'org.mandelbrot.tunnel'}


def absolute(path):
    # Do not resolve executable symlinks: venv Python needs its original path.
    return Path(path).expanduser().absolute()


def find_root(source=None):
    """Find the combined repository from this script, not the caller's cwd."""
    for root in Path(source or __file__).resolve().parents:
        if (root / 'core_code').is_dir() and (root / 'ui/code/web/server.py').is_file():
            return root
    raise ValueError('Place deployment/ in the repository containing core_code/ and ui/code/web/server.py')


def generate_config(*, root, home, python, cloudflared, tunnel_id,
                    credentials_file, hostname='samreiter.com', port=8124):
    """Pure configuration generation; credentials are referenced, never opened.

    Return (plist dictionaries keyed by service, tunnel config path, YAML text).
    JSON output is valid YAML and safely quotes paths without a YAML dependency.
    """
    root, home = absolute(root), absolute(home)
    python, cloudflared = absolute(python), absolute(cloudflared)
    credentials_file = absolute(credentials_file)
    tunnel_id = str(UUID(tunnel_id))
    if not 1 <= port <= 65535:
        raise ValueError('port must be between 1 and 65535')
    hostname = hostname.lower()
    if len(hostname) > 253 or not all(
        re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
        for label in hostname.split('.')
    ):
        raise ValueError('hostname must be a DNS name, without scheme, port or path')
    runtime = root / '.runtime'
    config_path = home / '.cloudflared/mandelbrot.yml'
    env = {'HOME': str(home), 'PUBLIC_ORIGIN': 'https://' + hostname,
           'PATH': str(python.parent) + ':/usr/bin:/bin:/usr/sbin:/sbin',
           'XDG_CACHE_HOME': str(runtime / 'cache'),
           'MPLCONFIGDIR': str(runtime / 'cache/matplotlib'),
           'DOT_SAGE': str(runtime / 'cache/sage')}
    commands = {
        'app': [str(python), '-u', str(root / 'ui/code/web/server.py'), '--port', str(port)],
        'tunnel': [str(cloudflared), 'tunnel', '--config', str(config_path), 'run', tunnel_id],
    }
    plists = {}
    for service, command in commands.items():
        plists[service] = {
            'Label': LABELS[service], 'ProgramArguments': command,
            'WorkingDirectory': str(root), 'RunAtLoad': True, 'KeepAlive': True,
            'StandardOutPath': str(runtime / 'logs' / (service + '.out.log')),
            'StandardErrorPath': str(runtime / 'logs' / (service + '.err.log')),
            'EnvironmentVariables': env if service == 'app' else {'HOME': str(home)},
        }
    config = {'tunnel': tunnel_id, 'credentials-file': str(credentials_file),
              'ingress': [{'hostname': hostname, 'service': 'http://127.0.0.1:' + str(port)},
                          {'service': 'http_status:404'}]}
    return plists, config_path, json.dumps(config, indent=2) + '\n'


def install(**options):
    """Validate dependencies and write configs only; never call launchctl."""
    plists, config_path, config = generate_config(**options)
    root, home = absolute(options['root']), absolute(options['home'])
    if not (root / 'ui/code/web/server.py').is_file() or not (root / 'core_code').is_dir():
        raise ValueError('root must contain core_code/ and ui/code/web/server.py')
    for name in ('python', 'cloudflared'):
        path = absolute(options[name])
        if not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError(name + ' must be an executable file')
    if not absolute(options['credentials_file']).is_file():
        raise ValueError('credentials-file must exist (contents are never read)')
    try:
        subprocess.run([str(absolute(options['python'])), '-c', 'import sage.all'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError('Supplied Python cannot import sage.all; activate the Sage environment and retry') from exc
    for directory in ('logs', 'cache', 'cache/sage', 'cache/matplotlib'):
        (root / '.runtime' / directory).mkdir(parents=True, exist_ok=True)
    agents = home / 'Library/LaunchAgents'
    agents.mkdir(parents=True, exist_ok=True)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    # Config has paths, not secrets, but keep it private as a precaution.
    config_path.touch(mode=0o600, exist_ok=True)
    config_path.chmod(0o600)
    config_path.write_text(config, encoding='utf-8')
    paths = []
    for service, plist in plists.items():
        path = agents / (LABELS[service] + '.plist')
        path.write_bytes(plistlib.dumps(plist))
        paths.append(path)
    return paths + [config_path]


def control(action, service='all', *, home=None):
    """Manage only our user agents. status returns nonzero if any are unloaded."""
    if sys.platform != 'darwin':
        raise ValueError('launchctl lifecycle commands require macOS in a logged-in GUI user session')
    home = absolute(home if home is not None else Path.home())
    domain = 'gui/' + str(os.getuid())
    failed = 0
    for name in LABELS if service == 'all' else (service,):
        target = domain + '/' + LABELS[name]
        loaded = subprocess.run(['/bin/launchctl', 'print', target],
                                stdout=None if action == 'status' else subprocess.DEVNULL,
                                stderr=None if action == 'status' else subprocess.DEVNULL).returncode == 0
        if action == 'status':
            failed |= int(not loaded)
            continue
        if action == 'stop':
            if loaded:
                subprocess.run(['/bin/launchctl', 'bootout', target], check=True)
        elif not loaded:
            path = home / 'Library/LaunchAgents' / (LABELS[name] + '.plist')
            subprocess.run(['/bin/launchctl', 'bootstrap', domain, str(path)], check=True)
        else:
            command = ['/bin/launchctl', 'kickstart']
            if action == 'restart':
                command.append('-k')
            subprocess.run(command + [target], check=True)
    return failed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    setup = commands.add_parser('install', help='write configs; does NOT load or restart agents')
    setup.add_argument('--python', type=Path, required=True, help='absolute Sage-enabled Python executable')
    setup.add_argument('--cloudflared', type=Path, required=True, help='cloudflared executable')
    setup.add_argument('--tunnel-id', required=True, help='named tunnel UUID (not a token)')
    setup.add_argument('--credentials-file', type=Path, required=True, help='existing tunnel JSON; never read')
    setup.add_argument('--hostname', default='samreiter.com')
    setup.add_argument('--port', type=int, default=8124)
    setup.add_argument('--home', type=Path, default=None, help='override output home (for isolated configuration tests)')
    for action in ('start', 'stop', 'restart', 'status'):
        command = commands.add_parser(action)
        command.add_argument('service', choices=['app', 'tunnel', 'all'], nargs='?', default='all')
        command.add_argument('--home', type=Path, default=None, help='home used during install')
    args = vars(parser.parse_args(argv))
    action = args.pop('command')
    try:
        if action == 'install':
            args['root'] = find_root()
            args['home'] = args['home'] if args['home'] is not None else Path.home()
            for path in install(**args):
                print('Wrote', path)
            print('Not activated. Use start explicitly; RunAtLoad also applies at future GUI logins.')
            return 0
        return control(action, **args)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, 'error: ' + str(exc) + '\n')


if __name__ == '__main__':
    sys.exit(main())
