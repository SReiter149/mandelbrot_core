import test from 'node:test';
import assert from 'node:assert/strict';
import * as viewport from '../code/web/static/state.mjs';
import * as entry from '../code/web/static/point_entry.mjs';

const bounds = {xmin: -2, xmax: 1, ymin: -1.5, ymax: 1.5};
const transform = {width: 600, height: 400, bounds};
const pixel = {x: 123, y: 287};

test('zoom preserves the world coordinate beneath the pointer and scales both spans', () => {
  assert.equal(typeof viewport.zoomBoundsAt, 'function');
  const next = viewport.zoomBoundsAt(pixel, transform, 0.5);
  const before = viewport.canvasToWorld(pixel, transform);
  const after = viewport.canvasToWorld(pixel, {...transform, bounds: next});
  assert.ok(Math.abs(before.real - after.real) < 1e-14);
  assert.ok(Math.abs(before.imag - after.imag) < 1e-14);
  assert.equal(next.xmax - next.xmin, 1.5);
  assert.equal(next.ymax - next.ymin, 1.5);
  assert.deepEqual(transform.bounds, bounds);
});

test('inverse zoom restores original bounds', () => {
  assert.equal(typeof viewport.zoomBoundsAt, 'function');
  const next = viewport.zoomBoundsAt(pixel, transform, 0.5);
  const restored = viewport.zoomBoundsAt(pixel, {...transform, bounds: next}, 2);
  for (const key of Object.keys(bounds)) assert.ok(Math.abs(restored[key] - bounds[key]) < 1e-14);
});

test('invalid or precision-collapsed zoom leaves bounds unchanged', () => {
  assert.equal(typeof viewport.zoomBoundsAt, 'function');
  for (const factor of [0, -1, NaN, Infinity, Number.MIN_VALUE]) {
    assert.deepEqual(viewport.zoomBoundsAt(pixel, transform, factor), bounds);
  }
});

test('shared expression transport sends text to Sage and returns its point', async () => {
  assert.equal(typeof entry.evaluatePoint, 'function');
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(url, '/api/point');
      assert.deepEqual(JSON.parse(options.body), {expression: '1/3 + sqrt(2)*I'});
      return {ok: true, json: async () => ({point: {real: 0.333, imag: 1.414}})};
    };
    assert.deepEqual(await entry.evaluatePoint('1/3 + sqrt(2)*I'), {real: 0.333, imag: 1.414});
    globalThis.fetch = async () => ({ok: false, json: async () => ({error: {message: 'Invalid Sage expression'}})});
    await assert.rejects(entry.evaluatePoint('bad'), /Invalid Sage expression/);
  } finally { globalThis.fetch = original; }
});
