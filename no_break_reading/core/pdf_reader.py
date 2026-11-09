"""
Module de lecture et gestion de PDF
"""

import fitz  # PyMuPDF
import numpy as np
import time
from PIL import Image

class PDFReader:
    """Gère le chargement et la navigation dans les PDFs"""

    def __init__(self):
        self.document = None
        self.current_page = 0
        self.total_pages = 0
        self.file_path = None
        self.zoom_level = 2.0
        self.auto_scroll_enabled = False
        self.scroll_speed = 5

        self.reading_start_time = None
        self.page_read_times = {}
        self.current_page_start_time = None

    def load_pdf(self, file_path):
        """
        Charge un fichier PDF

        Returns:
            bool: True si succès
        """
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
        """
        Retourne l'image de la page courante

        Returns:
            np.ndarray: Image RGB
        """
        if not self.document:
            return None

        if zoom is None:
            zoom = self.zoom_level

        try:
            page = self.document[self.current_page]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Convertir en numpy array RGB
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            return img
        except Exception as e:
            print(f"Erreur obtention image page: {e}")
            return None

    def get_current_page_text(self):
        """Extrait le texte de la page courante"""
        if not self.document:
            return ""

        try:
            page = self.document[self.current_page]
            return page.get_text()
        except Exception as e:
            print(f"Erreur extraction texte: {e}")
            return ""

    def next_page(self):
        """Passe à la page suivante"""
        if not self.document:
            return False

        if self.current_page < self.total_pages - 1:
            self.update_reading_time()
            self.current_page += 1
            self.current_page_start_time = time.time()
            return True
        return False

    def previous_page(self):
        """Revient à la page précédente"""
        if not self.document:
            return False

        if self.current_page > 0:
            self.update_reading_time()
            self.current_page -= 1
            self.current_page_start_time = time.time()
            return True
        return False

    def go_to_page(self, page_number):
        """Va à une page spécifique (1-indexed)"""
        if not self.document:
            return False

        page_idx = page_number - 1
        if 0 <= page_idx < self.total_pages:
            self.update_reading_time()
            self.current_page = page_idx
            self.current_page_start_time = time.time()
            return True
        return False

    def enable_auto_scroll(self, eye_tracking_data):
        """Active le défilement automatique (à implémenter selon besoins)"""
        self.auto_scroll_enabled = True

    def disable_auto_scroll(self):
        """Désactive le défilement automatique"""
        self.auto_scroll_enabled = False

    def update_reading_time(self):
        """Met à jour le temps de lecture de la page courante"""
        if self.current_page_start_time:
            duration = time.time() - self.current_page_start_time
            if self.current_page not in self.page_read_times:
                self.page_read_times[self.current_page] = 0
            self.page_read_times[self.current_page] += duration

    def get_reading_statistics(self):
        """Retourne les statistiques de lecture"""
        if not self.reading_start_time:
            return {
                'total_time': 0,
                'pages_read': 0,
                'avg_time_per_page': 0,
                'current_page': 0,
                'total_pages': 0,
                'progress': 0
            }

        total_time = time.time() - self.reading_start_time
        pages_read = len(self.page_read_times)
        avg_time = total_time / pages_read if pages_read > 0 else 0
        progress = (self.current_page + 1) / self.total_pages * 100 if self.total_pages > 0 else 0

        return {
            'total_time': total_time,
            'pages_read': pages_read,
            'avg_time_per_page': avg_time,
            'current_page': self.current_page + 1,
            'total_pages': self.total_pages,
            'progress': progress
        }

    def close(self):
        """Ferme le document"""
        if self.document:
            self.update_reading_time()
            self.document.close()
            self.document = None

    def set_zoom(self, zoom):
        """Définit le niveau de zoom"""
        self.zoom_level = max(1.0, min(4.0, zoom))
