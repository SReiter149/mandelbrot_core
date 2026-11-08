import test from 'node:test';
import assert from 'node:assert/strict';
import { selectionColor, acceptOrbit } from '../code/web/static/explorer_state.mjs';

test('selection colors are stable and distinct without cycling six colors', () => {
  const colors = Array.from({length: 30}, (_, index) => selectionColor(index + 1));
  assert.equal(new Set(colors).size, 30);
  assert.equal(selectionColor(3), colors[2]);
});

test('deleted selection and stale response cannot restore or replace an orbit', () => {
  const selection = { id: 'c-1', requestRevision: 2, trajectoryGeneration: 1 };
  const response = { trajectory_id: 'c-1', request_revision: 2, trajectory_generation: 1, points: [{ real: 0, imag: 0 }] };
  assert.equal(acceptOrbit(undefined, response), false);
  assert.equal(acceptOrbit(selection, {...response, request_revision: 1}), false);
  assert.equal(acceptOrbit(selection, response), true);
  assert.deepEqual(selection.points, response.points);
});
