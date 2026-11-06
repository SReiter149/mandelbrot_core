// Shared input transport. Sage, not JavaScript, interprets arithmetic expressions.
export async function evaluatePoint(expression) {
  const response = await fetch('/api/point', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({expression}),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error?.message || 'Unable to evaluate point');
  return result.point;
}

export function bindPointEntry(formId, inputId, selectPoint, showError) {
  const form = document.getElementById(formId);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      selectPoint(await evaluatePoint(document.getElementById(inputId).value));
    } catch (error) {
      showError(error.message);
    } finally {
      button.disabled = false;
    }
  });
}
