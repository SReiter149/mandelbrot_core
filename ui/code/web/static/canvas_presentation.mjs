import { worldToCanvas } from './state.mjs';

let parameterCurves;
export function loadParameterCurves() {
  return parameterCurves ||= fetch('/api/mandelbrot').then(async response => {
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || 'Unable to load live curves');
    return result;
  });
}

export function setup(canvas, bounds) {
  const { width, height } = canvas.getBoundingClientRect();
  const ratio = Math.min(devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  const transform = { width, height, bounds };
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

export function drawPath(ctx, transform, points, color, markers = false, style = null) {
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
