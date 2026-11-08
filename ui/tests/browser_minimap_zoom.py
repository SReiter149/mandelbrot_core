"""Live browser regression for minimap zoom/pan and transformed c selection."""
import math
import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors, calculations = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.add_init_script("""(() => {
      window.miniMarkers = [];
      const fill = CanvasRenderingContext2D.prototype.fillRect;
      const arc = CanvasRenderingContext2D.prototype.arc;
      CanvasRenderingContext2D.prototype.fillRect = function(...args) {
        if (this.canvas.id === 'vector-parameter-canvas') window.miniMarkers = [];
        return fill.apply(this, args);
      };
      CanvasRenderingContext2D.prototype.arc = function(...args) {
        if (this.canvas.id === 'vector-parameter-canvas' && args[2] === 5) window.miniMarkers.push(args);
        return arc.apply(this, args);
      };
    })()""")
    page.goto(os.environ.get('UI_URL', 'http://127.0.0.1:8124'), wait_until='networkidle')
    page.select_option('#mode', 'vector')
    page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready'")
    page.on('request', lambda r: calculations.append(r.url) if r.url.endswith(('/api/rebuild', '/api/trajectory', '/api/point')) else None)
    mini = page.locator('#vector-parameter-canvas')
    box = mini.bounding_box()
    assert box is not None
    w, h = box['width'], box['height']
    client_x, client_y = int(box['x'] + w * .3), int(box['y'] + h * .4)
    ax, ay = client_x - box['x'], client_y - box['y']
    before = page.evaluate('window.miniMarkers[0]')
    def wheel(dx, dy, ctrl):
        mini.dispatch_event('wheel', {'clientX': client_x, 'clientY': client_y,
                                     'deltaX': dx, 'deltaY': dy, 'ctrlKey': ctrl, 'bubbles': True, 'cancelable': True})
    wheel(0, -200, True)
    factor = math.exp(-.4)
    after = page.evaluate('window.miniMarkers[0]')
    assert abs(after[0] - (ax + (before[0] - ax) / factor)) < 1e-7, 'Minimap must zoom at pointer'
    assert abs(after[1] - (ay + (before[1] - ay) / factor)) < 1e-7
    wheel(0, 200, True)
    restored = page.evaluate('window.miniMarkers[0]')
    assert abs(restored[0] - before[0]) < 1e-7 and abs(restored[1] - before[1]) < 1e-7
    wheel(0, -200, True)
    zoomed = page.evaluate('window.miniMarkers[0]')
    wheel(12, 8, False)
    panned = page.evaluate('window.miniMarkers[0]')
    assert abs(panned[0] - (zoomed[0] - 12)) < 1e-7
    assert abs(panned[1] - (zoomed[1] - 8)) < 1e-7
    assert not calculations, 'Minimap navigation must not calculate or change c'
    anchor_real, anchor_imag = -2 + ax / w * 3, 1.5 - ay / h * 3
    xmin = anchor_real - ax / w * 3 * factor + 12 / w * 3 * factor
    ymax = anchor_imag + ay / h * 3 * factor - 8 / h * 3 * factor
    expected = {'real': xmin + .55 * 3 * factor, 'imag': ymax - .45 * 3 * factor}
    with page.expect_request(lambda r: r.url.endswith('/api/rebuild')) as request:
        mini.click(position={'x': w * .55, 'y': h * .45})
    actual = request.value.post_data_json['c']
    # Playwright pointer coordinates are integer CSS pixels.
    assert abs(actual['real'] - expected['real']) < 3 * factor / w
    assert abs(actual['imag'] - expected['imag']) < 3 * factor / h
    page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready'")
    marker = page.evaluate('window.miniMarkers')
    assert len(marker) == 1 and abs(marker[0][0] - w * .55) < 1 and abs(marker[0][1] - h * .45) < 1
    page.select_option('#mode', 'mandelbrot')
    page.select_option('#mode', 'vector')
    kept = page.evaluate('window.miniMarkers[0]')
    assert abs(kept[0] - marker[0][0]) < 1e-7 and abs(kept[1] - marker[0][1]) < 1e-7
    assert not errors, errors
    browser.close()
print('PASS: minimap pointer zoom, inverse zoom, pan, no calculations, zoomed c click, viewport persistence')
