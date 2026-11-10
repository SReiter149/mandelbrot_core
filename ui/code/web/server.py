"""Loopback-bound Sage UI transport with optional public-origin tunnel support.

Run with Sage's Python; Sage load preparses in memory (no copied core files).
The single request worker deliberately serializes Sage calls.
"""
import argparse
import ast
import json
import math
import mimetypes
import os
import re
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from sage.all import CC, Graphics
import sage.all
from sage.repl.load import load
from sage.plot.colors import to_mpl_color

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / 'code/web/static'
PUBLIC_ORIGIN = os.environ.get('PUBLIC_ORIGIN', '').rstrip('/')
CORE_DIR = ROOT.parent / 'core_code'
CORE = dict(vars(sage.all))
for filename in ('math_functions.sage', 'plotting_functions.sage', 'mandelbrot.sage', 'external_rays.sage'):
    load(str(CORE_DIR / filename), CORE)

SAVES_DIR = Path(os.environ.get('PSI_SAVES_DIR', str(ROOT.parent / 'saves')))
# Opaque, server-issued identities hold the loaded psi, never a client-supplied path.
COEFFICIENT_SESSIONS = {}


def coefficient_session():
    candidates = [(int(match[1]), path) for path in SAVES_DIR.glob('psi_coefficients_*.sobj')
                  if (match := re.fullmatch(r'psi_coefficients_([0-9]+)\.sobj', path.name))
                  and path.is_file()]
    if not candidates:
        raise ValueError('No numbered psi coefficient saves found; configure PSI_SAVES_DIR and refresh the page')
    selected = max(candidates, key=lambda item: (item[0], item[1].name))[1]
    try:
        psi, coefficients = CORE['load_psi'](selected)
        if not isinstance(coefficients, list):
            raise ValueError('Expected a coefficient list')
    except Exception as exc:
        raise ValueError(f'Unable to load selected coefficient save {selected.name}: {exc}') from exc
    token = secrets.token_urlsafe(32)
    COEFFICIENT_SESSIONS[token] = (psi, len(coefficients))
    return dict(session_token=token, coefficient_count=len(coefficients))


def number(value, label):
    if isinstance(value, bool):
        raise ValueError(f'{label} must be finite')
    result = float(value)
    if not math.isfinite(result) or abs(result) > 1000000:
        raise ValueError(f'{label} must be finite and at most 1,000,000 in magnitude')
    return result


# JSON integers must round-trip exactly through the JavaScript client.
MAX_SAFE_INTEGER = 9007199254740991


def integer(value, label, maximum=MAX_SAFE_INTEGER, minimum=1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{label} must be an integer from {minimum} to {maximum}')
    return value


def complex_input(value, label):
    if not isinstance(value, dict):
        raise ValueError(f'{label} must contain real and imag')
    return CC(number(value.get('real'), label), number(value.get('imag'), label))


def point_payload(value):
    return {'real': float(value.real()), 'imag': float(value.imag())}


# Arithmetic input only: never expose Python statements, attributes, or arbitrary calls.
EXPRESSION_NAMES = {name: getattr(sage.all, name) for name in
                    ('I', 'pi', 'e', 'golden_ratio', 'sqrt', 'sin', 'cos', 'tan', 'exp', 'log')}
EXPRESSION_NAMES['abs'] = abs
EXPRESSION_NAMES['i'] = sage.all.I


def arithmetic_expression(expression, variable=None):
    names = dict(EXPRESSION_NAMES)
    if variable is not None:
        if (not isinstance(variable, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', variable)
                or len(variable) > 32 or variable in names):
            raise ValueError('Parameter variable must be a nonreserved mathematical name')
        names[variable] = sage.all.SR.var(variable)
    if not isinstance(expression, str) or not 0 < len(expression.strip()) <= 256:
        raise ValueError('Enter a Sage arithmetic expression (up to 256 characters)')
    try:
        tree = ast.parse(expression.strip().replace('^', '**'), mode='eval')
        allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name,
                   ast.Load, ast.Call, ast.Add, ast.Sub, ast.Mult, ast.Div,
                   ast.Pow, ast.UAdd, ast.USub)
        nodes = list(ast.walk(tree))
        if len(nodes) > 100:
            raise ValueError('Expression is too complex')
        for node in nodes:
            if not isinstance(node, allowed):
                raise ValueError('Only arithmetic, constants, and named math functions are allowed')
            if isinstance(node, ast.Constant) and type(node.value) not in (int, float, complex):
                raise ValueError('Only numeric literals are allowed')
            if isinstance(node, ast.Name) and node.id not in names:
                raise ValueError(f'Unknown constant or function: {node.id}')
            if isinstance(node, ast.Call) and (not isinstance(node.func, ast.Name)
                    or not callable(EXPRESSION_NAMES.get(node.func.id)) or node.keywords):
                raise ValueError('Only named math functions with positional arguments are allowed')
        return sage.all.sage_eval(expression.strip(), locals=names)
    except Exception as exc:
        raise ValueError(f'Invalid Sage point expression: {exc}') from exc


def expression_point(payload):
    try:
        point = point_payload(CC(arithmetic_expression(payload.get('expression'))))
        complex_input(point, 'Point')
        return {'point': point}
    except Exception as exc:
        raise ValueError(f'Invalid Sage point expression: {exc}') from exc


def curve_config(payload):
    token = payload.get('session_token')
    if not isinstance(token, str) or token not in COEFFICIENT_SESSIONS:
        raise ValueError('Unknown coefficient page session; refresh the page')
    variable = payload.get('variable')
    expression = sage.all.SR(arithmetic_expression(payload.get('expression'), variable))
    if variable is None:
        raise ValueError('Parameter variable is required')
    values = []
    for key in ('start', 'end', 'step'):
        value = payload.get(key)
        if isinstance(value, bool):
            raise ValueError(f'{key} must be finite')
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f'{key} must be finite')
        values.append(value)
    start, end, step = values
    if start >= end or step <= 0:
        raise ValueError('Parameter range must increase and step size must be positive')
    return token, expression, sage.all.SR.var(variable), (start, end), step


def graphics_primitives(graphics):
    from sage.plot.point import Point
    result = []
    for primitive in graphics:
        options = primitive.options()
        points = [dict(real=float(x), imag=float(y)) for x, y in zip(primitive.xdata, primitive.ydata)]
        if not all(math.isfinite(v) for point in points for v in point.values()):
            raise ValueError('Core plot returned nonfinite coordinates')
        is_point = isinstance(primitive, Point)
        result.append(dict(geometry='points' if is_point else 'path', points=points, style=dict(
            rgbcolor=[float(v) for v in to_mpl_color(options['rgbcolor'])],
            alpha=float(options.get('alpha', 1)), size=float(options.get('size', 10)),
            zorder=float(options.get('zorder', 2)),
            linestyle='' if is_point else options.get('linestyle', '-'),
            marker=options.get('marker', 'o' if is_point else None),
            markersize=float(options.get('markersize', 6)),
            thickness=float(options.get('thickness', 1)))))
    return result


def parametric_curve(payload):
    token, expression, variable, sample_range, step = curve_config(payload)
    kwargs = dict(parametric_variable=variable, sample_range=sample_range, step_size=step)
    source = CORE['plot_parametric'](Graphics(), expression, **kwargs)
    image = CORE['plot_external_rays'](Graphics(), expression, psi=COEFFICIENT_SESSIONS[token][0], **kwargs)
    return dict(source=graphics_primitives(source), image=graphics_primitives(image),
                session_token=token, coefficient_count=COEFFICIENT_SESSIONS[token][1],
                curve_id=payload.get('curve_id'), request_revision=payload.get('request_revision'))


def trajectory(payload):
    c = complex_input(payload.get('c'), 'c')
    start = complex_input(payload.get('start'), 'start')
    steps = integer(payload.get('steps'), 'steps', minimum=-MAX_SAFE_INTEGER)
    # No recurrence, termination, or classification logic belongs in this adapter.
    if steps < 0:
        path = CORE['get_pullback_paths'](c, start, iterations=abs(steps))
        reason = 'Returned by live get_pullback_paths (its own stopping rules)'
    elif steps == 0:
        path = [start]
        reason = 'Zero steps: target only'
    else:
        path = CORE['get_path'](start, lambda z: CORE['quadratic'](z, c), iterations=steps)
        reason = 'Returned by live get_path (its own stopping rules)'
    return dict(points=[point_payload(p) for p in path],
                geometry='path' if steps > 0 else 'points',
                termination_reason=reason,
                **{key: payload.get(key) for key in ('trajectory_id', 'trajectory_generation', 'request_revision')})


# Sage symbolic plotting initializes Maxima/ECL and must stay on the main thread.
# Keep the actual user's Graphics as the source; parametric_plot samples adaptively.
MANDELBROT_GRAPHICS = CORE['addMandelBrotSoFar'](Graphics())


def curves():
    return {'curves': [[{'real': float(x), 'imag': float(y)}
                        for x, y in zip(primitive.xdata, primitive.ydata)]
                       for primitive in MANDELBROT_GRAPHICS],
            'styles': [
                {'linestyle': primitive.options().get('linestyle', '-'),
                 'marker': primitive.options().get('marker', None),
                 'markersize': float(primitive.options().get('markersize', 6)),
                 'rgbcolor': [float(v) for v in to_mpl_color(primitive.options()['rgbcolor'])],
                 'thickness': float(primitive.options().get('thickness', 1)),
                 'alpha': float(primitive.options().get('alpha', 1))}
                for primitive in MANDELBROT_GRAPHICS]}



def rebuild(payload):
    c = complex_input(payload.get('c'), 'c')
    bounds = payload.get('bounds')
    if not isinstance(bounds, dict):
        raise ValueError('bounds must be an object')
    b = {key: number(bounds.get(key), key) for key in ('xmin', 'xmax', 'ymin', 'ymax')}
    if b['xmin'] >= b['xmax'] or b['ymin'] >= b['ymax']:
        raise ValueError('View bounds must increase')
    spacing = number(payload.get('spacing'), 'spacing')
    threshold = number(payload.get('convergence_threshold'), 'convergence_threshold')
    length = number(payload.get('vector_length'), 'vector_length')
    iterations = integer(payload.get('classification_iterations'), 'classification_iterations')
    generation = integer(payload.get('grid_generation'), 'grid_generation', 2147483647)
    if spacing <= 0 or threshold <= 0 or length <= 0:
        raise ValueError('Spacing, convergence threshold, and vector length must be positive')
    points = list(CORE['rect_point_sampler'](
        (b['xmin'], b['xmax']), (b['ymin'], b['ymax']), spacing))
    return c, points, iterations, threshold, length, generation


def grid_messages(config):
    c, points, iterations, threshold, length, generation = config
    def message(kind, **fields):
        return dict(type=kind, grid_generation=generation, **fields)
    yield message('accepted', point_count=len(points))
    stage = 'get_fixed_points'
    try:
        roots = CORE['get_fixed_points'](c)
        yield message('fixed_points', roots=[point_payload(z) for z in roots])
        stage = 'get_vector_field / add_vector_field'
        for offset in range(0, len(points), 128):
            batch = points[offset:offset + 128]
            field = CORE['get_vector_field'](batch, lambda z: CORE['quadratic'](z, c))
            graphics = CORE['add_vector_field'](Graphics(), field, vector_length=length)
            # Serialize the user's Arrow primitives, not a replacement vector formula.
            samples = [dict(start={'real': float(p.xtail), 'imag': float(p.ytail)},
                            end={'real': float(p.xhead), 'imag': float(p.yhead)},
                            color=[float(v) for v in p.options()['rgbcolor']], draw=True)
                       for p in graphics]
            yield message('vector_batch', samples=samples)
        stage = 'get_paths / classify_paths'
        for offset in range(0, len(points), 128):
            batch = points[offset:offset + 128]
            paths = CORE['get_paths'](batch, lambda z: CORE['quadratic'](z, c),
                                      iterations=iterations, convergence_threshold=threshold)
            classified = CORE['classify_paths'](paths, roots, convergence_threshold=threshold)
            # Preserve user's categories, including cycles, without inferring any ourselves.
            samples = [dict(point=point_payload(p), outcome=kind)
                       for index, kind in ((0, 'convergent'), (2, 'divergent'), (4, 'cycle'), (6, 'unresolved'))
                       for p in classified[index]]
            yield message('classification_batch', samples=samples)
        yield message('complete', elapsed_ms=0)
    except Exception as exc:
        yield message('error', error={'message': f'Live core {stage} failed: {type(exc).__name__}: {exc}. No substitute math was used.'})


class Handler(BaseHTTPRequestHandler):
    def send_data(self, status, content, content_type='application/json'):
        if not isinstance(content, bytes):
            content = json.dumps(content, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        try:
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def error(self, status, message):
        self.send_data(status, {'error': {'message': message}})

    def local(self):
        if PUBLIC_ORIGIN and self.headers.get('Host', '') == urlsplit(PUBLIC_ORIGIN).netloc:
            return True
        if urlsplit('//' + self.headers.get('Host', '')).hostname not in ('localhost', '127.0.0.1', '::1'):
            self.error(403, 'Only loopback hosts are allowed')
            return False
        return True

    def do_GET(self):
        if not self.local():
            return
        path = urlsplit(self.path).path
        if path == '/api/health':
            return self.send_data(200, dict(status='ok', engine='sage', core=str(CORE_DIR)))
        if path == '/api/rays/session':
            try:
                return self.send_data(200, coefficient_session())
            except ValueError as exc:
                return self.error(503, str(exc))
        if path == '/api/mandelbrot':
            try:
                return self.send_data(200, curves())
            except Exception as exc:
                return self.error(500, f'Live addMandelBrotSoFar failed: {exc}')
        file = STATIC / ('index.html' if path == '/' else path.removeprefix('/static/'))
        if (path != '/' and not path.startswith('/static/')) or not file.resolve().is_relative_to(STATIC) or not file.is_file():
            return self.error(404, 'Not found')
        self.send_data(200, file.read_bytes(), mimetypes.guess_type(str(file))[0] or 'application/octet-stream')

    def do_POST(self):
        if not self.local():
            return
        if self.headers.get('Origin') not in (None, 'http://' + self.headers.get('Host', ''), PUBLIC_ORIGIN or None):
            return self.error(403, 'Cross-origin requests are not allowed')
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.error(415, 'application/json required')
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16384:
                raise ValueError('Request body must be 1–16384 bytes')
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError('Body must be a JSON object')
            if self.path == '/api/point':
                return self.send_data(200, expression_point(payload))
            if self.path == '/api/rays/curve':
                curve_config(payload)
            elif self.path == '/api/rebuild':
                config = rebuild(payload)
            elif self.path == '/api/trajectory':
                # Validate separately so live core failures are not called invalid input.
                complex_input(payload.get('c'), 'c')
                complex_input(payload.get('start'), 'start')
                integer(payload.get('steps'), 'steps', minimum=-MAX_SAFE_INTEGER)
            else:
                return self.error(404, 'Not found')
        except (ValueError, TypeError, OverflowError) as exc:
            return self.error(422, str(exc))
        try:
            if self.path == '/api/rays/curve':
                return self.send_data(200, parametric_curve(payload))
            if self.path == '/api/trajectory':
                return self.send_data(200, trajectory(payload))
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-ndjson')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.close_connection = True
            messages = grid_messages(config)
            try:
                for message in messages:
                    self.wfile.write((json.dumps(message, allow_nan=False) + '\n').encode())
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass  # Disconnect stops requesting further computation batches.
            finally:
                messages.close()
        except Exception as exc:
            self.error(500, f'Live core failed: {type(exc).__name__}: {exc}. No substitute math was used.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8124)
    args = parser.parse_args()
    server = HTTPServer(('127.0.0.1', args.port), Handler)
    server.timeout = 30
    print(f'Explorer http://127.0.0.1:{args.port} — live core {CORE_DIR}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
