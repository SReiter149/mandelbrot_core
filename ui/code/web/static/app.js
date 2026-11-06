import {
  configTransition,
  isCurrentTrajectoryResponse,
  findTrajectoryNear,
  worldToCanvas,
  canvasToWorld,
  wheelBoundsAt,
} from "./state.mjs";
import { bindPointEntry, evaluatePoint } from './point_entry.mjs';
import { setup, drawPath, loadParameterCurves } from './canvas_presentation.mjs';

const $ = (id) => document.getElementById(id);
const form = $("controls");
const plotFrame = $("plot-frame");
const emptyState = $("plot-empty");
const stageBadge = $("stage-badge");
const progressText = $("progress-text");
const elapsedText = $("elapsed-text");
const formError = $("form-error");
const activeParameter = $("active-parameter");

const canvases = {
  axes: $("axes-canvas"),
  vectors: $("vector-canvas"),
  classifications: $("classification-canvas"),
  overlay: $("overlay-canvas"),
  interaction: $("interaction-canvas"),
};
const contexts = Object.fromEntries(
  Object.entries(canvases).map(([key, canvas]) => [key, canvas.getContext("2d")]),
);

const palette = ["#fff1b8", "#67e8f9", "#fdba74", "#f9a8d4", "#c4b5fd", "#a7f3d0"];
const state = {
  appliedConfig: null,
  viewBounds: null,
  pendingBuild: null,
  gridGeneration: 0,
  trajectoryGeneration: 0,
  nextTrajectoryId: 1,
  rebuildController: null,
  trajectories: new Map(),
  fixedPoints: [],
  vectors: [],
  classifications: [],
  pointCount: 0,
  completedPoints: 0,
  transform: null,
};

function readNumber(id, label) {
  const value = Number($(id).value);
  if (!Number.isFinite(value)) throw new Error(`${label} must be a finite number.`);
  return value;
}

function readInteger(id, label, min = -Infinity) {
  const value = readNumber(id, label);
  if (!Number.isSafeInteger(value) || value < min) {
    throw new Error(`${label} must be ${min === 1 ? "a positive integer" : "an integer"}.`);
  }
  return value;
}

async function readDraftConfig() {
  const expression = $("c-expression").value;
  const config = {
    c: null,
    bounds: {
      xmin: readNumber("xmin", "x minimum"),
      xmax: readNumber("xmax", "x maximum"),
      ymin: readNumber("ymin", "y minimum"),
      ymax: readNumber("ymax", "y maximum"),
    },
    spacing: readNumber("spacing", "Grid spacing"),
    classificationIterations: readInteger("iterations", "Iterations", 1),
    convergenceThreshold: readNumber("threshold", "Convergence threshold"),
    trajectorySteps: readInteger("trajectory-steps", "Orbit steps"),
    vectorLength: 0.1,
  };
  if (!(config.bounds.xmin < config.bounds.xmax)) throw new Error("x maximum must exceed x minimum.");
  if (!(config.bounds.ymin < config.bounds.ymax)) throw new Error("y maximum must exceed y minimum.");
  if (!(config.spacing > 0)) throw new Error("Grid spacing must be positive.");
  if (!(config.convergenceThreshold > 0)) throw new Error("Convergence threshold must be positive.");
  config.c = await evaluatePoint(expression);
  return config;
}

function showError(message) {
  formError.textContent = message;
  formError.hidden = false;
}
function clearError() {
  formError.textContent = "";
  formError.hidden = true;
}
function setStage(stage, detail = "") {
  stageBadge.textContent = stage;
  if (detail) progressText.textContent = detail;
}

function configureCanvas(canvas, ctx, width, height, dpr) {
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function resizePlot() {
  renderMinimap();
  const rect = canvases.interaction.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  for (const [key, canvas] of Object.entries(canvases)) {
    configureCanvas(canvas, contexts[key], rect.width, rect.height, dpr);
  }
  if (state.appliedConfig) {
    state.transform = { width: rect.width, height: rect.height, bounds: state.viewBounds };
    redrawAll();
  }
}

function clearCanvas(ctx) {
  const { width, height } = state.transform;
  ctx.clearRect(0, 0, width, height);
}

function drawAxes() {
  const ctx = contexts.axes;
  clearCanvas(ctx);
  const { width, height, bounds } = state.transform;
  ctx.fillStyle = "#0b0c0e";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "rgba(255,255,255,.055)";
  ctx.lineWidth = 1;
  const xSpan = bounds.xmax - bounds.xmin;
  const ySpan = bounds.ymax - bounds.ymin;
  const rough = Math.max(xSpan, ySpan) / 8;
  const magnitude = 10 ** Math.floor(Math.log10(rough || 1));
  const step = [1, 2, 5, 10].map((n) => n * magnitude).find((n) => n >= rough) || magnitude;

  ctx.beginPath();
  for (let x = Math.ceil(bounds.xmin / step) * step; x <= bounds.xmax; x += step) {
    const px = worldToCanvas({ real: x, imag: 0 }, state.transform).x;
    ctx.moveTo(Math.round(px) + 0.5, 0);
    ctx.lineTo(Math.round(px) + 0.5, height);
  }
  for (let y = Math.ceil(bounds.ymin / step) * step; y <= bounds.ymax; y += step) {
    const py = worldToCanvas({ real: 0, imag: y }, state.transform).y;
    ctx.moveTo(0, Math.round(py) + 0.5);
    ctx.lineTo(width, Math.round(py) + 0.5);
  }
  ctx.stroke();

  ctx.strokeStyle = "rgba(247,248,248,.24)";
  ctx.beginPath();
  if (bounds.xmin <= 0 && bounds.xmax >= 0) {
    const x0 = worldToCanvas({ real: 0, imag: 0 }, state.transform).x;
    ctx.moveTo(x0, 0); ctx.lineTo(x0, height);
  }
  if (bounds.ymin <= 0 && bounds.ymax >= 0) {
    const y0 = worldToCanvas({ real: 0, imag: 0 }, state.transform).y;
    ctx.moveTo(0, y0); ctx.lineTo(width, y0);
  }
  ctx.stroke();
}

function drawArrow(ctx, start, end, color) {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const length = Math.hypot(dx, dy);
  if (length < 0.5) return;
  const ux = dx / length;
  const uy = dy / length;
  const head = Math.min(4, length * 0.35);
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(end.x, end.y);
  ctx.lineTo(end.x - head * ux + head * 0.65 * uy, end.y - head * uy - head * 0.65 * ux);
  ctx.lineTo(end.x - head * ux - head * 0.65 * uy, end.y - head * uy + head * 0.65 * ux);
  ctx.closePath();
  ctx.fill();
}

function drawVectorSamples(samples) {
  const ctx = contexts.vectors;
  ctx.lineWidth = 0.75;
  ctx.globalAlpha = 0.32;
  for (const sample of samples) {
    if (!sample.draw) continue;
    const start = worldToCanvas(sample.start, state.transform);
    const end = worldToCanvas(sample.end, state.transform);
    const color = `rgb(${sample.color.map((v) => Math.round(v * 255)).join(",")})`;
    drawArrow(ctx, start, end, color);
  }
  ctx.globalAlpha = 1;
}

function drawClassificationSamples(samples) {
  const ctx = contexts.classifications;
  const colors = { convergent: "#80b59e", unresolved: "#baac78", divergent: "#b98693", cycle: "#83a9c4" };
  ctx.globalAlpha = 0.36;
  for (const sample of samples) {
    const pixel = worldToCanvas(sample.point, state.transform);
    ctx.fillStyle = colors[sample.outcome];
    ctx.beginPath();
    ctx.arc(pixel.x, pixel.y, 2.1, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function drawOverlay() {
  const ctx = contexts.overlay;
  clearCanvas(ctx);
  for (const fixed of state.fixedPoints) {
    const pixel = worldToCanvas(fixed.point, state.transform);
    ctx.fillStyle = "rgba(125,211,252,.14)";
    ctx.beginPath(); ctx.arc(pixel.x, pixel.y, 10, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#7dd3fc";
    ctx.beginPath(); ctx.arc(pixel.x, pixel.y, 4.5, 0, Math.PI * 2); ctx.fill();
    if (fixed.multiplicity === 2) {
      ctx.font = "11px SFMono-Regular, Consolas, monospace";
      ctx.fillStyle = "#bae6fd";
      ctx.fillText("×2", pixel.x + 9, pixel.y - 8);
    }
  }

  for (const record of state.trajectories.values()) {
    const points = record.points || [record.start];
    ctx.strokeStyle = record.color;
    ctx.fillStyle = record.color;
    ctx.lineWidth = 1.8;
    if (record.geometry === 'path') {
      ctx.beginPath();
      points.forEach((point, index) => {
        const pixel = worldToCanvas(point, state.transform);
        if (index === 0) ctx.moveTo(pixel.x, pixel.y);
        else ctx.lineTo(pixel.x, pixel.y);
      });
      ctx.stroke();
    }
    for (const point of points) {
      const pixel = worldToCanvas(point, state.transform);
      ctx.beginPath(); ctx.arc(pixel.x, pixel.y, 2.2, 0, Math.PI * 2); ctx.fill();
    }
    const startPixel = worldToCanvas(record.start, state.transform);
    ctx.beginPath(); ctx.arc(startPixel.x, startPixel.y, 5, 0, Math.PI * 2); ctx.fill();
    if (record.loading) {
      const pixel = worldToCanvas(record.start, state.transform);
      ctx.strokeStyle = "rgba(247,248,248,.7)";
      ctx.beginPath(); ctx.arc(pixel.x, pixel.y, 8, 0, Math.PI * 2); ctx.stroke();
    }
  }
}

function redrawAll() {
  drawAxes();
  clearCanvas(contexts.vectors);
  drawVectorSamples(state.vectors);
  clearCanvas(contexts.classifications);
  drawClassificationSamples(state.classifications);
  drawOverlay();
}

function clearGridLayers() {
  state.fixedPoints = [];
  state.vectors = [];
  state.classifications = [];
  state.pointCount = 0;
  state.completedPoints = 0;
  if (!state.transform) return;
  clearCanvas(contexts.vectors);
  clearCanvas(contexts.classifications);
  drawOverlay();
}

function formatC(c) {
  const sign = c.imag < 0 ? "−" : "+";
  return `c = ${c.real} ${sign} ${Math.abs(c.imag)}i`;
}

function applyAcceptedBuild(message) {
  const pending = state.pendingBuild;
  if (!pending || pending.generation !== message.grid_generation) return false;

  const { config, transition } = pending;
  state.appliedConfig = structuredClone(config);
  state.viewBounds = {...config.bounds};
  const rect = canvases.interaction.getBoundingClientRect();
  state.transform = { width: rect.width, height: rect.height, bounds: state.viewBounds };
  clearGridLayers();
  drawAxes();

  if (transition === "clear-trajectories") {
    state.trajectoryGeneration += 1;
    for (const record of state.trajectories.values()) record.controller?.abort();
    state.trajectories.clear();
    drawOverlay();
  } else if (transition === "recalculate-trajectories") {
    state.trajectoryGeneration += 1;
    for (const record of state.trajectories.values()) requestTrajectory(record);
  }

  activeParameter.textContent = formatC(config.c);
  renderMinimap();
  emptyState.hidden = true;
  elapsedText.textContent = "—";
  state.pendingBuild = null;
  return true;
}

async function consumeNdjson(response, generation) {
  if (!response.ok) {
    let message = `Rebuild failed (${response.status}).`;
    try { message = (await response.json()).error?.message || message; } catch {}
    const error = new Error(message);
    error.kind = response.status === 422 ? "validation" : "network";
    throw error;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.trim()) continue;
      const message = JSON.parse(line);
      if (message.grid_generation !== state.gridGeneration || generation !== state.gridGeneration) continue;
      handleGridMessage(message);
    }
    if (done) break;
  }
  if (buffer.trim() && generation === state.gridGeneration) handleGridMessage(JSON.parse(buffer));
}

function handleGridMessage(message) {
  if (message.type === "accepted") {
    if (!applyAcceptedBuild(message)) return;
    state.pointCount = message.point_count;
    setStage("Fixed points", `0 / ${state.pointCount} samples`);
  } else if (message.type === "fixed_points") {
    state.fixedPoints = message.multiplicity?.[0] === 2
      ? [{ point: message.roots[0], multiplicity: 2 }]
      : message.roots.map((point) => ({ point, multiplicity: 1 }));
    drawOverlay();
    setStage("Vector field", `0 / ${state.pointCount} samples`);
  } else if (message.type === "vector_batch") {
    state.vectors.push(...message.samples);
    drawVectorSamples(message.samples);
  } else if (message.type === "classification_batch") {
    state.classifications.push(...message.samples);
    state.completedPoints += message.samples.length;
    drawClassificationSamples(message.samples);
    setStage("Classifying", `${state.completedPoints} / ${state.pointCount} samples`);
  } else if (message.type === "complete") {
    setStage("Ready", `${state.pointCount} / ${state.pointCount} samples`);
    elapsedText.textContent = `${message.elapsed_ms} ms`;
  } else if (message.type === "error") {
    showError(message.error?.message || "The rebuild stream failed.");
    setStage("Failed", `${state.completedPoints} / ${state.pointCount} samples`);
  }
}

async function rebuild(config) {
  const transition = configTransition(state.appliedConfig, config);
  state.gridGeneration += 1;
  const generation = state.gridGeneration;
  state.pendingBuild = { generation, config: structuredClone(config), transition };
  if (state.rebuildController) state.rebuildController.abort();
  state.rebuildController = new AbortController();
  setStage("Starting", "validating grid…");

  const payload = {
    grid_generation: generation,
    c: config.c,
    bounds: config.bounds,
    spacing: config.spacing,
    classification_iterations: config.classificationIterations,
    convergence_threshold: config.convergenceThreshold,
    vector_length: config.vectorLength,
  };
  try {
    const response = await fetch("/api/rebuild", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: state.rebuildController.signal,
    });
    await consumeNdjson(response, generation);
  } catch (error) {
    if (error.name !== "AbortError" && generation === state.gridGeneration) {
      state.pendingBuild = null;
      showError(error.message);
      const detail = state.appliedConfig ? "previous view retained" : "Sage server unavailable";
      setStage(error.kind === "validation" ? "Rejected" : "Offline", detail);
    }
  }
}

async function requestTrajectory(record) {
  record.controller?.abort();
  record.controller = new AbortController();
  record.requestRevision += 1;
  record.trajectoryGeneration = state.trajectoryGeneration;
  record.loading = true;
  record.error = null;
  drawOverlay();
  const requestRevision = record.requestRevision;
  try {
    const response = await fetch("/api/trajectory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        trajectory_generation: record.trajectoryGeneration,
        trajectory_id: record.id,
        request_revision: requestRevision,
        c: state.appliedConfig.c,
        start: record.start,
        steps: state.appliedConfig.trajectorySteps,
      }),
      signal: record.controller.signal,
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || "Orbit request failed.");
    const current = state.trajectories.get(record.id);
    if (!isCurrentTrajectoryResponse(current, result)) return;
    current.points = result.points;
    current.geometry = result.geometry;
    current.loading = false;
    current.terminationReason = result.termination_reason;
    drawOverlay();
  } catch (error) {
    if (error.name === "AbortError") return;
    const current = state.trajectories.get(record.id);
    if (current && current.requestRevision === requestRevision) {
      current.loading = false;
      current.error = error.message;
      showError(`Orbit ${record.id}: ${error.message}`);
      drawOverlay();
    }
  }
}

bindPointEntry('vector-point-form', 'vector-point', start => {
  if (!state.appliedConfig) throw new Error('Rebuild the vector field first.');
  clearError();
  addTrajectory(start);
}, showError);

function addTrajectory(start) {
  const id = `trajectory-${state.nextTrajectoryId++}`;
  const record = {
    id,
    start,
    color: palette[(state.nextTrajectoryId - 2) % palette.length],
    points: [start],
    requestRevision: 0,
    trajectoryGeneration: state.trajectoryGeneration,
    loading: false,
    controller: null,
  };
  state.trajectories.set(id, record);
  requestTrajectory(record);
}

canvases.interaction.addEventListener('wheel', event => {
  if (!state.transform || !state.appliedConfig) return;
  event.preventDefault();
  const rect = canvases.interaction.getBoundingClientRect();
  const pixel = {x: event.clientX - rect.left, y: event.clientY - rect.top};
  state.viewBounds = wheelBoundsAt(pixel, state.transform, event);
  state.transform = {...state.transform, bounds: state.viewBounds};
  redrawAll();
}, {passive: false});
$('reset-vector-view').addEventListener('click', () => {
  if (!state.appliedConfig) return;
  state.viewBounds = {...state.appliedConfig.bounds};
  state.transform = {...state.transform, bounds: state.viewBounds};
  redrawAll();
});

canvases.interaction.addEventListener("click", (event) => {
  if (!state.transform || !state.appliedConfig) return;
  const rect = canvases.interaction.getBoundingClientRect();
  const pixel = { x: event.clientX - rect.left, y: event.clientY - rect.top };
  const existing = findTrajectoryNear([...state.trajectories.values()], pixel, state.transform, 8);
  if (existing) {
    existing.controller?.abort();
    state.trajectories.delete(existing.id);
    drawOverlay();
    return;
  }
  addTrajectory(canvasToWorld(pixel, state.transform));
});

const minimapCanvas = $('vector-parameter-canvas');
let minimapBounds = {xmin: -2, xmax: 1, ymin: -1.5, ymax: 1.5};
let minimapCurves = null;
let minimapTransform = null;
function renderMinimap() {
  if (!minimapCurves || $('vector-workspace').hidden) return;
  const {ctx, transform} = setup(minimapCanvas, minimapBounds);
  minimapTransform = transform;
  minimapCurves.curves.forEach((curve, i) =>
    drawPath(ctx, transform, curve, '#d0d6e0', false, minimapCurves.styles[i]));
  if (state.appliedConfig) {
    const {x, y} = worldToCanvas(state.appliedConfig.c, transform);
    ctx.fillStyle = palette[0];
    ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI * 2); ctx.fill();
  }
}
minimapCanvas.addEventListener('wheel', event => {
  if (!minimapTransform) return;
  event.preventDefault();
  const rect = minimapCanvas.getBoundingClientRect();
  const pixel = {x: event.clientX - rect.left, y: event.clientY - rect.top};
  minimapBounds = wheelBoundsAt(pixel, minimapTransform, event);
  renderMinimap();
}, {passive: false});
minimapCanvas.addEventListener('click', event => {
  if (!minimapTransform) return;
  const rect = minimapCanvas.getBoundingClientRect();
  const c = canvasToWorld({x: event.clientX - rect.left, y: event.clientY - rect.top}, minimapTransform);
  $('c-expression').value = `${c.real} + (${c.imag})*I`;
  rebuildDraft();
});
loadParameterCurves().then(result => {
  minimapCurves = result;
  renderMinimap();
}).catch(error => showError(error.message));

let draftRevision = 0;
async function rebuildDraft() {
  const revision = ++draftRevision;
  clearError();
  try {
    const config = await readDraftConfig();
    if (revision === draftRevision) await rebuild(config);
  } catch (error) {
    if (revision === draftRevision) showError(error.message);
  }
}
form.addEventListener("submit", event => {
  event.preventDefault();
  rebuildDraft();
});

$("clear-trajectories").addEventListener("click", () => {
  state.trajectoryGeneration += 1;
  for (const record of state.trajectories.values()) record.controller?.abort();
  state.trajectories.clear();
  if (state.transform) drawOverlay();
});
window.addEventListener("resize", resizePlot);
new ResizeObserver(resizePlot).observe(plotFrame);

resizePlot();
window.addEventListener("explorer-mode", (event) => {
  if (event.detail !== "vector") return;
  resizePlot();
  if (!state.appliedConfig) {
    rebuildDraft();
  }
});
