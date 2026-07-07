const DEFAULT_MIME_TYPE = 'audio/mpeg';
const DEFAULT_MIN_BUFFERED_CHUNKS = 2;

const toArrayBuffer = (chunk: Uint8Array): ArrayBuffer => {
  const copy = new Uint8Array(chunk.byteLength);
  copy.set(chunk);
  return copy.buffer;
};

export interface WebSocketAudioJitterBufferOptions {
  mimeType?: string;
  minBufferedChunks?: number;
  createAudioElement?: () => HTMLAudioElement;
  createMediaSource?: () => MediaSource;
  createObjectUrl?: (object: Blob | MediaSource) => string;
  revokeObjectUrl?: (url: string) => void;
}

export interface WebSocketAudioJitterBufferResult {
  audioUrl: string;
  streamed: boolean;
  chunkCount: number;
}

export class WebSocketAudioJitterBuffer {
  private readonly mimeType: string;
  private readonly minBufferedChunks: number;
  private readonly createAudioElement: () => HTMLAudioElement;
  private readonly createMediaSource?: () => MediaSource;
  private readonly createObjectUrl: (object: Blob | MediaSource) => string;
  private readonly revokeObjectUrl: (url: string) => void;
  private readonly chunks: Uint8Array[] = [];
  private audio: HTMLAudioElement | null = null;
  private mediaSource: MediaSource | null = null;
  private sourceBuffer: SourceBuffer | null = null;
  private objectUrl: string | null = null;
  private pendingAppends: Uint8Array[] = [];
  private streamEnded = false;
  private started = false;
  private playbackRequested = false;
  private playbackAttempt: Promise<void> | null = null;

  constructor(options: WebSocketAudioJitterBufferOptions = {}) {
    this.mimeType = options.mimeType ?? DEFAULT_MIME_TYPE;
    this.minBufferedChunks = options.minBufferedChunks ?? DEFAULT_MIN_BUFFERED_CHUNKS;
    this.createAudioElement = options.createAudioElement ?? (() => new Audio());
    this.createMediaSource = options.createMediaSource;
    this.createObjectUrl = options.createObjectUrl ?? ((object) => URL.createObjectURL(object));
    this.revokeObjectUrl = options.revokeObjectUrl ?? ((url) => URL.revokeObjectURL(url));
  }

  get chunkCount(): number {
    return this.chunks.length;
  }

  get isStreaming(): boolean {
    return this.started;
  }

  start(): void {
    this.reset();
    if (!this.canUseMediaSource()) {
      return;
    }

    this.mediaSource = this.createMediaSource ? this.createMediaSource() : new MediaSource();
    this.objectUrl = this.createObjectUrl(this.mediaSource);
    this.audio = this.createAudioElement();
    this.audio.src = this.objectUrl;

    this.mediaSource.addEventListener('sourceopen', () => {
      if (!this.mediaSource || this.sourceBuffer) {
        return;
      }
      this.sourceBuffer = this.mediaSource.addSourceBuffer(this.mimeType);
      this.sourceBuffer.addEventListener('updateend', () => this.flushAppends());
      this.flushAppends();
    });
  }

  push(chunk: Uint8Array): void {
    if (!chunk.length) {
      return;
    }
    this.chunks.push(chunk);

    if (!this.mediaSource) {
      return;
    }

    this.pendingAppends.push(chunk);
    if (!this.playbackRequested && this.chunks.length >= this.minBufferedChunks) {
      this.playbackRequested = true;
      const playPromise = this.audio?.play();
      this.playbackAttempt = playPromise
        ? playPromise
            .then(() => {
              this.started = true;
            })
            .catch((error) => {
              this.playbackRequested = false;
              this.started = false;
              console.warn('WebSocket audio stream playback failed', error);
            })
        : null;
    }
    this.flushAppends();
  }

  async finish(): Promise<WebSocketAudioJitterBufferResult | null> {
    this.streamEnded = true;
    this.flushAppends();
    await this.playbackAttempt;

    if (this.mediaSource && this.sourceBuffer && !this.sourceBuffer.updating && this.mediaSource.readyState === 'open') {
      this.mediaSource.endOfStream();
    }

    if (!this.chunks.length) {
      this.reset();
      return null;
    }

    const blob = new Blob(this.chunks.map(toArrayBuffer), { type: this.mimeType });
    const finalUrl = this.createObjectUrl(blob);
    const streamed = this.started;

    this.releaseStreamingResources({ keepFinalUrl: finalUrl, keepStreaming: streamed });
    return {
      audioUrl: finalUrl,
      streamed,
      chunkCount: this.chunks.length,
    };
  }

  reset(): void {
    this.audio?.pause();
    this.releaseStreamingResources();
    this.chunks.length = 0;
    this.pendingAppends.length = 0;
    this.streamEnded = false;
    this.started = false;
    this.playbackRequested = false;
    this.playbackAttempt = null;
  }

  private canUseMediaSource(): boolean {
    const mediaSourceCtor = globalThis.MediaSource;
    return Boolean(mediaSourceCtor?.isTypeSupported?.(this.mimeType));
  }

  private flushAppends(): void {
    if (!this.sourceBuffer || this.sourceBuffer.updating || !this.pendingAppends.length) {
      return;
    }

    const nextChunk = this.pendingAppends.shift();
    if (nextChunk) {
      this.sourceBuffer.appendBuffer(toArrayBuffer(nextChunk));
    }

    if (
      this.streamEnded &&
      this.pendingAppends.length === 0 &&
      !this.sourceBuffer.updating &&
      this.mediaSource?.readyState === 'open'
    ) {
      this.mediaSource.endOfStream();
    }
  }

  private releaseStreamingResources(options: { keepFinalUrl?: string; keepStreaming?: boolean } = {}): void {
    if (options.keepStreaming) {
      return;
    }

    this.audio?.pause();
    this.audio = null;
    this.sourceBuffer = null;
    this.mediaSource = null;
    this.pendingAppends.length = 0;
    if (this.objectUrl && this.objectUrl !== options.keepFinalUrl) {
      this.revokeObjectUrl(this.objectUrl);
    }
    this.objectUrl = null;
  }
}
