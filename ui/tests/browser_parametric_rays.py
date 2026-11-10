"""Real browser + HTTP acceptance; run against an isolated Sage UI_URL server."""
import json
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
url = os.environ['UI_URL']
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get('CHROME_PATH', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
        headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 1100})
    errors, requests, sessions = [], [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: requests.append(json.loads(request.post_data))
            if request.url.endswith('/api/rays/curve') else None)
    page.on('response', lambda response: sessions.append(response.json())
            if response.url.endswith('/api/rays/session') and response.ok else None)
    page.add_init_script("""
      window.rayCalls = [];
      for (const name of ['arc', 'stroke', 'fillRect']) {
        const original = CanvasRenderingContext2D.prototype[name];
        CanvasRenderingContext2D.prototype[name] = function(...args) {
          if (this.canvas.id.startsWith('rays-')) window.rayCalls.push({
            canvas: this.canvas.id, name, args, color: this.fillStyle, stroke: this.strokeStyle});
          return original.apply(this, args);
        };
      }
    """)
    page.goto(url, wait_until='networkidle')
    page.select_option('#mode', 'rays', timeout=3000)
    expect(page.locator('#rays-coefficients')).to_have_text(re.compile(r'Using \d+ coefficients'))
    page.click('#rays-add')
    expect(page.locator('#rays-list .selection-row')).to_have_count(1)
    expect(page.locator('#rays-status')).to_have_text('1 curves · 0 pending')
    page.fill('#rays-expression', 't*exp(I*pi/3)')
    page.click('#rays-add')
    expect(page.locator('#rays-list .selection-row')).to_have_count(2)
    expect(page.locator('#rays-status')).to_have_text('2 curves · 0 pending')
    assert len(sessions) == 1
    expect(page.locator('#rays-coefficients')).to_have_text(f"Using {sessions[0]['coefficient_count']} coefficients")
    assert requests[0]['session_token'] == requests[1]['session_token'] == sessions[0]['session_token']
    calls = page.evaluate('window.rayCalls')
    for canvas in ['rays-source', 'rays-image']:
        assert any(c['canvas'] == canvas and c['name'] == 'arc' and c['color'] == '#000000' for c in calls)
        assert any(c['canvas'] == canvas and c['name'] == 'fillRect' and c['color'] == '#ffffff' for c in calls)
        assert not any(c['canvas'] == canvas and c['name'] == 'stroke' and c['stroke'] == '#000000' for c in calls)
    page.screenshot(path=str(ROOT / '.runtime/rays-browser.png'))
    page.fill('#rays-expression', 't.__class__')
    page.click('#rays-add')
    expect(page.locator('#rays-error')).to_be_visible()
    expect(page.locator('#rays-list .selection-row')).to_have_count(2)
    page.select_option('#mode', 'mandelbrot')
    expect(page.locator('#rays-workspace')).to_be_hidden()
    expect(page.locator('#explorer-workspace')).to_be_visible()
    page.select_option('#mode', 'rays')
    expect(page.locator('#rays-list .selection-row')).to_have_count(2)
    assert len(sessions) == 1
    # Pan/zoom/reset change only the selected viewport and issue no new plot requests.
    before = len(requests)
    def redraw_arcs():
        return page.evaluate("window.rayCalls.filter(c => c.name === 'arc').map(c => [c.canvas, ...c.args])")
    page.evaluate('window.rayCalls = []')
    page.click('#rays-reset-source')
    original = redraw_arcs()
    page.evaluate('window.rayCalls = []')
    canvas = page.locator('#rays-source')
    canvas.dispatch_event('wheel', {'deltaX': 100, 'deltaY': 50})
    panned = redraw_arcs()
    assert [c for c in panned if c[0] == 'rays-source'] != [c for c in original if c[0] == 'rays-source']
    assert [c for c in panned if c[0] == 'rays-image'] == [c for c in original if c[0] == 'rays-image']
    page.evaluate('window.rayCalls = []')
    canvas.dispatch_event('wheel', {'deltaX': 0, 'deltaY': -150, 'ctrlKey': True})
    assert redraw_arcs() != panned
    page.evaluate('window.rayCalls = []')
    page.click('#rays-reset-source')
    assert redraw_arcs() == original
    assert len(requests) == before
    page.locator('#rays-list button').first.click()
    expect(page.locator('#rays-list .selection-row')).to_have_count(1)
    page.click('#rays-clear')
    expect(page.locator('#rays-list .selection-row')).to_have_count(0)
    # Full page refresh gets a new snapshot; switching modes did not.
    token = sessions[0]['session_token']
    page.reload(wait_until='networkidle')
    assert len(sessions) == 2 and sessions[1]['session_token'] != token
    # Coefficient failure is local to this mode, leaving existing modes usable.
    page.route('**/api/rays/session', lambda route: route.fulfill(status=503,
               content_type='application/json', body='{"error":{"message":"No coefficient saves"}}'))
    page.reload(wait_until='networkidle')
    page.select_option('#mode', 'rays')
    expect(page.locator('#rays-error')).to_contain_text('No coefficient saves')
    expect(page.locator('#rays-add')).to_be_disabled()
    page.select_option('#mode', 'mandelbrot')
    expect(page.locator('#explorer-status')).to_contain_text('selected')
    assert not errors, errors
    browser.close()
print('browser_parametric_rays: PASS — paired core points, add/remove/clear, error retention, session refresh, mode persistence, independent pan/zoom/reset')
