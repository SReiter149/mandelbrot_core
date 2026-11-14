import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import * as stateHelpers from '../code/web/static/state.mjs';

const base = new URL('../code/web/static/', import.meta.url);
const html = readFileSync(new URL('index.html', base), 'utf8');
const source = readFileSync(new URL('app.js', base), 'utf8').replace(/import\s+[\s\S]*?from\s+['"][^'"]+['"];\s*/g, '');
function app() {
  const elements = new Map();
  for (const id of html.matchAll(/id="([^"]+)"/g)) {
    const listeners = {};
    const ctx = new Proxy({}, {get: (target, key) => target[key] ?? (() => {})});
    elements.set(id[1], {hidden: false, checked: true, value: '10', listeners,
      addEventListener: (name, fn) => {listeners[name] = fn;},
      getContext: () => ctx, getBoundingClientRect: () => ({width: 800, height: 600})});
  }
  const calls = [];
  const context = vm.createContext({...stateHelpers, document: {getElementById: id => elements.get(id)},
    window: {addEventListener() {}, devicePixelRatio: 1}, ResizeObserver: class {observe() {}},
    bindPointEntry() {}, loadParameterCurves: () => new Promise(() => {}), AbortController,
    fetch: async (url, options) => {calls.push({url, payload: JSON.parse(options.body)}); return {ok: true, json: async () => ({})};},
    console});
  vm.runInContext(source, context);
  return {elements, calls, context};
}

test('classification and vector visibility are independent and never fetch', () => {
  assert.match(html, /id="show-classification"/, 'Classification toggle missing');
  assert.match(html, /id="show-vectors"/, 'Vector toggle missing');
  const {elements, calls} = app();
  for (const [classification, vectors] of [[false,true], [false,false], [true,false], [true,true]]) {
    for (const [id, checked] of [['show-classification',classification], ['show-vectors',vectors]]) {
      elements.get(id).checked = checked;
      elements.get(id).listeners.change();
    }
    assert.equal(elements.get('classification-canvas').hidden, !classification);
    assert.equal(elements.get('vector-canvas').hidden, !vectors);
    assert.equal(elements.get('overlay-canvas').hidden, false);
  }
  assert.equal(calls.length, 0);
});

test('classification dots are visible without dimming later overlay drawing', () => {
  const {context} = app();
  context.worldToCanvas = () => ({x: 10, y: 10});
  const rendered = vm.runInContext(`(() => {
    const dots = [];
    contexts.classifications.fill = function() { dots.push({alpha: this.globalAlpha, color: this.fillStyle}); };
    drawClassificationSamples(['convergent', 'unresolved', 'divergent', 'cycle'].map(outcome => ({point: {}, outcome})));
    return {dots, finalAlpha: contexts.classifications.globalAlpha};
  })()`, context);
  assert.equal(rendered.dots.length, 4);
  for (const dot of rendered.dots) assert.equal(dot.alpha, 0.7);
  assert.equal(rendered.finalAlpha, 1);
});

test('orbit steps belongs to point entry, not rebuild controls', () => {
  const controls = html.match(/<form id="controls"[\s\S]*?<\/form>/)[0];
  const pointEntry = html.match(/<form id="vector-point-form"[\s\S]*?<\/form>/)[0];
  assert.doesNotMatch(controls, /id="trajectory-steps"/);
  assert.match(pointEntry, /id="trajectory-steps"/);
});

test('new orbit reads current positive, negative, and zero steps without rebuilding', async () => {
  const {elements, calls, context} = app();
  vm.runInContext("state.appliedConfig = {c: {real: .25, imag: 0}, trajectorySteps: 10}; drawOverlay = () => {};", context);
  for (const steps of [23, -3, 0]) {
    elements.get('trajectory-steps').value = String(steps);
    await vm.runInContext("requestTrajectory({id: 'test', start: {real: .5, imag: .2}, requestRevision: 0})", context);
    assert.equal(calls.at(-1).url, '/api/trajectory');
    assert.equal(calls.at(-1).payload.steps, steps);
  }
});
