import test from 'node:test';
import assert from 'node:assert/strict';
import { RaysState } from '../code/web/static/rays_state.mjs';
import { drawPrimitive, setup } from '../code/web/static/canvas_presentation.mjs';

test('multiple curves retain one page session; remove and clear invalidate pending replies', () => {
  const state = new RaysState({session_token: 'page-1', coefficient_count: 30});
  const a = state.begin({expression: 't'}), b = state.begin({expression: 'I*t'});
  assert.equal(a.session_token, b.session_token);
  const response = request => ({...request, source: [], image: []});
  assert.equal(state.accept(response(a)), true);
  assert.equal(state.accept(response(b)), true);
  assert.equal(state.curves.size, 2);
  state.remove(a.curve_id);
  assert.equal(state.accept(response(a)), false);
  state.clear();
  assert.equal(state.accept(response(b)), false);
  assert.equal(state.session.coefficient_count, 30);
});

test('revisions, wrong sessions and failures cannot overwrite successful curves', () => {
  const state = new RaysState({session_token: 'page-1', coefficient_count: 30});
  const old = state.begin({expression: 't'});
  assert.equal(state.accept({...old, session_token: 'other'}), false);
  const next = state.begin({expression: '2*t'}, old.curve_id);
  assert.equal(state.accept({...old, source: [], image: []}), false);
  assert.equal(state.accept({...next, source: [1], image: [2]}), true);
  const invalid = state.begin({expression: 'invalid'});
  state.reject(invalid);
  assert.equal(state.curves.size, 1);
  assert.deepEqual(state.curves.get(next.curve_id).source, [1]);
  // Changing modes has no effect on this page-owned model.
  assert.equal(state.session.session_token, 'page-1');
});

test('core point primitives draw markers with native scatter area, never connecting strokes', () => {
  const calls = [];
  const ctx = {save(){}, restore(){}, setLineDash(){}, beginPath(){},
    arc(...args){calls.push(['arc', ...args]);}, fill(){calls.push(['fill']);},
    stroke(){calls.push(['stroke']);}, moveTo(){}, lineTo(){}};
  drawPrimitive(ctx, {width:100, height:100, bounds:{xmin:0,xmax:2,ymin:0,ymax:2}},
    {geometry:'points', points:[{real:1,imag:1},{real:2,imag:2}],
     style:{rgbcolor:[0,0,0], alpha:1, size:10, marker:'o', linestyle:'-', thickness:1}});
  assert.equal(calls.filter(c => c[0] === 'stroke').length, 0);
  assert.equal(calls.filter(c => c[0] === 'arc').length, 2);
  assert.equal(calls[0][3], Math.sqrt(10) * (96/72) / 2);
});

test('paired plots can use a light background without changing existing plot defaults', () => {
  globalThis.devicePixelRatio = 1;
  const fills = [];
  const ctx = {setTransform(){}, fillRect(){fills.push(this.fillStyle);}};
  const canvas = {getBoundingClientRect:()=>({width:100,height:100}), getContext:()=>ctx};
  const bounds = {xmin:.1,xmax:.9,ymin:.1,ymax:.9};
  setup(canvas, bounds, '#ffffff');
  setup(canvas, bounds);
  assert.deepEqual(fills, ['#ffffff', '#0b0c0e']);
});
