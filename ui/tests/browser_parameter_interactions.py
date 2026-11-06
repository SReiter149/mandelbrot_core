"""Real Sage/browser checks for pointer zoom and vector parameter expressions."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors, requests = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: requests.append((r.url, r.post_data_json)) if r.method == 'POST' else None)
    page.goto(os.environ.get('UI_URL', 'http://127.0.0.1:8124'), wait_until='networkidle')
    page.wait_for_function("document.querySelector('#explorer-status').textContent.includes('selected')")
    canvas = page.locator('#parameter-canvas')
    box = canvas.bounding_box()
    orbit_box = page.locator('#orbit-canvas').bounding_box()
    assert abs(box['y'] - orbit_box['y']) < 1, 'Plot headings must keep both canvases aligned'
    x, y = box['width'] * .37, box['height'] * .43
    def select_at(px, py):
        with page.expect_request(lambda r: r.url.endswith('/api/trajectory')) as request:
            canvas.click(position={'x': px, 'y': py})
        return request.value.post_data_json['c']
    original = select_at(x, y)
    page.click('#clear-selections')
    page.mouse.move(box['x'] + x, box['y'] + y)
    page.keyboard.down('Control')
    page.mouse.wheel(0, -500)
    page.keyboard.up('Control')
    page.wait_for_timeout(150)
    anchored = select_at(x, y)
    assert abs(anchored['real'] - original['real']) < 1e-12
    assert abs(anchored['imag'] - original['imag']) < 1e-12
    page.click('#clear-selections')
    zoomed = select_at(x + 50, y + 30)
    assert abs(zoomed['real'] - anchored['real']) < 3 * 50 / box['width']
    page.click('#reset-parameter-view')
    assert page.locator('#selection-list button').count() == 1
    page.click('#clear-selections')
    reset = select_at(x, y)
    assert abs(reset['real'] - original['real']) < 1e-12
    assert abs(reset['imag'] - original['imag']) < 1e-12
    page.select_option('#mode', 'vector')
    page.wait_for_function("document.querySelector('#active-parameter').textContent.includes('0.25')")
    page.fill('#spacing', '1')
    page.fill('#c-expression', '1/3 + sqrt(2)*I')
    with page.expect_request(lambda r: r.url.endswith('/api/rebuild')) as build:
        page.click('#controls button[type=submit]')
    c = build.value.post_data_json['c']
    assert abs(c['real'] - 1/3) < 1e-14
    assert abs(c['imag'] - 2**.5) < 1e-14
    page.wait_for_function("document.querySelector('#active-parameter').textContent.includes('1.414')")
    assert page.input_value('#c-expression') == '1/3 + sqrt(2)*I'
    applied = page.locator('#active-parameter').inner_text()
    before = sum(url.endswith('/api/rebuild') for url, _ in requests)
    page.fill('#c-expression', '__import__("os")')
    page.click('#controls button[type=submit]')
    page.wait_for_function("document.querySelector('#form-error').textContent.includes('Invalid Sage')")
    assert page.locator('#active-parameter').inner_text() == applied
    assert sum(url.endswith('/api/rebuild') for url, _ in requests) == before
    page.fill('#vector-point', 'I/4')
    with page.expect_request(lambda r: r.url.endswith('/api/trajectory')) as orbit:
        page.click('#vector-point-form button')
    assert orbit.value.post_data_json['c'] == c
    # Hold a real Sage response while a newer expression is submitted.
    held = []
    def hold_older_expression(route):
        if route.request.post_data_json.get('expression') == 'I/2':
            held.append((route, route.fetch()))
        else:
            route.continue_()
    page.route('**/api/point', hold_older_expression)
    page.fill('#c-expression', 'I/2')
    page.click('#controls button[type=submit]')
    page.wait_for_timeout(200)
    assert held, 'Expected the first expression response to be delayed'
    page.fill('#c-expression', 'I/3')
    with page.expect_request(lambda r: r.url.endswith('/api/rebuild')) as latest:
        page.click('#controls button[type=submit]')
    assert abs(latest.value.post_data_json['c']['imag'] - 1/3) < 1e-14
    page.wait_for_function("document.querySelector('#active-parameter').textContent.includes('0.3333')")
    before_release = sum(url.endswith('/api/rebuild') for url, _ in requests)
    route, response = held.pop()
    route.fulfill(response=response)
    page.wait_for_timeout(200)
    assert sum(url.endswith('/api/rebuild') for url, _ in requests) == before_release
    assert '0.3333' in page.locator('#active-parameter').inner_text()
    page.select_option('#mode', 'mandelbrot')
    page.screenshot(path=str(Path('tests/browser-parameter-interactions.png')), full_page=True)
    assert not errors, errors
    browser.close()
print('Pointer anchor, zoomed click, reset, selection preservation, exact c, invalid c retention, and applied orbit c: PASS')
