import { RaysState } from './rays_state.mjs';
import { setup, drawPrimitive } from './canvas_presentation.mjs';
import { wheelBoundsAt } from './state.mjs';

const $ = id => document.getElementById(id);
const defaults = {xmin: -2, xmax: 2, ymin: -2, ymax: 2};
const bounds = {source: {...defaults}, image: {...defaults}};
const transforms = {};
const controllers = new Map();
let state;

function error(message = '') {
  $('rays-error').textContent = message;
  $('rays-error').hidden = !message;
}

function render() {
  if ($('rays-workspace').hidden) return;
  for (const plane of ['source', 'image']) {
    // The core currently uses black points: keep its styles, on a light plane.
    const {ctx, transform} = setup($(`rays-${plane}`), bounds[plane], '#ffffff');
    transforms[plane] = transform;
    const primitives = [...(state?.curves.values() || [])].flatMap(curve => curve[plane]);
    primitives.sort((a, b) => a.style.zorder - b.style.zorder);
    for (const primitive of primitives) drawPrimitive(ctx, transform, primitive);
  }
}

function renderList() {
  $('rays-list').replaceChildren();
  if (!state) return;
  $('rays-status').textContent = `${state.curves.size} curves · ${state.pending.size} pending`;
  const records = new Map([...state.curves, ...state.pending]);
  for (const [id, record] of records) {
    const row = document.createElement('div');
    row.className = 'selection-row';
    const text = document.createElement('span');
    text.textContent = `${record.expression} · ${record.variable}: ${record.start}…${record.end}, step ${record.step}${state.pending.has(id) ? ' · loading…' : ''}`;
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'secondary'; button.textContent = 'Remove';
    button.setAttribute('aria-label', `Remove ${id}`);
    button.addEventListener('click', () => {
      controllers.get(id)?.abort(); controllers.delete(id);
      state.remove(id); renderList(); render();
    });
    row.append(text, button); $('rays-list').append(row);
  }
}

$('rays-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (!state) return;
  error();
  const request = state.begin({expression: $('rays-expression').value,
    variable: $('rays-variable').value, start: Number($('rays-start').value),
    end: Number($('rays-end').value), step: Number($('rays-step').value)});
  const controller = new AbortController();
  controllers.set(request.curve_id, controller);
  renderList();
  try {
    const response = await fetch('/api/rays/curve', {method: 'POST',
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify(request), signal: controller.signal});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || 'Core curve request failed');
    state.accept(result);
  } catch (exc) {
    if (state.current(request)) {
      state.reject(request);
      if (exc.name !== 'AbortError') error(exc.message);
    }
  } finally {
    controllers.delete(request.curve_id);
    renderList(); render();
  }
});

$('rays-clear').addEventListener('click', () => {
  for (const controller of controllers.values()) controller.abort();
  controllers.clear(); state?.clear(); error(); renderList(); render();
});
for (const plane of ['source', 'image']) {
  const canvas = $(`rays-${plane}`);
  canvas.addEventListener('wheel', event => {
    if (!transforms[plane]) return;
    event.preventDefault();
    const rect = canvas.getBoundingClientRect();
    bounds[plane] = wheelBoundsAt({x: event.clientX - rect.left, y: event.clientY - rect.top},
      transforms[plane], event);
    render();
  }, {passive: false});
  $(`rays-reset-${plane}`).addEventListener('click', () => {
    bounds[plane] = {...defaults}; render();
  });
  new ResizeObserver(render).observe(canvas.parentElement);
}
window.addEventListener('explorer-mode', render);

// Once per full document load, including when another mode is initially visible.
try {
  const response = await fetch('/api/rays/session');
  const session = await response.json();
  if (!response.ok) throw new Error(session.error?.message || 'Unable to load coefficients');
  state = new RaysState(session);
  $('rays-coefficients').textContent = `Using ${session.coefficient_count} coefficients`;
  $('rays-add').disabled = false;
  renderList(); render();
} catch (exc) {
  $('rays-coefficients').textContent = 'Coefficients unavailable';
  $('rays-status').textContent = 'Coefficients unavailable';
  error(exc.message);
}
