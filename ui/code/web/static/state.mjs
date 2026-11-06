function sameComplex(a, b) {
  return a.real === b.real && a.imag === b.imag;
}

function sameBounds(a, b) {
  return a.xmin === b.xmin && a.xmax === b.xmax &&
    a.ymin === b.ymin && a.ymax === b.ymax;
}

export function configTransition(previous, next) {
  if (!previous || !sameComplex(previous.c, next.c)) {
    return "clear-trajectories";
  }
  if (!sameBounds(previous.bounds, next.bounds) ||
      previous.trajectorySteps !== next.trajectorySteps) {
    return "recalculate-trajectories";
  }
  return "grid-only";
}

export function isCurrentTrajectoryResponse(record, response) {
  return Boolean(record) &&
    record.id === response.trajectory_id &&
    record.trajectoryGeneration === response.trajectory_generation &&
    record.requestRevision === response.request_revision;
}

export function worldToCanvas(point, transform) {
  const { width, height, bounds } = transform;
  return {
    x: ((point.real - bounds.xmin) / (bounds.xmax - bounds.xmin)) * width,
    y: ((bounds.ymax - point.imag) / (bounds.ymax - bounds.ymin)) * height,
  };
}

export function canvasToWorld(point, transform) {
  const { width, height, bounds } = transform;
  return {
    real: bounds.xmin + (point.x / width) * (bounds.xmax - bounds.xmin),
    imag: bounds.ymax - (point.y / height) * (bounds.ymax - bounds.ymin),
  };
}

// Viewport geometry only; the existing Sage curves and dynamics are unchanged.
export function zoomBoundsAt(pixel, transform, factor) {
  const {bounds, width, height} = transform;
  if (!Number.isFinite(factor) || factor <= 0 || width <= 0 || height <= 0) return bounds;
  const anchor = canvasToWorld(pixel, transform);
  const xSpan = (bounds.xmax - bounds.xmin) * factor;
  const ySpan = (bounds.ymax - bounds.ymin) * factor;
  const next = {
    xmin: anchor.real - (pixel.x / width) * xSpan,
    xmax: anchor.real + (1 - pixel.x / width) * xSpan,
    ymin: anchor.imag - (1 - pixel.y / height) * ySpan,
    ymax: anchor.imag + (pixel.y / height) * ySpan,
  };
  // Keep redraw loops bounded at extreme zoom-out and stop before pixel precision collapses.
  if (!Object.values(next).every(Number.isFinite) || xSpan > 100 || ySpan > 100 ||
      xSpan / width <= Number.EPSILON * Math.max(1, Math.abs(anchor.real)) * 8 ||
      ySpan / height <= Number.EPSILON * Math.max(1, Math.abs(anchor.imag)) * 8) return bounds;
  return next;
}

// Trackpad scrolling pans; Chromium pinch gestures arrive as Ctrl+wheel.
export function wheelBoundsAt(pixel, transform, event) {
  const {bounds, width, height} = transform;
  const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? height : 1;
  const dx = event.deltaX * unit, dy = event.deltaY * unit;
  if (width <= 0 || height <= 0 || !Number.isFinite(dx) || !Number.isFinite(dy)) return bounds;
  if (event.ctrlKey) return zoomBoundsAt(pixel, transform, Math.exp(Math.max(-1, Math.min(1, dy * 0.002))));
  const x = dx / width * (bounds.xmax - bounds.xmin);
  const y = -dy / height * (bounds.ymax - bounds.ymin);
  const next = {xmin: bounds.xmin + x, xmax: bounds.xmax + x,
    ymin: bounds.ymin + y, ymax: bounds.ymax + y};
  if (!Object.values(next).every(Number.isFinite) ||
      (next.xmax - next.xmin) / width <= Number.EPSILON * Math.max(1, Math.abs(next.xmin), Math.abs(next.xmax)) * 8 ||
      (next.ymax - next.ymin) / height <= Number.EPSILON * Math.max(1, Math.abs(next.ymin), Math.abs(next.ymax)) * 8) return bounds;
  return next;
}

export function findTrajectoryNear(trajectories, pixel, transform, tolerance = 8) {
  const toleranceSquared = tolerance * tolerance;
  for (const trajectory of trajectories) {
    const startPixel = worldToCanvas(trajectory.start, transform);
    const dx = pixel.x - startPixel.x;
    const dy = pixel.y - startPixel.y;
    if (dx * dx + dy * dy <= toleranceSquared) {
      return trajectory;
    }
  }
  return null;
}
