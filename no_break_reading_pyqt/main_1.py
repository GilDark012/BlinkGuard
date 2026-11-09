#!/usr/bin/env python3
"""
No Break Reading - PyQt6 Application
Interface desktop professionnelle avec eye tracking
"""

import sys
import cv2
import numpy as np
import os
from pathlib import Path

from PyQt6.QtWidgets import *
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap, QAction, QFont

# Import modules core
sys.path.insert(0, str(Path(__file__).parent))

from core.eye_tracker import EyeTracker
from core.alert_system import AlertSystem
from core.pdf_reader import PDFReader
from core.statistics_manager import StatisticsManager
from config import EYE_TRACKING_CONFIG, ALERT_CONFIG

class NoBreakReadingApp(QMainWindow):
    """Application principale PyQt6"""

    def __init__(self):
        super().__init__()

        # Modules core
        self.eye_tracker = EyeTracker(ear_threshold=EYE_TRACKING_CONFIG['ear_threshold'])
        self.alert_system = AlertSystem(
            trigger_frames=ALERT_CONFIG['trigger_frames'],
            duration=ALERT_CONFIG['duration'],
            cooldown=ALERT_CONFIG['cooldown']
        )
        self.pdf_reader = PDFReader()
        self.stats_manager = StatisticsManager()

        # État
        self.tracking_active = False
        self.cap = None

        # Setup UI
        self.init_ui()
        self.init_menu()
        self.init_timers()

        self.statusBar().showMessage("Prêt à démarrer 🚀")

    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("No Break Reading - Eye Tracking PDF Reader 👁️")
        self.setGeometry(100, 100, 1400, 900)

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel gauche - Eye Tracking
        left_panel = self.create_eye_tracking_panel()
        left_panel.setMaximumWidth(500)

        # Panel droit - PDF Reader
        right_panel = self.create_pdf_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

    def create_eye_tracking_panel(self):
        """Crée le panneau eye tracking"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Titre
        title = QLabel("👁️ Eye Tracking")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Webcam display
        self.webcam_label = QLabel()
        self.webcam_label.setMinimumSize(450, 340)
        self.webcam_label.setMaximumSize(450, 340)
        self.webcam_label.setStyleSheet("background-color: #2c3e50; border: 3px solid #34495e; border-radius: 10px;")
        self.webcam_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.webcam_label.setText("Webcam inactive\n\nCliquez sur Démarrer")
        layout.addWidget(self.webcam_label)

        # Bouton Start/Stop
        self.start_btn = QPushButton("▶️ Démarrer Eye Tracking")
        self.start_btn.clicked.connect(self.toggle_eye_tracking)
        self.start_btn.setStyleSheet("""
            QPushButton {
                font-size: 14pt; padding: 12px; background-color: #27ae60;
                color: white; border-radius: 8px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        layout.addWidget(self.start_btn)

        # Stats group
        stats_group = QGroupBox("📊 Statistiques")
        stats_layout = QVBoxLayout()

        self.ear_label = QLabel("EAR: --")
        self.state_label = QLabel("État: Inactif")
        self.blinks_label = QLabel("Clignements: 0")
        self.closed_frames_label = QLabel("Frames fermées: 0")

        for label in [self.ear_label, self.state_label, self.blinks_label, self.closed_frames_label]:
            label.setStyleSheet("font-size: 12pt; padding: 5px;")
            stats_layout.addWidget(label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Alert group
        alert_group = QGroupBox("🔔 Alertes")
        alert_layout = QVBoxLayout()

        self.alert_status_label = QLabel("Status: Actives ✅")
        self.cooldown_label = QLabel("Cooldown: 0.0s")

        alert_layout.addWidget(self.alert_status_label)
        alert_layout.addWidget(self.cooldown_label)
        alert_group.setLayout(alert_layout)
        layout.addWidget(alert_group)

        layout.addStretch()
        return panel

    def create_pdf_panel(self):
        """Crée le panneau PDF"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📖 Lecteur PDF")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)

        open_btn = QPushButton("📂 Ouvrir PDF")
        open_btn.clicked.connect(self.open_pdf)
        open_btn.setStyleSheet("font-size: 11pt; padding: 8px 16px; background-color: #3498db; color: white; border-radius: 6px;")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(open_btn)
        layout.addLayout(header_layout)

        # PDF display
        self.pdf_scroll = QScrollArea()
        self.pdf_label = QLabel("Aucun PDF chargé\n\n📂 Cliquez sur 'Ouvrir PDF'")
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_label.setStyleSheet("background-color: white; font-size: 14pt; color: #7f8c8d; padding: 40px;")
        self.pdf_scroll.setWidget(self.pdf_label)
        self.pdf_scroll.setWidgetResizable(True)
        layout.addWidget(self.pdf_scroll)

        # Navigation
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀️ Précédent")
        self.prev_btn.clicked.connect(self.previous_page)
        self.prev_btn.setEnabled(False)

        self.page_label = QLabel("Page: 0 / 0")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton("Suivant ▶️")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_btn)
        layout.addLayout(nav_layout)

        # Stats lecture
        stats_layout = QHBoxLayout()
        self.reading_time_label = QLabel("⏱️ Temps: 0s")
        self.reading_pages_label = QLabel("📄 Pages: 0")
        self.reading_progress_label = QLabel("📊 Progression: 0%")

        for label in [self.reading_time_label, self.reading_pages_label, self.reading_progress_label]:
            stats_layout.addWidget(label)
        layout.addLayout(stats_layout)

        return panel

    def init_menu(self):
        """Initialise la barre de menu"""
        menubar = self.menuBar()

        # Fichier
        file_menu = menubar.addMenu("📁 Fichier")
        open_action = QAction("Ouvrir PDF...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_action)

        file_menu.addSeparator()
        quit_action = QAction("Quitter", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Statistiques
        stats_menu = menubar.addMenu("📊 Statistiques")
        view_stats = QAction("Voir statistiques", self)
        view_stats.triggered.connect(self.show_statistics)
        stats_menu.addAction(view_stats)

        export_csv = QAction("Exporter CSV...", self)
        export_csv.triggered.connect(lambda: self.export_stats('csv'))
        stats_menu.addAction(export_csv)

        export_json = QAction("Exporter JSON...", self)
        export_json.triggered.connect(lambda: self.export_stats('json'))
        stats_menu.addAction(export_json)

        # Aide
        help_menu = menubar.addMenu("❓ Aide")
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_timers(self):
        """Initialise les timers"""
        self.webcam_timer = QTimer()
        self.webcam_timer.timeout.connect(self.update_webcam)

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics)
        self.stats_timer.start(1000)

    def toggle_eye_tracking(self):
        """Démarre/arrête l'eye tracking"""
        if not self.tracking_active:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.eye_tracker.start()
                self.tracking_active = True
                self.start_btn.setText("⏸️ Arrêter")
                self.start_btn.setStyleSheet("font-size: 14pt; padding: 12px; background-color: #e74c3c; color: white; border-radius: 8px;")
                self.webcam_timer.start(33)
                self.statusBar().showMessage("Eye tracking actif 🟢")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible d'ouvrir la webcam!")
        else:
            self.tracking_active = False
            self.start_btn.setText("▶️ Démarrer Eye Tracking")
            self.start_btn.setStyleSheet("font-size: 14pt; padding: 12px; background-color: #27ae60; color: white; border-radius: 8px;")
            self.webcam_timer.stop()
            if self.cap:
                self.cap.release()
            self.eye_tracker.stop()
            self.webcam_label.setText("Webcam inactive")
            self.statusBar().showMessage("Eye tracking arrêté 🔴")

    def update_webcam(self):
        """Mise à jour webcam avec eye tracking - INTÉGRATION COMPLÈTE"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)

                # Eye tracking
                result = self.eye_tracker.process_frame(frame)

                # Afficher frame
                h, w, ch = result['frame'].shape
                qt_image = QImage(result['frame'].data, w, h, w * ch, QImage.Format.Format_BGR888)
                pixmap = QPixmap.fromImage(qt_image).scaled(self.webcam_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
                self.webcam_label.setPixmap(pixmap)

                # Stats
                self.ear_label.setText(f"EAR: {result['ear_avg']:.3f}")
                self.state_label.setText(f"État: {result['eye_state']}")
                stats = self.eye_tracker.get_statistics()
                self.blinks_label.setText(f"Clignements: {stats['total_blinks']}")
                self.closed_frames_label.setText(f"Frames fermées: {result['closed_duration']}")

                # Alertes
                alert = self.alert_system.check_and_trigger(result['closed_duration'])
                if alert:
                    self.statusBar().showMessage("⚠️ ALERTE: RÉVEILLEZ-VOUS! 🔔", 3000)

                cooldown = self.alert_system.get_cooldown_remaining()
                self.cooldown_label.setText(f"Cooldown: {cooldown:.1f}s")

                # Stats
                self.stats_manager.update_eye_tracking(stats)
                self.stats_manager.update_alert(alert)

    def open_pdf(self):
        """Ouvre un PDF"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Ouvrir PDF", "", "PDF Files (*.pdf)")
        if file_path:
            if self.pdf_reader.load_pdf(file_path):
                self.display_page()
                self.prev_btn.setEnabled(True)
                self.next_btn.setEnabled(True)
                self.statusBar().showMessage(f"PDF chargé: {Path(file_path).name}")

    def display_page(self):
        """Affiche la page PDF"""
        if self.pdf_reader.document:
            img = self.pdf_reader.get_current_page_image()
            if img is not None:
                h, w, ch = img.shape
                qt_img = QImage(img.data, w, h, w * ch, QImage.Format.Format_RGB888)
                self.pdf_label.setPixmap(QPixmap.fromImage(qt_img))
                self.page_label.setText(f"Page: {self.pdf_reader.current_page + 1} / {self.pdf_reader.total_pages}")

                stats = self.pdf_reader.get_reading_statistics()
                self.reading_time_label.setText(f"⏱️ Temps: {stats['total_time']:.0f}s")
                self.reading_pages_label.setText(f"📄 Pages: {stats['pages_read']}")
                self.reading_progress_label.setText(f"📊 Progression: {stats['progress']:.0f}%")

    def previous_page(self):
        if self.pdf_reader.previous_page():
            self.display_page()

    def next_page(self):
        if self.pdf_reader.next_page():
            self.display_page()

    def update_statistics(self):
        self.stats_manager.add_data_point()
        if self.pdf_reader.document:
            self.stats_manager.update_reading(self.pdf_reader.get_reading_statistics())

    def export_stats(self, fmt):
        file_path, _ = QFileDialog.getSaveFileName(self, "Exporter", f"stats.{fmt}", f"{fmt.upper()} (*.{fmt})")
        if file_path:
            success = self.stats_manager.export_to_csv(file_path) if fmt == 'csv' else self.stats_manager.export_to_json(file_path)
            if success:
                QMessageBox.information(self, "Succès", f"Stats exportées:\n{file_path}")

    def show_statistics(self):
        summary = self.stats_manager.get_summary()
        msg = f"""
📊 Statistiques de session

⏱️ Durée: {summary['session_duration']:.0f}s
👁️ Clignements: {summary['total_blinks']}
🔔 Alertes: {summary['total_alerts']}
📄 Pages: {summary['pages_read']}
⭐ Attention: {summary['attention_score']:.0f}/100
📖 Vitesse: {summary['reading_speed']:.1f} pages/h
        """
        QMessageBox.information(self, "Statistiques", msg)

    def show_about(self):
        QMessageBox.about(self, "À propos", """
<h2>No Break Reading</h2>
<p><b>Version:</b> 1.0 PyQt6</p>
<p>Application de lecture PDF avec eye tracking</p>
<p>Développé avec ❤️ pour les étudiants en IA</p>
        """)

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        self.eye_tracker.stop()
        self.alert_system.shutdown()
        if self.pdf_reader.document:
            self.pdf_reader.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = NoBreakReadingApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
