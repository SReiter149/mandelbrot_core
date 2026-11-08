"""Live Sage + Playwright regression: signed steps and vector single-c minimap.
Run: UI_URL=http://127.0.0.1:8126 uv run --with playwright python tests/browser_pullback_minimap.py
No synthetic API responses; delayed responses below are fetched from the real server.
"""
import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.add_init_script("""(() => {
      window.paint = {};
      for (const method of ['clearRect', 'fillRect', 'lineTo', 'arc']) {
        const original = CanvasRenderingContext2D.prototype[method];
        CanvasRenderingContext2D.prototype[method] = function(...args) {
          const id = this.canvas.id;
          if (method === 'clearRect' || method === 'fillRect') window.paint[id] = [];
          else (window.paint[id] ||= []).push({method, args});
          return original.apply(this, args);
        };
      }
    })()""")
    page.goto(os.environ.get('UI_URL', 'http://127.0.0.1:8124'), wait_until='networkidle')
    page.wait_for_function("document.querySelector('#explorer-status').textContent.includes('selected')")
    page.select_option('#mode', 'vector')
    page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready'")
    assert page.get_attribute('#trajectory-steps', 'min') is None, 'Orbit steps must allow negative and zero'
    for field in ['iterations', 'trajectory-steps', 'explorer-steps']:
        assert page.get_attribute('#' + field, 'max') is None, f'{field} still has an artificial cap'
    mini = page.locator('#vector-parameter-canvas')
    assert mini.is_visible(), 'Vector mode must expose its single-c minimap'
    frame, box = page.locator('#plot-frame').bounding_box(), mini.bounding_box()
    assert frame is not None and box is not None
    assert box['x'] > frame['x'] + frame['width'] / 2
    assert box['y'] > frame['y'] + frame['height'] / 2

    def rebuild(steps, expression='2', iterations='1001'):
        page.fill('#spacing', '4')
        page.fill('#iterations', iterations)
        page.fill('#trajectory-steps', str(steps))
        page.fill('#c-expression', expression)
        with page.expect_request(lambda r: r.url.endswith('/api/rebuild')) as req:
            page.click('#controls button[type=submit]')
        page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready'")
        assert req.value.post_data_json['classification_iterations'] == int(iterations)

    rebuild(-1001)  # Validate transport without constructing an enormous pullback set.
    rebuild(1001)
    def orbit(steps, expression='1/3 + I/5'):
        page.fill('#vector-point', expression)
        with page.expect_response(lambda r: r.url.endswith('/api/trajectory')) as response:
            page.click('#vector-point-form button')
        body = response.value.json()
        assert response.value.request.post_data_json['steps'] == steps
        assert response.value.ok, body
        page.wait_for_timeout(100)
        return body
    assert orbit(1001)['geometry'] == 'path'
    assert any(op['method'] == 'lineTo' for op in page.evaluate("window.paint['overlay-canvas']")), 'Forward paths must still be connected'
    page.click('#clear-trajectories')
    rebuild(-1)
    result = orbit(-1)
    assert result['geometry'] == 'points'
    paint = page.evaluate("window.paint['overlay-canvas']")
    assert not any(op['method'] == 'lineTo' for op in paint), 'Unordered pullbacks must never be connected'
    start = {'real': 1/3, 'imag': 1/5}
    overlay = page.locator('#overlay-canvas').bounding_box()
    assert overlay is not None
    expected = ((start['real'] + 2) / 4 * overlay['width'], (2 - start['imag']) / 4 * overlay['height'])
    markers = [op['args'] for op in paint if op['method'] == 'arc' and op['args'][2] == 5]
    assert len(markers) == 1 and abs(markers[0][0] - expected[0]) < 1e-8 and abs(markers[0][1] - expected[1]) < 1e-8, 'Start marker must mark the requested target, not the first pullback'
    page.click('#clear-trajectories')
    rebuild(0)
    zero = orbit(0)
    assert zero['geometry'] == 'points' and len(zero['points']) == 1
    assert not any(op['method'] == 'lineTo' for op in page.evaluate("window.paint['overlay-canvas']"))

    # Each minimap click replaces c, clears old orbits, and preserves exact numeric expression.
    def choose(x, y):
        with page.expect_request(lambda r: r.url.endswith('/api/rebuild')) as req:
            mini.click(position={'x': box['width'] * x, 'y': box['height'] * y})
        page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready'")
        return req.value.post_data_json['c']
    choose(.4, .45)
    c = choose(.6, .55)
    with page.expect_request(lambda r: r.url.endswith('/api/rebuild')) as req:
        page.click('#controls button[type=submit]')
    page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready'")
    assert req.value.post_data_json['c'] == c, 'Minimap expression must round-trip the full clicked coordinates'
    assert not any(op['method'] == 'arc' and op['args'][2] == 5 for op in page.evaluate("window.paint['overlay-canvas']")), 'Changing c must clear old orbits'
    markers = [op for op in page.evaluate("window.paint['vector-parameter-canvas']") if op['method'] == 'arc' and op['args'][2] == 5]
    assert len(markers) == 1, 'Minimap must show exactly one accepted c'
    assert orbit(0)['points'], 'Orbits must work after c replacement'

    # Two quick clicks: delay the first real build stream beyond the newer accepted one.
    delayed_builds = []
    delay_next = [True]
    def delay_build(route):
        if delay_next[0]:
            delay_next[0] = False
            delayed_builds.append((route, route.fetch()))
        else:
            route.continue_()
    page.route('**/api/rebuild', delay_build)
    with page.expect_request(lambda r: r.url.endswith('/api/rebuild')):
        mini.click(position={'x': box['width'] * .3, 'y': box['height'] * .35})
    page.wait_for_timeout(200)
    assert delayed_builds
    latest_c = choose(.65, .4)
    route, response = delayed_builds.pop()
    route.fulfill(response=response)
    page.wait_for_timeout(100)
    page.fill('#vector-point', 'I/4')
    with page.expect_response(lambda r: r.url.endswith('/api/trajectory')) as response:
        page.click('#vector-point-form button')
    assert response.value.request.post_data_json['c'] == latest_c, 'Stale click must not restore c'
    assert response.value.ok
    markers = [op['args'] for op in page.evaluate("window.paint['vector-parameter-canvas']") if op['method'] == 'arc' and op['args'][2] == 5]
    assert len(markers) == 1 and abs(markers[0][0] - box['width'] * .65) < 1, 'Marker must match the accepted latest click'

    rebuild(0, '1/3 + sqrt(2)*I')
    assert page.input_value('#c-expression') == '1/3 + sqrt(2)*I'
    # Delay a real expression response; a minimap click must invalidate it.
    held = []
    def hold(route):
        if route.request.post_data_json.get('expression') == 'I/2':
            held.append((route, route.fetch()))
        else:
            route.continue_()
    page.route('**/api/point', hold)
    page.fill('#c-expression', 'I/2')
    page.click('#controls button[type=submit]')
    page.wait_for_timeout(200)
    assert held
    c = choose(.45, .6)
    expression = page.input_value('#c-expression')
    route, response = held.pop()
    route.fulfill(response=response)
    page.wait_for_timeout(200)
    assert page.input_value('#c-expression') == expression
    assert orbit(0)['points']
    page.select_option('#mode', 'mandelbrot')
    page.fill('#explorer-steps', '1001')
    for expr in ['2', '3']:
        page.fill('#explorer-point', expr)
        with page.expect_response(lambda r: r.url.endswith('/api/trajectory')) as response:
            page.click('#explorer-point-form button')
        assert response.value.request.post_data_json['steps'] == 1001
        assert response.value.ok
    assert page.locator('#selection-list button').count() == 2, 'Explorer must retain multiple selections'
    page.select_option('#mode', 'vector')
    assert mini.is_visible()
    assert not errors, errors
    browser.close()
print('Signed uncapped steps, pullback dots/target, zero, single-c minimap, exact sync, stale expression, modes: PASS')
