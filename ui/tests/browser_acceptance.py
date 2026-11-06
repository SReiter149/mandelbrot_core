"""Real-browser smoke checks; run with Playwright and an already-running UI server."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

url = os.environ.get('UI_URL', 'http://127.0.0.1:8124')
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True, args=['--disable-gpu'], downloads_path=str(Path.cwd()/'.cache/downloads'))
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(url, wait_until='networkidle')
    page.locator('#parameter-canvas').wait_for(state='visible')
    page.wait_for_function("!document.querySelector('#explorer-status').textContent.includes('Loading')")
    print('Initial status:', page.locator('#explorer-status').inner_text())
    requests = []
    page.on('request', lambda r: requests.append(r.post_data_json) if r.url.endswith('/api/trajectory') and r.method == 'POST' else None)
    page.fill('#explorer-point', 'sqrt(2) * I / pi')
    page.click('#explorer-point-form button')
    page.wait_for_function("document.querySelectorAll('#selection-list button').length === 1 && !document.querySelector('#selection-list').textContent.includes('…')")
    assert requests[-1]['c']['real'] == 0
    assert abs(requests[-1]['c']['imag'] - 0.4501581580785531) < 1e-14
    page.fill('#explorer-point', '3*I + 4')
    page.click('#explorer-point-form button')
    page.wait_for_function("document.querySelectorAll('#selection-list button').length === 2 && !document.querySelector('#selection-list').textContent.includes('…')")
    assert requests[-1]['c'] == {'real': 4, 'imag': 3}
    page.fill('#explorer-point', 'bad_name')
    page.click('#explorer-point-form button')
    page.locator('#explorer-error').wait_for(state='visible')
    assert page.locator('#selection-list button').count() == 2
    page.click('#clear-selections')
    canvas = page.locator('#parameter-canvas')
    box = canvas.bounding_box()
    canvas.click(position={'x': box['width']*.40, 'y': box['height']*.48})
    page.wait_for_timeout(1200)
    canvas.click(position={'x': box['width']*.66, 'y': box['height']*.45})
    page.wait_for_timeout(1200)
    print('Selections:', page.locator('#selection-list').inner_text())
    assert page.locator('#selection-list button').count() >= 2, 'Expected two selectable orbits'
    page.screenshot(path='tests/browser-mandelbrot.png', full_page=True)
    page.select_option('#mode', 'vector')
    page.locator('#interaction-canvas').wait_for(state='visible')
    page.wait_for_timeout(1800)
    print('Vector status:', page.locator('#stage-badge').inner_text())
    print('Vector error:', page.locator('#form-error').inner_text())
    page.fill('#vector-point', 'sqrt(2) * I / pi')
    with page.expect_response(lambda r: r.url.endswith('/api/trajectory')) as orbit:
        page.click('#vector-point-form button')
    result = orbit.value.json()
    assert requests[-1]['start']['real'] == 0
    assert abs(requests[-1]['start']['imag'] - 0.4501581580785531) < 1e-14
    assert result['points'][0] == requests[-1]['start']
    print('Exact Sage expressions: PASS in both modes')
    page.screenshot(path='tests/browser-vector.png', full_page=True)
    page.select_option('#mode', 'mandelbrot')
    assert page.locator('#selection-list button').count() >= 2
    page.click('#clear-selections')
    assert page.locator('#selection-list button').count() == 0
    print('Browser JS errors:', errors)
    assert not errors
    browser.close()
print('browser_acceptance: PASS')
