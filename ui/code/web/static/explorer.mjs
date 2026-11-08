import { worldToCanvas, canvasToWorld, findTrajectoryNear, wheelBoundsAt } from './state.mjs';
import { selectionColor, acceptOrbit } from './explorer_state.mjs';
import { bindPointEntry } from './point_entry.mjs';

const $ = id => document.getElementById(id);
const selections = new Map();
let nextId = 1;
let curves = [];
let curveStyles = [];
let loaded = false;
const defaultParameterBounds = { xmin: -2, xmax: 1, ymin: -1.5, ymax: 1.5 };
let parameterBounds = {...defaultParameterBounds};
const defaultOrbitBounds = { xmin: -2, xmax: 2, ymin: -2, ymax: 2 };
let orbitBounds = {...defaultOrbitBounds};
const transforms = new Map();

function error(message) {
  $('explorer-error').textContent = message;
  $('explorer-error').hidden = !message;
}

function setup(canvas, bounds) {
  const { width, height } = canvas.getBoundingClientRect();
  const ratio = Math.min(devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  const transform = { width, height, bounds };
  transforms.set(canvas.id, transform);
  ctx.fillStyle = '#0b0c0e';
  ctx.fillRect(0, 0, width, height);
  ctx.font = '11px monospace';
  for (let n = Math.ceil(bounds.xmin); n <= bounds.xmax; n++) {
    const {x} = worldToCanvas({real: n, imag: 0}, transform);
    ctx.strokeStyle = n === 0 ? '#4c515b' : '#202329';
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
    ctx.fillStyle = '#8a8f98'; ctx.fillText(String(n), Math.min(width - 16, x + 4), height - 8);
  }
  for (let n = Math.ceil(bounds.ymin); n <= bounds.ymax; n++) {
    const {y} = worldToCanvas({real: 0, imag: n}, transform);
    ctx.strokeStyle = n === 0 ? '#4c515b' : '#202329';
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    ctx.fillStyle = '#8a8f98'; ctx.fillText(`${n}i`, 5, Math.max(12, y - 4));
  }
  return {ctx, transform};
}

function drawPath(ctx, transform, points, color, markers = false, style = null) {
  ctx.save();
  const ptToPx = 96 / 72;
  const lineStyle = style ? style.linestyle : '-';
  const drawLine = !['', ' ', 'None', 'none', null].includes(lineStyle);
  if (style) color = `rgb(${style.rgbcolor.map(v => v * 255).join(',')})`;
  ctx.strokeStyle = color; ctx.fillStyle = color;
  ctx.lineWidth = style ? style.thickness * ptToPx : 1.6;
  ctx.globalAlpha = style ? style.alpha : 1;
  const dashes = {'--': [6, 3], dashed: [6, 3], ':': [1, 3], dotted: [1, 3],
    '-.': [6, 3, 1, 3], dashdot: [6, 3, 1, 3]};
  ctx.setLineDash(dashes[lineStyle] || []);
  if (drawLine) {
    ctx.beginPath();
    points.forEach((p, i) => {
      const {x, y} = worldToCanvas(p, transform);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
  // Matplotlib's '.' marker has half the diameter of its 'o' marker.
  const marker = style ? style.marker : (markers ? 'o' : null);
  const radius = style ? style.markersize * ptToPx * (marker === '.' ? 0.25 : 0.5) : 3;
  if (!['', ' ', 'None', 'none', null].includes(marker) && radius > 0) {
    for (const p of points) {
      const {x, y} = worldToCanvas(p, transform);
      ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.fill();
    }
  }
  ctx.restore();
}

function render() {
  if ($('explorer-workspace').hidden) return;
  const left = setup($('parameter-canvas'), parameterBounds);
  const right = setup($('orbit-canvas'), orbitBounds);
  curves.forEach((curve, i) => drawPath(left.ctx, left.transform, curve, '#d0d6e0', false, curveStyles[i]));
  for (const record of selections.values()) {
    const {x, y} = worldToCanvas(record.start, left.transform);
    left.ctx.fillStyle = record.color;
    left.ctx.beginPath(); left.ctx.arc(x, y, 5, 0, Math.PI * 2); left.ctx.fill();
    drawPath(right.ctx, right.transform, record.points || [], record.color, true);
  }
  $('explorer-status').textContent = loaded
    ? `${selections.size} selected · ${[...selections.values()].filter(s => s.loading).length} pending`
    : 'Loading curves…';
}

function renderList() {
  $('selection-list').replaceChildren();
  for (const record of selections.values()) {
    const row = document.createElement('div');
    row.className = 'selection-row';
    const text = document.createElement('span');
    text.style.color = record.color;
    text.textContent = `${record.id}: ${record.start.real.toFixed(4)} ${record.start.imag < 0 ? '−' : '+'} ${Math.abs(record.start.imag).toFixed(4)}i${record.loading ? ' …' : record.error ? ' · failed' : ` · ${record.points.length} points`}`;
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'secondary'; button.textContent = 'Remove';
    button.setAttribute('aria-label', `Remove ${record.id}`);
    button.addEventListener('click', () => remove(record));
    row.append(text, button); $('selection-list').append(row);
  }
}

function remove(record) {
  record.controller?.abort();
  selections.delete(record.id);
  renderList(); render();
}

function steps() {
  const value = Number($('explorer-steps').value);
  if (!Number.isInteger(value) || value < 1 || value > 1000) throw new Error('Path steps must be an integer from 1 to 1000.');
  return value;
}

async function requestOrbit(record, count) {
  record.controller?.abort();
  record.controller = new AbortController();
  record.requestRevision++;
  const revision = record.requestRevision;
  record.loading = true; record.error = null;
  renderList(); render();
  try {
    const response = await fetch('/api/trajectory', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, signal: record.controller.signal,
      body: JSON.stringify({c: record.start, start: {real: 0, imag: 0}, steps: count,
        trajectory_id: record.id, trajectory_generation: record.trajectoryGeneration, request_revision: revision}),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || 'Path request failed');
    if (!acceptOrbit(selections.get(record.id), result)) return;
  } catch (e) {
    if (e.name === 'AbortError' || selections.get(record.id) !== record || revision !== record.requestRevision) return;
    record.loading = false; record.error = e.message;
    error(`${record.id}: ${e.message}`);
  }
  renderList(); render();
}

function selectParameter(start) {
  if (!loaded) throw new Error('Wait for the parameter curves to load.');
  const count = steps(); error('');
  const id = nextId++;
  const record = {id: `c-${id}`, start, color: selectionColor(id),
    points: [], requestRevision: 0, trajectoryGeneration: 1, loading: false};
  selections.set(record.id, record);
  requestOrbit(record, count);
}

bindPointEntry('explorer-point-form', 'explorer-point', selectParameter, error);

for (const [canvasId, resetId, defaults] of [
  ['parameter-canvas', 'reset-parameter-view', defaultParameterBounds],
  ['orbit-canvas', 'reset-orbit-view', defaultOrbitBounds],
]) {
const canvas = $(canvasId);
canvas.addEventListener('wheel', event => {
  const transform = transforms.get(canvas.id);
  if (!loaded || !transform) return;
  event.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const pixel = {x: event.clientX - rect.left, y: event.clientY - rect.top};
  const bounds = wheelBoundsAt(pixel, transform, event);
  if (canvasId === 'parameter-canvas') parameterBounds = bounds;
  else orbitBounds = bounds;
  render();
}, {passive: false});
$(resetId).addEventListener('click', () => {
  if (canvasId === 'parameter-canvas') parameterBounds = {...defaults};
  else orbitBounds = {...defaults};
  render();
});
}

$('parameter-canvas').addEventListener('click', event => {
  if (!loaded) return;
  const canvas = $('parameter-canvas');
  const transform = transforms.get(canvas.id);
  const rect = canvas.getBoundingClientRect();
  const pixel = {x: event.clientX - rect.left, y: event.clientY - rect.top};
  const existing = findTrajectoryNear([...selections.values()], pixel, transform, 9);
  if (existing) return remove(existing);
  try {
    selectParameter(canvasToWorld(pixel, transform));
  } catch (e) { error(e.message); }
});

$('explorer-form').addEventListener('submit', event => {
  event.preventDefault();
  try {
    const count = steps(); error('');
    for (const record of selections.values()) requestOrbit(record, count);
  } catch (e) { error(e.message); }
});
$('clear-selections').addEventListener('click', () => {
  for (const record of selections.values()) record.controller?.abort();
  selections.clear(); error(''); renderList(); render();
});
$('mode').addEventListener('change', () => {
  const vector = $('mode').value === 'vector';
  for (const id of ['controls', 'vector-point-form', 'vector-legend', 'vector-workspace']) $(id).hidden = !vector;
  for (const id of ['explorer-controls', 'explorer-workspace']) $(id).hidden = vector;
  window.dispatchEvent(new CustomEvent('explorer-mode', {detail: $('mode').value}));
  render();
});
new ResizeObserver(render).observe($('parameter-canvas').parentElement);
new ResizeObserver(render).observe($('orbit-canvas').parentElement);
try {
  const response = await fetch('/api/mandelbrot');
  const result = await response.json();
  if (!response.ok) throw new Error(result.error?.message || 'Unable to load live curves');
  curves = result.curves; curveStyles = result.styles; loaded = true; render();
} catch (e) {
  error(e.message); $('explorer-status').textContent = 'Live core unavailable';
}
