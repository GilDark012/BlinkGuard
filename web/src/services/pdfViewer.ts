import { getDocument, GlobalWorkerOptions, type PDFDocumentProxy, type RenderTask } from 'pdfjs-dist';
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { PDF_CONFIG } from '../config';

GlobalWorkerOptions.workerSrc = workerUrl;

/** Renders a local PDF file onto a canvas with pdf.js. The file never leaves the browser. */
export class PdfViewer {
  page = 1;
  zoom: number = PDF_CONFIG.defaultZoom;
  private doc: PDFDocumentProxy | null = null;
  private renderTask: RenderTask | null = null;

  constructor(private readonly canvas: HTMLCanvasElement) {}

  get total(): number {
    return this.doc?.numPages ?? 0;
  }

  get loaded(): boolean {
    return this.doc !== null;
  }

  /** Loads a new document. On failure the previous one stays open. */
  async load(data: ArrayBuffer): Promise<void> {
    const doc = await getDocument({
      data,
      // Untrusted input: never evaluate code from the file.
      isEvalSupported: false,
      enableXfa: false,
    }).promise;
    if (doc.numPages === 0) {
      await doc.destroy();
      throw new Error('empty document');
    }
    await this.doc?.destroy();
    this.doc = doc;
    this.page = 1;
    await this.render();
  }

  async goTo(page: number): Promise<boolean> {
    if (!this.doc || page < 1 || page > this.total || page === this.page) return false;
    this.page = page;
    await this.render();
    return true;
  }

  async setZoom(zoom: number): Promise<void> {
    const clamped = Math.min(PDF_CONFIG.maxZoom, Math.max(PDF_CONFIG.minZoom, Math.round(zoom * 100) / 100));
    if (clamped === this.zoom) return;
    this.zoom = clamped;
    await this.render();
  }

  private async render(): Promise<void> {
    if (!this.doc) return;
    this.renderTask?.cancel();
    const page = await this.doc.getPage(this.page);
    const viewport = page.getViewport({ scale: this.zoom });
    const dpr = window.devicePixelRatio || 1;
    const canvas = this.canvas;
    canvas.width = Math.floor(viewport.width * dpr);
    canvas.height = Math.floor(viewport.height * dpr);
    canvas.style.width = `${Math.floor(viewport.width)}px`;
    canvas.style.height = `${Math.floor(viewport.height)}px`;
    const context = canvas.getContext('2d');
    if (!context) return;
    const task = page.render({
      canvasContext: context,
      viewport,
      transform: dpr === 1 ? undefined : [dpr, 0, 0, dpr, 0, 0],
    });
    this.renderTask = task;
    try {
      await task.promise;
    } catch (e) {
      // A newer render replaced this one: not an error.
      if (!(e instanceof Error && e.name === 'RenderingCancelledException')) throw e;
    } finally {
      if (this.renderTask === task) this.renderTask = null;
    }
  }
}
