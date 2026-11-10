// One page owns this model, independently of mode visibility.
export class RaysState {
  constructor(session) {
    this.session = Object.freeze({...session});
    this.curves = new Map();
    this.pending = new Map();
    this.nextId = 1;
    this.revision = 0;
  }
  begin(draft, id = `curve-${this.nextId++}`) {
    const request = {...draft, curve_id: id, request_revision: ++this.revision,
      session_token: this.session.session_token};
    this.pending.set(id, request);
    return request;
  }
  current(response) {
    const request = this.pending.get(response.curve_id);
    return request && request.request_revision === response.request_revision &&
      response.session_token === this.session.session_token;
  }
  accept(response) {
    if (!this.current(response)) return false;
    this.curves.set(response.curve_id, {...this.pending.get(response.curve_id), ...response});
    this.pending.delete(response.curve_id);
    return true;
  }
  reject(request) {
    if (this.current(request)) this.pending.delete(request.curve_id);
  }
  remove(id) {
    this.curves.delete(id);
    this.pending.delete(id);
  }
  clear() {
    this.curves.clear();
    this.pending.clear();
  }
}
