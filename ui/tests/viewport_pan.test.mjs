import test from 'node:test';
import assert from 'node:assert/strict';
import * as view from '../code/web/static/state.mjs';
const t = {width:600,height:400,bounds:{xmin:-2,xmax:1,ymin:-1.5,ymax:1.5}};
const pixel = {x:123,y:287};
test('ordinary two-axis wheel translates without zooming or mutating source', () => {
  const next = view.wheelBoundsAt(pixel,t,{deltaX:60,deltaY:40,deltaMode:0,ctrlKey:false});
  assert.deepEqual(next,{xmin:-1.7,xmax:1.3,ymin:-1.8,ymax:1.2});
  const a=view.worldToCanvas({real:0,imag:0},t);
  const b=view.worldToCanvas({real:0,imag:0},{...t,bounds:next});
  assert.ok(Math.abs(b.x-a.x+60)<1e-12);
  assert.ok(Math.abs(b.y-a.y+40)<1e-12);
  assert.equal(t.bounds.xmin,-2);
});
test('pinch/control wheel delegates to pointer-anchored zoom',()=>{
  const next=view.wheelBoundsAt(pixel,t,{deltaX:0,deltaY:-200,deltaMode:0,ctrlKey:true});
  assert.deepEqual(next,view.zoomBoundsAt(pixel,t,Math.exp(-.4)));
});
test('line/page wheel normalization and invalid pan inputs',()=>{
  const next=view.wheelBoundsAt(pixel,t,{deltaX:1,deltaY:1,deltaMode:1});
  const pixels=view.wheelBoundsAt(pixel,t,{deltaX:16,deltaY:16,deltaMode:0});
  assert.deepEqual(next,pixels);
  assert.deepEqual(view.wheelBoundsAt(pixel,t,{deltaX:0,deltaY:1,deltaMode:2}),view.wheelBoundsAt(pixel,t,{deltaX:0,deltaY:400,deltaMode:0}));
  for (const dx of [NaN,Infinity,Number.MAX_VALUE]) assert.deepEqual(view.wheelBoundsAt(pixel,t,{deltaX:dx,deltaY:0,deltaMode:0}),t.bounds);
});
