"""Verify live Sage styles survive all the way to Canvas drawing calls."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

url = os.environ.get('UI_URL', 'http://127.0.0.1:8137')
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        headless=True, args=['--disable-gpu'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.add_init_script("""
        window.plotCalls = [];
        for (const name of ['stroke', 'arc']) {
            const original = CanvasRenderingContext2D.prototype[name];
            CanvasRenderingContext2D.prototype[name] = function(...args) {
                if (this.canvas.id === 'parameter-canvas') {
                    window.plotCalls.push({name, color: this.strokeStyle,
                        fill: this.fillStyle, radius: name === 'arc' ? args[2] : null});
                }
                return original.apply(this, args);
            };
        }
    """)
    page.goto(url, wait_until='networkidle')
    page.wait_for_function("document.querySelector('#explorer-status').textContent.includes('selected')")
    data = page.request.get(url + '/api/mandelbrot').json()
    assert len(data['styles']) == len(data['curves']) == 5
    calls = page.evaluate('window.plotCalls')
    # Browser colors are normalized to hex; the first two core curves are blue.
    assert any(c['name'] == 'stroke' and c['color'] == '#0000ff' for c in calls)
    assert not any(c['name'] == 'stroke' and c['color'] in ('#ff0000', '#008000') for c in calls)
    # Check each actual core style, including subpixel markers (no minimum-size override).
    for style in data['styles'][2:]:
        assert style['linestyle'] == ''
        assert style['marker'] == '.'
        expected_radius = style['markersize'] * (96 / 72) / 4
        expected_color = '#' + ''.join(f'{round(v * 255):02x}' for v in style['rgbcolor'])
        assert any(c['name'] == 'arc' and c['fill'] == expected_color
                   and abs(c['radius'] - expected_radius) < 1e-12 for c in calls)
    # Isolate a subsequent redraw: exactly two curve strokes, never three branch strokes.
    page.evaluate('window.plotCalls = []')
    page.click('#reset-parameter-view')
    strokes = page.evaluate("window.plotCalls.filter(c => c.name === 'stroke' && ['#0000ff', '#ff0000', '#008000'].includes(c.color))")
    assert len(strokes) == 2, strokes
    page.locator('#parameter-canvas').screenshot(path='tests/browser-plot-styles.png')
    assert not errors, errors
    browser.close()
print('browser_plot_styles: PASS — two line curves; three marker-only branches; live colors and sizes')
