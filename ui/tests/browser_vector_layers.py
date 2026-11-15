"""Vector layer toggles and viewport-sized plot regression checks."""
import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 800})
    errors, calculations = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: calculations.append(r.url) if '/api/' in r.url else None)
    page.goto(os.environ.get('UI_URL', 'http://127.0.0.1:8124'), wait_until='networkidle')
    page.select_option('#mode', 'vector')
    page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready'")
    assert page.locator('#show-classification').count() == 1, 'Classification toggle is missing'
    assert page.locator('#show-vectors').count() == 1, 'Vector toggle is missing'
    before = len(calculations)
    for classification, vectors in [(False, True), (False, False), (True, False), (True, True)]:
        page.locator('#show-classification').set_checked(classification)
        page.locator('#show-vectors').set_checked(vectors)
        assert page.locator('#classification-canvas').is_visible() == classification
        assert page.locator('#vector-canvas').is_visible() == vectors
        assert page.locator('#overlay-canvas').is_visible(), 'Orbit/fixed-point layer must remain visible'
    assert len(calculations) == before, 'Visibility toggles must not request calculations'
    page.locator('#show-vectors').uncheck()
    page.select_option('#mode', 'mandelbrot')
    page.select_option('#mode', 'vector')
    assert not page.locator('#vector-canvas').is_visible(), 'Mode switching must preserve layer choice'
    for width, height in [(1440, 800), (1280, 600)]:
        page.set_viewport_size({'width': width, 'height': height})
        page.wait_for_timeout(150)
        for selector in ['#plot-frame', '#vector-minimap']:
            box = page.locator(selector).bounding_box()
            assert box is not None
            assert box['y'] >= 0 and box['y'] + box['height'] <= height, (selector, box, height)
        plot_box = page.locator('#plot-frame').bounding_box()
        assert plot_box is not None and plot_box['height'] > 200
    assert not errors, errors
    browser.close()
print('PASS: independent layer toggles; no calculation requests; mode persistence; plot/minimap fit 800px and 600px windows; no JS errors')
