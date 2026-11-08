"""Check the vector plot's focus/background color hierarchy in a real browser."""
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1100})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.add_init_script("""(() => {
      window.colors = {};
      for (const method of ['arc', 'stroke']) {
        const original = CanvasRenderingContext2D.prototype[method];
        CanvasRenderingContext2D.prototype[method] = function(...args) {
          (window.colors[this.canvas.id] ||= []).push({method, args,
            fill: this.fillStyle, alpha: this.globalAlpha});
          return original.apply(this, args);
        };
      }
    })()""")
    page.goto(os.environ.get('UI_URL', 'http://127.0.0.1:8124'), wait_until='networkidle')
    page.select_option('#mode', 'vector')
    page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready'")
    page.fill('#trajectory-steps', '-7')
    with page.expect_request(lambda r: r.url.endswith('/api/rebuild')):
        page.click('#controls button[type=submit]')
    page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready'")
    page.fill('#vector-point', '1/3 + I/5')
    with page.expect_response(lambda r: r.url.endswith('/api/trajectory')):
        page.click('#vector-point-form button')
    page.wait_for_function("(window.colors['overlay-canvas'] || []).some(p => p.method === 'arc' && p.args[2] === 2.2 && p.fill === '#fff1b8')")
    colors = page.evaluate('window.colors')
    assert all(p['alpha'] <= .4 for p in colors['vector-canvas'] if p['method'] == 'stroke'), 'Arrows must stay behind selected points'
    assert all(p['alpha'] <= .4 for p in colors['classification-canvas'] if p['method'] == 'arc'), 'Classifications must stay behind selected points'
    assert any(p['fill'] == '#7dd3fc' and p['args'][2] == 4.5 for p in colors['overlay-canvas'] if p['method'] == 'arc'), 'Fixed points must use a different hue'
    swatch = page.locator('.swatch.orbit').evaluate('(el) => getComputedStyle(el).backgroundColor')
    assert swatch == 'rgb(255, 241, 184)', 'Legend must match the first selected set'
    page.screenshot(path='.runtime/pullback-colors-after.png', full_page=True)
    assert not errors, errors
    browser.close()
print('PASS: ivory pullbacks, blue fixed points, subdued background layers, matching legend, no JS errors')
