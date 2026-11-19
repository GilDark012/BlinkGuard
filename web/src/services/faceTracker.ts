import { FaceLandmarker, FilesetResolver, type NormalizedLandmark } from '@mediapipe/tasks-vision';
import { EYE_CONFIG, LEFT_EYE_LANDMARKS, RIGHT_EYE_LANDMARKS } from '../config';
import { calculateEar, type Point } from '../core/ear';

export interface EyeReading {
  left: Point[];
  right: Point[];
  /** Average EAR of both eyes. */
  ear: number;
}

/**
 * MediaPipe Face Landmarker running in the browser (WebAssembly, GPU when available).
 * The runtime and the model are served from our own origin (see scripts/fetch-assets.mjs).
 */
export class FaceTracker {
  private constructor(private readonly landmarker: FaceLandmarker) {}

  static async create(): Promise<FaceTracker> {
    const base = new URL('mediapipe/', document.baseURI).href;
    const fileset = await FilesetResolver.forVisionTasks(`${base}wasm`);
    const options = (delegate: 'GPU' | 'CPU') => ({
      baseOptions: { modelAssetPath: `${base}face_landmarker.task`, delegate },
      runningMode: 'VIDEO' as const,
      numFaces: 1,
      minFaceDetectionConfidence: EYE_CONFIG.minDetectionConfidence,
      minFacePresenceConfidence: EYE_CONFIG.minDetectionConfidence,
      minTrackingConfidence: EYE_CONFIG.minTrackingConfidence,
    });
    try {
      return new FaceTracker(await FaceLandmarker.createFromOptions(fileset, options('GPU')));
    } catch {
      // No WebGL / GPU delegate: fall back to the CPU.
      return new FaceTracker(await FaceLandmarker.createFromOptions(fileset, options('CPU')));
    }
  }

  /** @returns the eye points in video pixels, or null when no face is found */
  detect(video: HTMLVideoElement, timestampMs: number): EyeReading | null {
    const result = this.landmarker.detectForVideo(video, timestampMs);
    const face = result.faceLandmarks[0];
    if (!face) return null;
    const w = video.videoWidth;
    const h = video.videoHeight;
    const pick = (indices: readonly number[]): Point[] =>
      indices
        .map((i) => face[i])
        .filter((p): p is NormalizedLandmark => p !== undefined)
        .map((p) => ({ x: p.x * w, y: p.y * h }));
    const left = pick(LEFT_EYE_LANDMARKS);
    const right = pick(RIGHT_EYE_LANDMARKS);
    return { left, right, ear: (calculateEar(left) + calculateEar(right)) / 2 };
  }

  close(): void {
    this.landmarker.close();
  }
}
