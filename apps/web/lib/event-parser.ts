export type SSEFrame = {event: string; id?: string; data: unknown};
export const MAX_FRAME_BYTES = 65536;

export function parseCursor(value: string): {epoch: string; seq: number} {
  const match = /^([a-f0-9]{32}):([1-9][0-9]{0,15})$/.exec(value);
  if (!match || !Number.isSafeInteger(Number(match[2]))) throw new Error('INVALID_CURSOR');
  return {epoch: match[1], seq: Number(match[2])};
}

/** Byte cap precedes every append; no unbounded decoded chunk concatenation. */
export class EventParser {
  private line: number[] = [];
  private size = 0;
  private event?: string;
  private id?: string;
  private data: string[] = [];
  private decoder = new TextDecoder('utf-8', {fatal: true});

  constructor(private receive: (frame: SSEFrame) => void) {}

  push(bytes: Uint8Array) {
    for (const byte of bytes) {
      if (++this.size > MAX_FRAME_BYTES) throw new Error('FRAME_LIMIT');
      if (byte !== 10) {this.line.push(byte); continue;}
      if (this.line.at(-1) === 13) this.line.pop();
      const text = this.decoder.decode(new Uint8Array(this.line));
      this.line = [];
      if (text === '') {
        if (this.data.length) {
          const value: unknown = JSON.parse(this.data.join('\n'));
          this.receive({event: this.event ?? 'message', id: this.id, data: value});
        } else if (this.id !== undefined || this.event !== undefined) throw new Error('EMPTY_FRAME');
        this.size = 0; this.event = undefined; this.id = undefined; this.data = [];
        continue;
      }
      if (text.startsWith(':')) continue;
      const colon = text.indexOf(':');
      const field = colon < 0 ? text : text.slice(0, colon);
      let value = colon < 0 ? '' : text.slice(colon + 1);
      if (value.startsWith(' ')) value = value.slice(1);
      if (field === 'data') this.data.push(value);
      else if (field === 'id') {
        if (this.id !== undefined) throw new Error('DUPLICATE_FIELD');
        parseCursor(value); this.id = value;
      } else if (field === 'event') {
        if (this.event !== undefined || !value) throw new Error('INVALID_EVENT');
        this.event = value;
      } else throw new Error('UNKNOWN_FIELD');
    }
  }

  finish() {
    if (this.size || this.line.length || this.data.length) throw new Error('PARTIAL_FRAME');
  }
}
