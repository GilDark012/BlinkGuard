#!/usr/bin/env python3
"""
No Break Reading - PyQt6 Application
Interface desktop avec zoom PDF fonctionnel
"""

import sys
from pathlib import Path

import cv2

from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSlider, QSplitter, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap, QAction, QFont, QKeySequence, QShortcut

# Import modules core
sys.path.insert(0, str(Path(__file__).parent))

from core.eye_tracker import EyeTracker, EyeTrackerError, STATE_OPEN, STATE_NO_FACE
from core.alert_system import AlertSystem, REASON_FACE_LOST
from core.pdf_reader import PDFReader
from core.statistics_manager import StatisticsManager
from config import EYE_TRACKING_CONFIG, ALERT_CONFIG, PDF_CONFIG, STATS_CONFIG

class NoBreakReadingApp(QMainWindow):
    """Application principale PyQt6"""

    def __init__(self):
        super().__init__()

        # Modules core
        self.eye_tracker = EyeTracker(
            ear_threshold=EYE_TRACKING_CONFIG['ear_threshold'],
            min_detection_confidence=EYE_TRACKING_CONFIG['min_detection_confidence'],
            min_tracking_confidence=EYE_TRACKING_CONFIG['min_tracking_confidence'],
        )
        self.alert_system = AlertSystem(
            trigger_seconds=ALERT_CONFIG['trigger_seconds'],
            duration=ALERT_CONFIG['duration'],
            cooldown=ALERT_CONFIG['cooldown'],
            reset_after=ALERT_CONFIG['reset_after'],
            face_lost_alert=ALERT_CONFIG['face_lost_alert'],
            face_lost_seconds=ALERT_CONFIG['face_lost_seconds'],
            frequency=ALERT_CONFIG['frequency'],
            volume_increase=ALERT_CONFIG['volume_increase'],
            max_volume_multiplier=ALERT_CONFIG['max_volume_multiplier'],
            sound_enabled=ALERT_CONFIG['enabled'],
        )
        self.pdf_reader = PDFReader()
        self.stats_manager = StatisticsManager()

        # État
        self.tracking_active = False
        self.cap = None
        self.read_failures = 0

        # Setup UI
        self.init_ui()
        self.init_menu()
        self.init_timers()
        self.init_shortcuts()

        if not self.alert_system.audio_available:
            self.alert_status_label.setText("Status: Son indisponible ⚠️ (alerte visuelle seulement)")
        self.statusBar().showMessage("Prêt à démarrer 🚀")

    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Wake Reader - Eye Tracking PDF Reader 👁️📚")
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
        self.closed_frames_label = QLabel("Yeux fermés depuis: 0.0s")

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
        self.alert_intensity_label = QLabel("Intensité: 100%")

        alert_layout.addWidget(self.alert_status_label)
        alert_layout.addWidget(self.cooldown_label)
        alert_layout.addWidget(self.alert_intensity_label)
        alert_group.setLayout(alert_layout)
        layout.addWidget(alert_group)

        layout.addStretch()
        return panel

    def create_pdf_panel(self):
        """Crée le panneau PDF avec contrôle de zoom"""
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
        open_btn.setStyleSheet("""
            QPushButton {
                font-size: 11pt; padding: 8px 16px; background-color: #3498db;
                color: white; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5dade2; }
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(open_btn)
        layout.addLayout(header_layout)

        # ✅ CONTRÔLE DE ZOOM
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("🔍 Zoom:")
        zoom_label.setStyleSheet("font-weight: bold; font-size: 11pt;")

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(int(PDF_CONFIG['min_zoom'] * 100))
        self.zoom_slider.setMaximum(int(PDF_CONFIG['max_zoom'] * 100))
        self.zoom_slider.setValue(int(PDF_CONFIG['default_zoom'] * 100))
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(25)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        self.zoom_slider.setEnabled(False)

        self.zoom_value_label = QLabel(f"{PDF_CONFIG['default_zoom']:.1f}x")
        self.zoom_value_label.setStyleSheet("font-weight: bold; font-size: 11pt; min-width: 50px;")

        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_value_label)
        layout.addLayout(zoom_layout)

        # PDF display avec scroll
        self.pdf_scroll = QScrollArea()
        self.pdf_scroll.setWidgetResizable(True)
        self.pdf_scroll.setStyleSheet("border: 2px solid #bdc3c7; border-radius: 8px; background-color: #ecf0f1;")

        self.pdf_label = QLabel("Aucun PDF chargé\n\n📂 Cliquez sur 'Ouvrir PDF'")
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_label.setStyleSheet("""
            background-color: white; font-size: 14pt; color: #7f8c8d; padding: 40px;
        """)

        self.pdf_scroll.setWidget(self.pdf_label)
        layout.addWidget(self.pdf_scroll)

        # Navigation
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀️ Précédent")
        self.prev_btn.clicked.connect(self.previous_page)
        self.prev_btn.setEnabled(False)

        self.page_label = QLabel("Page: 0 / 0")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("font-size: 12pt; font-weight: bold;")

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
            label.setStyleSheet("font-size: 10pt; padding: 5px;")
            stats_layout.addWidget(label)
        layout.addLayout(stats_layout)

        return panel

    def on_zoom_changed(self, value):
        """Appelé quand le slider de zoom change"""
        zoom = value / 100.0
        self.zoom_value_label.setText(f"{zoom:.1f}x")
        self.pdf_reader.set_zoom(zoom)
        # Re-rendu différé : évite de recalculer la page à chaque cran du slider
        if self.pdf_reader.document:
            self.zoom_timer.start(PDF_CONFIG['zoom_debounce_ms'])

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
        view_stats.setShortcut("Ctrl+S")
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
        self.stats_timer.start(int(STATS_CONFIG['data_point_interval'] * 1000))

        self.zoom_timer = QTimer()
        self.zoom_timer.setSingleShot(True)
        self.zoom_timer.timeout.connect(self.display_page)

    def init_shortcuts(self):
        """Navigation clavier dans le PDF"""
        for key in (Qt.Key.Key_Right, Qt.Key.Key_PageDown):
            QShortcut(QKeySequence(key), self, activated=self.next_page)
        for key in (Qt.Key.Key_Left, Qt.Key.Key_PageUp):
            QShortcut(QKeySequence(key), self, activated=self.previous_page)

    def _set_start_button(self, running):
        color, hover = ("#e74c3c", "#ec7063") if running else ("#27ae60", "#2ecc71")
        self.start_btn.setText("⏸️ Arrêter" if running else "▶️ Démarrer Eye Tracking")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 14pt; padding: 12px; background-color: {color};
                color: white; border-radius: 8px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
        """)

    def toggle_eye_tracking(self):
        """Démarre/arrête l'eye tracking"""
        if self.tracking_active:
            self.stop_eye_tracking()
        else:
            self.start_eye_tracking()

    def start_eye_tracking(self):
        self.cap = cv2.VideoCapture(EYE_TRACKING_CONFIG['webcam_index'])
        if not self.cap.isOpened():
            self._release_camera()
            QMessageBox.warning(self, "Erreur", "Impossible d'ouvrir la webcam !\n"
                                "Vérifiez qu'elle est branchée et qu'aucune autre application ne l'utilise.")
            return
        try:
            self.eye_tracker.start()
        except EyeTrackerError as e:
            self._release_camera()
            QMessageBox.critical(self, "Eye tracking indisponible", str(e))
            return

        self.alert_system.reset()
        self.read_failures = 0
        self.tracking_active = True
        self._set_start_button(running=True)
        self.webcam_timer.start(EYE_TRACKING_CONFIG['frame_interval_ms'])
        self.statusBar().showMessage("Eye tracking actif 🟢")

    def stop_eye_tracking(self, message="Eye tracking arrêté 🔴"):
        self.tracking_active = False
        self.webcam_timer.stop()
        self._release_camera()
        self.eye_tracker.stop()
        self.alert_system.reset()
        self._set_start_button(running=False)
        self.webcam_label.clear()
        self.webcam_label.setText("Webcam inactive")
        self.statusBar().showMessage(message)

    def _release_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def update_webcam(self):
        """Mise à jour webcam avec eye tracking"""
        if not (self.cap and self.cap.isOpened()):
            return
        ret, frame = self.cap.read()
        if not ret:
            self.read_failures += 1
            if self.read_failures >= EYE_TRACKING_CONFIG['max_read_failures']:
                self.stop_eye_tracking("Webcam déconnectée ⚠️")
                QMessageBox.warning(self, "Webcam", "La webcam ne répond plus : eye tracking arrêté.")
            return
        self.read_failures = 0

        result = self.eye_tracker.process_frame(cv2.flip(frame, 1))

        # Afficher frame
        img = result['frame']
        h, w, ch = img.shape
        qt_image = QImage(img.data, w, h, w * ch, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_image).scaled(
            self.webcam_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.webcam_label.setPixmap(pixmap)

        # Stats
        state = result['eye_state']
        self.ear_label.setText(f"EAR: {result['ear_avg']:.3f}" if result['face_detected'] else "EAR: --")
        if state == STATE_OPEN:
            icon, color = "🟢", "#27ae60"
        elif state == STATE_NO_FACE:
            icon, color = "🟠", "#e67e22"
        else:
            icon, color = "🔴", "#e74c3c"
        self.state_label.setText(f"État: {icon} {state}")
        self.state_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12pt; padding: 5px;")

        stats = self.eye_tracker.get_statistics()
        self.blinks_label.setText(f"Clignements: {stats['total_blinks']}")
        self.closed_frames_label.setText(f"Yeux fermés depuis: {result['closed_seconds']:.1f}s")

        # Alertes avec intensité progressive
        alert = self.alert_system.check_and_trigger(
            result['closed_seconds'], result['face_missing_seconds']
        )
        if alert:
            intensity = int(self.alert_system.get_alert_intensity() * 100)
            count = self.alert_system.get_alert_count()
            why = "Visage absent" if self.alert_system.last_reason == REASON_FACE_LOST else "Yeux fermés"
            self.statusBar().showMessage(f"⚠️ ALERTE #{count} ({why}) - Intensité: {intensity}%! 🔔", 5000)

        cooldown = self.alert_system.get_cooldown_remaining()
        self.cooldown_label.setText(f"Prochaine alerte possible dans: {cooldown:.1f}s")
        self.alert_intensity_label.setText(
            f"Intensité: {int(self.alert_system.get_alert_intensity() * 100)}%"
        )

        self.stats_manager.update_eye_tracking(stats, eye_state=state)
        self.stats_manager.update_alert(alert, self.alert_system.last_reason if alert else None)

    def open_pdf(self):
        """Ouvre un PDF"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Ouvrir PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return
        if not self.pdf_reader.load_pdf(file_path):
            QMessageBox.warning(self, "PDF", f"Impossible d'ouvrir ce PDF :\n{self.pdf_reader.last_error}")
            return
        self.display_page()
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.zoom_slider.setEnabled(True)
        self.statusBar().showMessage(f"PDF chargé: {Path(file_path).name}")

    def display_page(self):
        """Affiche la page PDF avec le zoom actuel"""
        if self.pdf_reader.document:
            # Obtenir l'image avec le zoom actuel
            img = self.pdf_reader.get_current_page_image()

            if img is not None:
                h, w, ch = img.shape
                qt_img = QImage(img.data, w, h, w * ch, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_img)

                # Afficher le pixmap sans redimensionnement supplémentaire
                # Le scroll permet de naviguer si trop grand
                self.pdf_label.setPixmap(pixmap)
                self.pdf_label.setScaledContents(False)
                self.pdf_label.adjustSize()

                self.page_label.setText(
                    f"Page: {self.pdf_reader.current_page + 1} / {self.pdf_reader.total_pages}"
                )

                # Stats
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
        if self.pdf_reader.document:
            stats = self.pdf_reader.get_reading_statistics()
            self.stats_manager.update_reading(stats)
            self.reading_time_label.setText(f"⏱️ Temps: {stats['total_time']:.0f}s")
        if self.tracking_active:
            self.stats_manager.add_data_point()

    def export_stats(self, fmt):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter", f"stats.{fmt}", f"{fmt.upper()} (*.{fmt})"
        )
        if not file_path:
            return
        try:
            if fmt == 'csv':
                self.stats_manager.export_to_csv(file_path)
            else:
                self.stats_manager.export_to_json(file_path)
        except OSError as e:
            QMessageBox.warning(self, "Export", f"Échec de l'export :\n{e}")
            return
        QMessageBox.information(self, "Succès", f"Stats exportées:\n{file_path}")

    def show_statistics(self):
        summary = self.stats_manager.get_summary()
        intensity = int(self.alert_system.get_alert_intensity() * 100)
        alert_count = self.alert_system.get_alert_count()

        msg = f"""
📊 Statistiques de session

⏱️ Durée: {summary['session_duration']:.0f}s
👁️ Clignements: {summary['total_blinks']}
🔔 Alertes: {summary['total_alerts']} (#{alert_count} actuel)
📢 Intensité: {intensity}%
📄 Pages: {summary['pages_read']}
⭐ Attention: {summary['attention_score']:.0f}/100
📖 Vitesse: {summary['reading_speed']:.1f} pages/h
        """
        QMessageBox.information(self, "Statistiques", msg)

    def show_about(self):
        QMessageBox.about(self, "À propos", """
<h2>Wake Reader</h2>
<p><b>Version:</b> 2.0 PyQt6 (avec alertes progressives)</p>
<p>Application de lecture PDF avec eye tracking</p>
<p><b>Nouvelles fonctionnalités:</b></p>
<ul>
<li>✅ Slider de zoom fonctionnel (0.5x - 3.0x)</li>
<li>✅ Alertes progressives (+20% par alerte)</li>
<li>✅ Affichage PDF optimisé avec scroll</li>
<li>✅ Intensité affichée en temps réel</li>
</ul>
<p>Développé avec ❤️ pour les étudiants en IA</p>
        """)

    def closeEvent(self, event):
        for timer in (self.webcam_timer, self.stats_timer, self.zoom_timer):
            timer.stop()
        self._release_camera()
        self.eye_tracker.stop()
        self.alert_system.shutdown()
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
