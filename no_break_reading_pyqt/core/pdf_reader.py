"""Module de lecture et gestion de PDF"""
import fitz
import numpy as np
import time

class PDFReader:
    def __init__(self):
        self.document = None
        self.current_page = 0
        self.total_pages = 0
        self.file_path = None
        self.zoom_level = 1.2
        self.auto_scroll_enabled = False
        self.scroll_speed = 5
        self.reading_start_time = None
        self.page_read_times = {}
        self.current_page_start_time = None

    def load_pdf(self, file_path):
        try:
            if self.document:
                self.document.close()
            self.document = fitz.open(file_path)
            self.file_path = file_path
            self.total_pages = len(self.document)
            self.current_page = 0
            self.reading_start_time = time.time()
            self.current_page_start_time = time.time()
            self.page_read_times = {}
            return True
        except Exception as e:
            print(f"Erreur chargement PDF: {e}")
            return False

    def get_current_page_image(self, zoom=None):
        if not self.document:
            return None
        if zoom is None:
            zoom = self.zoom_level
        try:
            page = self.document[self.current_page]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            return img
        except Exception as e:
            print(f"Erreur obtention image page: {e}")
            return None

    def next_page(self):
        if not self.document:
            return False
        if self.current_page < self.total_pages - 1:
            self.update_reading_time()
            self.current_page += 1
            self.current_page_start_time = time.time()
            return True
        return False

    def previous_page(self):
        if not self.document:
            return False
        if self.current_page > 0:
            self.update_reading_time()
            self.current_page -= 1
            self.current_page_start_time = time.time()
            return True
        return False

    def set_zoom(self, zoom):
        self.zoom_level = max(0.5, min(3.0, zoom))

    def update_reading_time(self):
        if self.current_page_start_time:
            duration = time.time() - self.current_page_start_time
            if self.current_page not in self.page_read_times:
                self.page_read_times[self.current_page] = 0
            self.page_read_times[self.current_page] += duration

    def get_reading_statistics(self):
        if not self.reading_start_time:
            return {'total_time': 0, 'pages_read': 0, 'avg_time_per_page': 0, 
                    'current_page': 0, 'total_pages': 0, 'progress': 0}
        total_time = time.time() - self.reading_start_time
        pages_read = len(self.page_read_times)
        avg_time = total_time / pages_read if pages_read > 0 else 0
        progress = (self.current_page + 1) / self.total_pages * 100 if self.total_pages > 0 else 0
        return {'total_time': total_time, 'pages_read': pages_read, 'avg_time_per_page': avg_time,
                'current_page': self.current_page + 1, 'total_pages': self.total_pages, 'progress': progress}

    def close(self):
        if self.document:
            self.update_reading_time()
            self.document.close()
            self.document = None
