import {API_ORIGIN} from './api';
import {EventParser} from './event-parser';
import {EventSession} from './event-session';
import {EventReducer, type JobState, type ServerEvent} from './event-reducer';
export type {ServerEvent, JobState} from './event-reducer';
export type EventOptions = {snapshot: (jobs:JobState[])=>void; error?: (code:string)=>void};
export type EventSubscription = (()=>void) & {
  changeScope:(url:string)=>void;
  readonly state:'connecting'|'streaming'|'halted'|'closed';
  readonly haltReason:string|undefined;
  readonly cleanupState:EventSession['cleanupState'];
  readonly revocationState:EventSession['revocationState'];
};
function targetURL(url:string): string {
  try {
    if (url.length > 4096 || /%(?![0-9a-fA-F]{2})/.test(url)) throw new Error();
    decodeURIComponent(url);
    const target = new URL(url);
    if (target.origin !== API_ORIGIN || target.pathname !== '/api/events' || target.username || target.password || target.hash) throw new Error();
    let song = false;
    const known = new Set<string>();
    for (const [key, value] of target.searchParams) {
      if (!/^[0-7][0-9A-HJKMNP-TV-Z]{25}$/.test(value)) throw new Error();
      if (key === 'song_id' && !song) song = true;
      else if (key === 'known_job_id' && !known.has(value) && known.size < 64) known.add(value);
      else throw new Error();
    }
    return target.href;
  } catch {throw new Error('INVALID_EVENT_URL');}
}
export function subscribeEvents(url:string, receive:(event:ServerEvent)=>void, options:EventOptions): EventSubscription {
  if (!options || typeof options.snapshot !== 'function') throw new Error('SNAPSHOT_CONSUMER_REQUIRED');
  let target = targetURL(url);
  const session = new EventSession();
  let stopped = false;
  let halted = false;
  let state:EventSubscription['state'] = 'connecting';
  let haltReason:string|undefined;
  let generation = 0;
  let callbackFailed = false;
  function callback<T>(fn: (value:T)=>void, value:T) {
    try {fn(value);} catch {callbackFailed = true; throw new Error('CALLBACK_FAILED');}
  }
  const reducer = new EventReducer(event => callback(receive, event), jobs => callback(options.snapshot, jobs));
  const reported = new Set<string>();
  const report = (code:string) => {
    haltReason ??= code;
    if (reported.has(code)) return;
    reported.add(code);
    try {options.error?.(code);} catch {/* External callbacks cannot leak a rejection or credentials. */}
  };
  const finish = () => {
    void session.close().then(() => {
      if (session.cleanupState === 'unknown') report('EVENT_CANCEL_UNCONFIRMED');
      if (session.revocationState === 'unknown') report('EVENT_REVOKE_UNCONFIRMED');
    }).catch(() => report('EVENT_CANCEL_UNCONFIRMED'));
  };
  const halt = (code:string) => {
    if (!stopped) {halted = true; state = 'halted'; haltReason = code;}
    report(code); finish();
  };
  const cancelResponse = async (response:Response) => {
    if (await session.cancelResponse(response) === 'unknown') {halt('EVENT_CANCEL_UNCONFIRMED'); return false;}
    return true;
  };
  let renewed = false;
  async function run(endpoint:string, version:number) {
    for (let attempt = 0; attempt < 5 && !session.stopped && !stopped && !halted && version === generation; attempt++) {
      const parser = new EventParser(frame => {
        if (!session.stopped && !stopped && !halted && version === generation) reducer.accept(frame);
      });
      try {
        const response = await session.open(endpoint, reducer.cursor);
        if (session.stopped || stopped || version !== generation) {await cancelResponse(response); break;}
        if (response.status === 401 && !renewed) {
          if (!await cancelResponse(response)) return;
          if (attempt === 4) {halt('EVENT_RETRY_LIMIT'); break;}
          await session.renew(); renewed = true; continue;
        }
        if (response.status === 401 || response.status === 403 || response.status === 422 || response.status === 503) {
          if (!await cancelResponse(response)) return;
          halt('EVENT_STREAM_UNAVAILABLE'); break;
        }
        if (response.status !== 200 || response.headers.get('Content-Type')?.split(';')[0].trim().toLowerCase() !== 'text/event-stream') {
          if (!await cancelResponse(response)) return;
          throw new Error('INVALID_RESPONSE');
        }
        state = 'streaming';
        await session.read(response, bytes => parser.push(bytes));
        parser.finish();
      } catch {
        if (session.cleanupState === 'unknown') {halt('EVENT_CANCEL_UNCONFIRMED'); break;}
        if (session.revocationState === 'unknown') {halt('EVENT_REVOKE_UNCONFIRMED'); break;}
        if (session.stopped || stopped || version !== generation) break;
        if (callbackFailed) {halt('EVENT_CALLBACK_FAILED'); break;}
      } finally {if (version === generation) reducer.discard();}
      if (stopped || halted || version !== generation) break;
      if (attempt === 4) {halt('EVENT_RETRY_LIMIT'); break;}
      state = 'connecting';
      await session.wait(250 * 2 ** attempt);
    }
  }
  let running = run(target, generation).catch(() => halt('EVENT_CANCEL_UNCONFIRMED'));
  const close = (() => {
    if (stopped) return;
    stopped = true; state = 'closed'; generation++; session.abortConnection(); reducer.discard(); finish();
  }) as EventSubscription;
  Object.defineProperties(close, {
    state:{get:()=>state}, haltReason:{get:()=>haltReason},
    cleanupState:{get:()=>session.cleanupState}, revocationState:{get:()=>session.revocationState},
  });
  close.changeScope = (url:string) => {
    const next = targetURL(url);
    if (halted && !stopped) throw new Error('EVENT_SUBSCRIPTION_HALTED');
    if (stopped || next === target) return;
    target = next; generation++; session.abortConnection(); state = 'connecting';
    const version = generation;
    try {reducer.clear();} catch {close(); return;}
    if (version !== generation) return;
    running = running.then(() => {
      if (stopped || halted || version !== generation) return;
      if (session.cleanupState === 'unknown') {halt('EVENT_CANCEL_UNCONFIRMED'); return;}
      callbackFailed = false;
      return run(target, version);
    }).catch(() => halt('EVENT_CANCEL_UNCONFIRMED'));
  };
  return close;
}
