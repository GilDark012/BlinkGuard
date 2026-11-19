import { defineConfig, type Plugin } from 'vitest/config';

/**
 * Content-Security-Policy added to the production build only
 * (the dev server injects inline styles for hot reload).
 * Everything is served from our own origin: no CDN, no analytics, no network calls.
 */
const CSP = [
  "default-src 'self'",
  "script-src 'self' 'wasm-unsafe-eval'",
  "worker-src 'self' blob:",
  "style-src 'self'",
  "img-src 'self' data: blob:",
  "media-src 'self' blob: mediastream:",
  "connect-src 'self'",
  "font-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'none'",
].join('; ');

function contentSecurityPolicy(): Plugin {
  return {
    name: 'blinkguard-csp',
    apply: 'build',
    transformIndexHtml: (html) =>
      html.replace('<head>', `<head>\n    <meta http-equiv="Content-Security-Policy" content="${CSP}">`),
  };
}

export default defineConfig({
  base: './',
  plugins: [contentSecurityPolicy()],
  build: { target: 'es2022', sourcemap: true },
  test: { environment: 'node', include: ['src/**/*.test.ts'] },
});
