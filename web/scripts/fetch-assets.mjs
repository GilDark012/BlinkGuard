// Copies the MediaPipe runtime into public/ and downloads the face model once,
// so the app never loads code or models from a third-party server at runtime.
import { copyFileSync, existsSync, mkdirSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const target = join(root, 'public', 'mediapipe');
const wasmSrc = join(root, 'node_modules', '@mediapipe', 'tasks-vision', 'wasm');
const wasmDst = join(target, 'wasm');

mkdirSync(wasmDst, { recursive: true });
for (const file of readdirSync(wasmSrc)) {
  copyFileSync(join(wasmSrc, file), join(wasmDst, file));
}

const MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task';
const modelPath = join(target, 'face_landmarker.task');

if (!existsSync(modelPath)) {
  console.log('Downloading the MediaPipe face landmarker model...');
  const res = await fetch(MODEL_URL);
  if (!res.ok) throw new Error(`Model download failed: HTTP ${res.status}`);
  writeFileSync(modelPath, Buffer.from(await res.arrayBuffer()));
}
console.log('MediaPipe assets ready in public/mediapipe');
