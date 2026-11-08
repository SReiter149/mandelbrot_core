import { isCurrentTrajectoryResponse } from './state.mjs';

// Presentation only: stable hues keyed to a never-reused selection identifier.
export function selectionColor(id) {
  return `hsl(${(id * 137.508) % 360} 78% 65%)`;
}

export function acceptOrbit(record, response) {
  if (!isCurrentTrajectoryResponse(record, response)) return false;
  record.points = response.points;
  record.loading = false;
  return true;
}
