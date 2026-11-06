import assert from "node:assert/strict";
import {
  configTransition,
  isCurrentTrajectoryResponse,
  findTrajectoryNear,
  worldToCanvas,
  canvasToWorld,
} from "../code/web/static/state.mjs";

const base = {
  c: { real: 0, imag: 0.25 },
  bounds: { xmin: -2, xmax: 2, ymin: -2, ymax: 2 },
  spacing: 0.2,
  classificationIterations: 50,
  convergenceThreshold: 0.001,
  trajectorySteps: 10,
};

assert.equal(configTransition(base, { ...base, spacing: 0.1 }), "grid-only");
assert.equal(configTransition(base, {
  ...base,
  bounds: { ...base.bounds, xmax: 3 },
}), "recalculate-trajectories");
assert.equal(configTransition(base, { ...base, trajectorySteps: 20 }), "recalculate-trajectories");
assert.equal(configTransition(base, {
  ...base,
  c: { real: -1, imag: 0 },
}), "clear-trajectories");

const record = { id: "t-1", trajectoryGeneration: 4, requestRevision: 2 };
assert.equal(isCurrentTrajectoryResponse(record, {
  trajectory_id: "t-1",
  trajectory_generation: 4,
  request_revision: 2,
}), true);
assert.equal(isCurrentTrajectoryResponse(record, {
  trajectory_id: "t-1",
  trajectory_generation: 3,
  request_revision: 2,
}), false);

const transform = {
  width: 400,
  height: 400,
  bounds: { xmin: -2, xmax: 2, ymin: -2, ymax: 2 },
};
const pixel = worldToCanvas({ real: 1, imag: -1 }, transform);
assert.deepEqual(pixel, { x: 300, y: 300 });
const world = canvasToWorld(pixel, transform);
assert(Math.abs(world.real - 1) < 1e-12);
assert(Math.abs(world.imag + 1) < 1e-12);

const trajectories = [
  { id: "a", start: { real: 0, imag: 0 } },
  { id: "b", start: { real: 1, imag: 1 } },
];
assert.equal(findTrajectoryNear(trajectories, { x: 201, y: 199 }, transform, 8)?.id, "a");
assert.equal(findTrajectoryNear(trajectories, { x: 250, y: 250 }, transform, 8), null);

console.log("frontend_state.test: PASS");
