import type { MessageKey } from '../i18n';

export class CameraError extends Error {
  constructor(
    public readonly messageKey: MessageKey,
    public readonly detail = '',
  ) {
    super(detail || messageKey);
  }
}

/** Opens the front camera (video only, never audio) and plays it in `video`. */
export async function startCamera(video: HTMLVideoElement): Promise<MediaStream> {
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
    throw new CameraError('err.insecure');
  }
  let stream: MediaStream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    });
  } catch (e) {
    const name = e instanceof DOMException ? e.name : '';
    if (name === 'NotAllowedError' || name === 'SecurityError') throw new CameraError('err.cameraDenied');
    if (name === 'NotFoundError' || name === 'OverconstrainedError') throw new CameraError('err.cameraMissing');
    if (name === 'NotReadableError') throw new CameraError('err.cameraBusy');
    throw new CameraError('err.cameraGeneric', e instanceof Error ? e.message : String(e));
  }
  video.srcObject = stream;
  await video.play();
  return stream;
}

export function stopCamera(video: HTMLVideoElement, stream: MediaStream | null): void {
  stream?.getTracks().forEach((track) => track.stop());
  video.pause();
  video.srcObject = null;
}
