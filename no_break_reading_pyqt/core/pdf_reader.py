"""Module de lecture et gestion de PDF"""
import time

import pymupdf as fitz
import numpy as np

from config import PDF_CONFIG


class PDFReader:
    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self.document = None
        self.file_path = None
        self.zoom_level = PDF_CONFIG['default_zoom']
        self.last_error = None
        self._reset_session()

    def _reset_session(self):
        self.current_page = 0
        self.total_pages = 0
        self.reading_start_time = None
        self.page_read_times = {}
        self.visited_pages = set()
        self.current_page_start_time = None

    def load_pdf(self, file_path):
        """Charge un PDF. Retourne False (et renseigne last_error) en cas d'échec."""
        try:
            document = fitz.open(file_path)
            if document.page_count == 0:
                document.close()
                raise ValueError("le document ne contient aucune page")
        except Exception as e:
            self.last_error = str(e)
            return False

        self.close()
        self.document = document
        self.file_path = file_path
        self.last_error = None
        self._reset_session()
        self.total_pages = document.page_count
        now = self._clock()
        self.reading_start_time = now
        self.current_page_start_time = now
        self.visited_pages.add(0)
        return True

    def get_current_page_image(self, zoom=None):
        """Retourne la page courante en tableau RGB (h, w, 3), ou None."""
        if not self.document:
            return None
        zoom = self.zoom_level if zoom is None else zoom
        try:
            page = self.document[self.current_page]
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            img = np.frombuffer(pix.samples, dtype=np.uint8)
            # pix.stride peut être > width * 3 (alignement) : on en tient compte
            img = img.reshape(pix.height, pix.stride)[:, :pix.width * pix.n]
            return np.ascontiguousarray(img.reshape(pix.height, pix.width, pix.n))
        except Exception as e:
            self.last_error = str(e)
            return None

    def go_to_page(self, index):
        if not self.document or not 0 <= index < self.total_pages or index == self.current_page:
            return False
        self.update_reading_time()
        self.current_page = index
        self.visited_pages.add(index)
        self.current_page_start_time = self._clock()
        return True

    def next_page(self):
        return self.go_to_page(self.current_page + 1)

    def previous_page(self):
        return self.go_to_page(self.current_page - 1)

    def set_zoom(self, zoom):
        self.zoom_level = max(PDF_CONFIG['min_zoom'], min(PDF_CONFIG['max_zoom'], zoom))

    def update_reading_time(self):
        if self.current_page_start_time is None:
            return
        now = self._clock()
        self.page_read_times[self.current_page] = (
            self.page_read_times.get(self.current_page, 0.0) + now - self.current_page_start_time
        )
        self.current_page_start_time = now

    def get_reading_statistics(self):
        if self.reading_start_time is None:
            return {'total_time': 0, 'pages_read': 0, 'avg_time_per_page': 0,
                    'current_page': 0, 'total_pages': 0, 'progress': 0}
        total_time = self._clock() - self.reading_start_time
        pages_read = len(self.visited_pages)
        return {
            'total_time': total_time,
            'pages_read': pages_read,
            'avg_time_per_page': total_time / pages_read if pages_read else 0,
            'current_page': self.current_page + 1,
            'total_pages': self.total_pages,
            'progress': (self.current_page + 1) / self.total_pages * 100 if self.total_pages else 0,
        }

    def close(self):
        if self.document:
            self.update_reading_time()
            self.document.close()
            self.document = None
