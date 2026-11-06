"""Real backend/browser viewport regressions; no substituted calculation responses."""
import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors, requests = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: requests.append(r.url) if r.method == 'POST' else None)
    page.add_init_script("""window.plotArcs = {};
      const proto = CanvasRenderingContext2D.prototype;
      const oldSet = proto.setTransform, oldArc = proto.arc;
      proto.setTransform = function(...args) { window.plotArcs[this.canvas.id] = []; return oldSet.apply(this,args); };
      proto.arc = function(...args) { (window.plotArcs[this.canvas.id] ||= []).push(args); return oldArc.apply(this,args); };
    """)
    page.goto(os.environ.get('UI_URL', 'http://127.0.0.1:8124'), wait_until='networkidle')
    page.wait_for_function("document.querySelector('#explorer-status').textContent.includes('selected')")
    page.fill('#explorer-point', '-1/2')
    page.click('#explorer-point-form button')
    page.wait_for_function("document.querySelector('#selection-list').textContent.includes('points')")
    def arcs():
        return page.evaluate("window.plotArcs['orbit-canvas']")
    def wheel(selector, delta=-400):
        b = page.locator(selector).bounding_box()
        assert b is not None
        page.mouse.move(b['x'] + b['width']*.5, b['y'] + b['height']*.5)
        page.keyboard.down('Control')
        page.mouse.wheel(0, delta)
        page.keyboard.up('Control')
        page.wait_for_timeout(150)
    before = arcs()
    left = page.evaluate("window.plotArcs['parameter-canvas']")
    count = len(requests)
    wheel('#orbit-canvas')
    after = arcs()
    assert abs(after[1][0]-after[0][0]) > abs(before[1][0]-before[0][0])*1.5, 'Right plot must actually magnify paths'
    assert page.evaluate("window.plotArcs['parameter-canvas']") == left, 'Right zoom must not change left plot'
    assert len(requests) == count, 'Zoom must not recalculate'
    page.click('#reset-orbit-view')
    assert arcs() == before, 'Orbit reset must restore original geometry'
    assert page.locator('#selection-list button').count() == 1
    assert len(requests) == count
    page.select_option('#mode', 'vector')
    page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready' || document.querySelector('#stage-badge').textContent === 'Failed'")
    canvas = page.locator('#interaction-canvas')
    def click_point(fx, fy):
        b = canvas.bounding_box()
        assert b is not None
        with page.expect_request(lambda r: r.url.endswith('/api/trajectory')) as r:
            canvas.dispatch_event('click', {'clientX': b['x'] + b['width']*fx, 'clientY': b['y'] + b['height']*fy})
        page.wait_for_timeout(100)
        payload = r.value.post_data_json
        assert payload is not None
        return payload['start']
    original = click_point(.65, .6)
    page.click('#clear-trajectories')
    inputs = [page.input_value('#'+i) for i in ['xmin','xmax','ymin','ymax']]
    count = len(requests)
    wheel('#interaction-canvas')
    assert len(requests) == count, 'Vector zoom must not rebuild or recalculate'
    zoomed = click_point(.65, .6)
    assert abs(zoomed['real']) < abs(original['real'])*.6, 'Vector click transform must zoom'
    assert abs(zoomed['imag']) < abs(original['imag'])*.6
    page.click('#clear-trajectories')
    anchor = click_point(.5, .5)
    assert abs(anchor['real']) < .01 and abs(anchor['imag']) < .01, anchor
    page.click('#clear-trajectories')
    page.set_viewport_size({'width':1500, 'height':1050})
    page.wait_for_timeout(150)
    resized = click_point(.65, .6)
    # Browser MouseEvent coordinates round to CSS pixels; allow one pixel across sizes.
    assert abs(resized['real']-zoomed['real']) < .004
    page.click('#clear-trajectories')
    page.select_option('#mode', 'mandelbrot')
    page.select_option('#mode', 'vector')
    page.wait_for_timeout(150)
    switched = click_point(.65, .6)
    assert abs(switched['real']-zoomed['real']) < .004
    page.click('#clear-trajectories')
    count = len(requests)
    page.click('#reset-vector-view')
    assert len(requests) == count
    reset = click_point(.65, .6)
    assert abs(reset['real']-original['real']) < .004
    assert [page.input_value('#'+i) for i in ['xmin','xmax','ymin','ymax']] == inputs
    page.click('#clear-trajectories')
    wheel('#interaction-canvas')
    page.fill('#spacing', '1')
    with page.expect_response(lambda r: r.url.endswith('/api/rebuild')):
        page.click('#controls button[type=submit]')
    page.wait_for_function("document.querySelector('#stage-badge').textContent === 'Ready' || document.querySelector('#stage-badge').textContent === 'Failed'")
    rebuilt = click_point(.65, .6)
    assert abs(rebuilt['real']-original['real']) < .004, 'Accepted rebuild resets viewport'
    page.screenshot(path='tests/browser-vector-zoom.png', full_page=True)
    page.select_option('#mode','mandelbrot')
    wheel('#orbit-canvas')
    page.screenshot(path='tests/browser-orbit-zoom.png', full_page=True)
    assert not errors, errors
    browser.close()
print('PASS: orbit magnification/reset/independence; vector zoom/click/reset/resize/mode/rebuild; no zoom calculation requests; no JS errors')
