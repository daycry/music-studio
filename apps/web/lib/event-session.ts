import {API_ORIGIN} from './api';

export const CLEANUP_DEADLINE_MS = 2000;
type Outcome = 'confirmed' | 'unknown';
type Cleanup = {status: 'pending' | Outcome; completion: Promise<void>};

/** One credential owner per subscription; connections may be replaced independently. */
export class EventSession {
  private token?: string;
  private bootstrap?: Promise<void>;
  private lifetime = new AbortController();
  private connection?: AbortController;
  private reader?: ReadableStreamDefaultReader<Uint8Array>;
  private timer?: ReturnType<typeof setTimeout>;
  private wake?: () => void;
  private cleanups = new Map<object, Cleanup>();
  private cleaned = false;
  private closing?: Promise<void>;
  stopped = false;
  revocationState: 'idle' | 'pending' | Outcome | 'inactive' = 'idle';

  get cleanupState(): 'idle' | 'pending' | Outcome {
    const values = [...this.cleanups.values()];
    if (values.some(value => value.status === 'unknown')) return 'unknown';
    if (values.length) return 'pending';
    return this.cleaned ? 'confirmed' : 'idle';
  }

  get retainedCleanupCount() {return this.cleanups.size;}

  private async bounded<T>(operation: () => Promise<T>, duration: number, signal: AbortSignal, code: string): Promise<T> {
    if (signal.aborted) throw new Error('CLOSED');
    let timer!: ReturnType<typeof setTimeout>;
    let abort!: () => void;
    const interrupted = new Promise<never>((_, reject) => {
      abort = () => reject(new Error('CLOSED'));
      signal.addEventListener('abort', abort, {once: true});
      timer = setTimeout(() => reject(new Error(code)), duration);
    });
    try {return await Promise.race([operation(), interrupted]);}
    finally {clearTimeout(timer); signal.removeEventListener('abort', abort);}
  }

  private async credential() {
    if (this.token) return;
    if (!this.bootstrap) {
      const credential = new AbortController();
      const abort = () => credential.abort();
      this.lifetime.signal.addEventListener('abort', abort, {once: true});
      this.bootstrap = this.bounded(async () => {
        const response = await fetch(API_ORIGIN + '/api/session/bootstrap', {
          method: 'POST', credentials: 'omit', cache: 'no-store', redirect: 'error',
          signal: credential.signal, headers: {'X-Studio-Session-Bootstrap': '1'},
        });
        if (!response.ok) throw new Error('BOOTSTRAP_FAILED');
        const dto: unknown = await response.json();
        if (!dto || typeof dto !== 'object' || Array.isArray(dto)) throw new Error('INVALID_SESSION');
        const value = dto as Record<string, unknown>;
        if (Object.keys(value).sort().join(',') !== 'expires_in_s,session_token' ||
            typeof value.session_token !== 'string' || !/^[A-Za-z0-9_-]{1,64}$/.test(value.session_token) ||
            !Number.isInteger(value.expires_in_s) || (value.expires_in_s as number) < 1 || (value.expires_in_s as number) > 28800) throw new Error('INVALID_SESSION');
        if (this.stopped || credential.signal.aborted) {await this.revoke(value.session_token); throw new Error('CLOSED');}
        this.token = value.session_token;
      }, 30000, credential.signal, 'OPEN_TIMEOUT').catch(error => {
        credential.abort();
        this.bootstrap = undefined;
        throw error;
      }).finally(() => {credential.abort(); this.lifetime.signal.removeEventListener('abort', abort);});
    }
    await this.bootstrap;
  }

  async open(url: string, cursor?: string): Promise<Response> {
    if (this.stopped) throw new Error('CLOSED');
    if (this.cleanups.size) throw new Error('EVENT_CANCEL_UNCONFIRMED');
    if (this.reader) throw new Error('CONNECTION_BUSY');
    this.abortConnection();
    const connection = this.connection = new AbortController();
    try {
      return await this.bounded(async () => {
        await this.credential();
        if (connection.signal.aborted || this.stopped) throw new Error('CLOSED');
        const headers: Record<string, string> = {Accept: 'text/event-stream', 'X-Studio-Session-Token': this.token!};
        if (cursor) headers['Last-Event-ID'] = cursor;
        const response = await fetch(url, {credentials: 'omit', cache: 'no-store', redirect: 'error', signal: connection.signal, headers});
        if (connection.signal.aborted) {await this.cancelResponse(response); throw new Error('CLOSED');}
        return response;
      }, 30000, connection.signal, 'OPEN_TIMEOUT');
    } catch (error) {connection.abort(); throw error;}
  }

  private async cancel(resource: object, operation: () => Promise<void>, release: () => void): Promise<Outcome> {
    let record = this.cleanups.get(resource);
    if (!record) {
      record = {status: 'pending', completion: Promise.resolve()};
      this.cleanups.set(resource, record);
      const owned = record;
      owned.completion = Promise.resolve().then(operation).then(() => {
        release(); owned.status = 'confirmed'; this.cleanups.delete(resource); this.cleaned = true;
      }).catch(() => {owned.status = 'unknown';});
    }
    const owned = record;
    let deadline!: ReturnType<typeof setTimeout>;
    const timeout = new Promise<Outcome>(resolve => {
      deadline = setTimeout(() => {owned.status = 'unknown'; resolve('unknown');}, CLEANUP_DEADLINE_MS);
    });
    try {return await Promise.race([owned.completion.then(() => owned.status as Outcome), timeout]);}
    finally {clearTimeout(deadline);}
  }

  async cancelResponse(response: Response): Promise<Outcome> {
    const body = response.body;
    return body ? this.cancel(body, () => body.cancel(), () => undefined) : 'confirmed';
  }

  private cleanupReader(reader: ReadableStreamDefaultReader<Uint8Array>): Promise<Outcome> {
    return this.cancel(reader, () => reader.cancel(), () => {
      reader.releaseLock(); if (this.reader === reader) this.reader = undefined;
    });
  }

  async read(response: Response, receive: (bytes: Uint8Array) => void): Promise<void> {
    if (!response.body) throw new Error('MISSING_STREAM');
    const reader = this.reader = response.body.getReader();
    const connection = this.connection ??= new AbortController();
    let failed = false;
    let firstCause: unknown;
    try {
      while (!this.stopped && !connection.signal.aborted) {
        // A waiter belongs to one read only; a stream-long pending promise
        // would retain another race reaction for every completed chunk.
        let aborted!: () => void;
        const interrupted = new Promise<never>((_, reject) => {
          aborted = () => reject(new Error('CONNECTION_CLOSED'));
          connection.signal.addEventListener('abort', aborted, {once: true});
        });
        const timeout = new Promise<never>((_, reject) => {
          this.timer = setTimeout(() => {reject(new Error('READ_TIMEOUT')); connection.abort();}, 45000);
        });
        let result:ReadableStreamReadResult<Uint8Array>;
        try {result = await Promise.race([reader.read(), interrupted, timeout]);}
        finally {
          clearTimeout(this.timer); this.timer = undefined;
          connection.signal.removeEventListener('abort', aborted);
        }
        if (this.stopped || connection.signal.aborted || result.done) break;
        receive(result.value);
      }
    } catch (error) {failed = true; firstCause = error;}
    finally {
      clearTimeout(this.timer); this.timer = undefined;
      const outcome = await this.cleanupReader(reader);
      if (!failed && outcome === 'unknown') {failed = true; firstCause = new Error('EVENT_CANCEL_UNCONFIRMED');}
    }
    if (failed) throw firstCause;
  }

  wait(delay: number): Promise<void> {
    if (this.stopped) return Promise.resolve();
    return new Promise(resolve => {
      this.wake = resolve;
      this.timer = setTimeout(() => {this.timer = undefined; this.wake = undefined; resolve();}, delay);
    });
  }

  abortConnection() {
    this.connection?.abort();
    clearTimeout(this.timer); this.timer = undefined;
    this.wake?.(); this.wake = undefined;
  }

  private async revoke(token: string): Promise<Outcome | 'inactive'> {
    const controller = new AbortController();
    this.revocationState = 'pending';
    try {
      const response = await this.bounded(() => fetch(API_ORIGIN + '/api/session', {
        method: 'DELETE', credentials: 'omit', cache: 'no-store', redirect: 'error',
        signal: controller.signal, headers: {'X-Studio-Session-Token': token},
      }), CLEANUP_DEADLINE_MS, controller.signal, 'REVOKE_TIMEOUT');
      const cleanup = await this.cancelResponse(response);
      if (response.status !== 204 && response.status !== 401 || cleanup === 'unknown') throw new Error('REVOKE_UNCONFIRMED');
      this.revocationState = response.status === 204 ? 'confirmed' : 'inactive';
    } catch {this.revocationState = 'unknown';}
    finally {controller.abort();}
    return this.revocationState;
  }

  async renew() {
    const token = this.token;
    this.token = undefined; this.bootstrap = undefined;
    if (token && await this.revoke(token) === 'unknown') throw new Error('EVENT_REVOKE_UNCONFIRMED');
  }

  close(): Promise<void> {
    if (this.closing) return this.closing;
    this.stopped = true;
    this.lifetime.abort(); this.abortConnection();
    const token = this.token; this.token = undefined;
    this.closing = Promise.all([
      this.reader ? this.cleanupReader(this.reader) : Promise.resolve(),
      token ? this.revoke(token) : Promise.resolve(),
    ]).then(() => undefined);
    return this.closing;
  }
}
