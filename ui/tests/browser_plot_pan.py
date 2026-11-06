"""Exercise real two-axis wheel panning on every plot with a live Sage backend."""
import os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    requests,errors=[],[]
    page.on('request',lambda r: requests.append(r.url) if r.method=='POST' else None)
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.add_init_script("""window.arcs={}; const p=CanvasRenderingContext2D.prototype;
    for(const name of ['setTransform','clearRect']) {const old=p[name]; p[name]=function(...a){window.arcs[this.canvas.id]=[];return old.apply(this,a);};}
    const old=p.arc;p.arc=function(...a){(window.arcs[this.canvas.id] ||= []).push(a);return old.apply(this,a);};""")
    page.goto(os.environ.get('UI_URL','http://127.0.0.1:8124'),wait_until='networkidle')
    page.fill('#explorer-point','-1/2');page.click('#explorer-point-form button')
    page.wait_for_function("document.querySelector('#selection-list').textContent.includes('points')")
    for target,draw,reset in [('parameter-canvas','parameter-canvas','reset-parameter-view'),('orbit-canvas','orbit-canvas','reset-orbit-view'),('interaction-canvas','overlay-canvas','reset-vector-view')]:
        if target=='interaction-canvas':
            page.select_option('#mode','vector')
            page.wait_for_function("['Ready','Failed'].includes(document.querySelector('#stage-badge').textContent)")
        before=page.evaluate('(id)=>window.arcs[id]',draw)
        assert before
        count=len(requests)
        box=page.locator('#'+target).bounding_box();assert box
        page.mouse.move(box['x']+box['width']*.5,box['y']+box['height']*.5)
        page.mouse.wheel(50,35);page.wait_for_timeout(150)
        after=page.evaluate('(id)=>window.arcs[id]',draw)
        assert len(after)==len(before)
        for a,b in zip(before,after):
            assert abs(b[0]-a[0]+50)<.01,(target,a,b)
            assert abs(b[1]-a[1]+35)<.01,(target,a,b)
        assert len(requests)==count
        page.click('#'+reset)
        restored=page.evaluate('(id)=>window.arcs[id]',draw)
        for a,b in zip(before,restored):
            assert abs(a[0]-b[0])<1e-9 and abs(a[1]-b[1])<1e-9
        assert len(requests)==count
        print('PASS:',target,'two-axis pan translates all markers without scaling; reset; no calculation requests')
    assert not errors,errors
    browser.close()
