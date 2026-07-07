import { describe, expect, it, vi, beforeEach } from 'vitest';
import { WebSocketAudioJitterBuffer } from '@/lib/ws-audio-jitter-buffer';

class FakeAudio {
  src = '';
  play = vi.fn().mockResolvedValue(undefined);
  pause = vi.fn();
}

class FakeSourceBuffer extends EventTarget {
  updating = false;
  appended: number[][] = [];

  appendBuffer(chunk: ArrayBuffer) {
    this.updating = true;
    this.appended.push(Array.from(new Uint8Array(chunk)));
    this.updating = false;
    this.dispatchEvent(new Event('updateend'));
  }
}

class FakeMediaSource extends EventTarget {
  readyState: 'closed' | 'open' | 'ended' = 'open';
  sourceBuffer = new FakeSourceBuffer();
  ended = false;

  addSourceBuffer() {
    return this.sourceBuffer as unknown as SourceBuffer;
  }

  endOfStream() {
    this.ended = true;
    this.readyState = 'ended';
  }
}

describe('WebSocketAudioJitterBuffer', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('starts streaming playback after the configured jitter buffer fills', async () => {
    vi.stubGlobal('MediaSource', {
      isTypeSupported: vi.fn(() => true),
    });

    const audio = new FakeAudio();
    const mediaSource = new FakeMediaSource();
    const createdUrls: Array<Blob | MediaSource> = [];
    const revokedUrls: string[] = [];

    const buffer = new WebSocketAudioJitterBuffer({
      minBufferedChunks: 2,
      createAudioElement: () => audio as unknown as HTMLAudioElement,
      createMediaSource: () => mediaSource as unknown as MediaSource,
      createObjectUrl: (object) => {
        createdUrls.push(object);
        return `mock-stream-url-${createdUrls.length}`;
      },
      revokeObjectUrl: (url) => revokedUrls.push(url),
    });

    buffer.start();
    mediaSource.dispatchEvent(new Event('sourceopen'));
    buffer.push(new Uint8Array([1]));

    expect(audio.play).not.toHaveBeenCalled();

    buffer.push(new Uint8Array([2]));

    expect(audio.play).toHaveBeenCalledOnce();
    expect(mediaSource.sourceBuffer.appended).toEqual([[1], [2]]);

    const result = await buffer.finish();

    expect(result).toEqual({
      audioUrl: 'mock-stream-url-2',
      streamed: true,
      chunkCount: 2,
    });
    expect(mediaSource.ended).toBe(true);
    expect(revokedUrls).toEqual([]);

    buffer.reset();

    expect(audio.pause).toHaveBeenCalled();
    expect(revokedUrls).toEqual(['mock-stream-url-1']);
  });

  it('falls back to a final blob URL when MediaSource is unavailable', async () => {
    vi.stubGlobal('MediaSource', undefined);
    const createdObjects: Array<Blob | MediaSource> = [];

    const buffer = new WebSocketAudioJitterBuffer({
      createObjectUrl: (object) => {
        createdObjects.push(object);
        return 'mock-final-url';
      },
    });

    buffer.start();
    buffer.push(new Uint8Array([1, 2, 3]));

    const result = await buffer.finish();

    expect(result).toEqual({
      audioUrl: 'mock-final-url',
      streamed: false,
      chunkCount: 1,
    });
    expect(createdObjects[0]).toBeInstanceOf(Blob);
  });
});
