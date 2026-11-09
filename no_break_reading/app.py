"""
Interface Streamlit pour No Break Reading
"""

import streamlit as st
import cv2
import numpy as np
import time
import tempfile
import os
from PIL import Image

# Import modules core
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.eye_tracker import EyeTracker
from core.alert_system import AlertSystem
from core.pdf_reader import PDFReader
from core.statistics_manager import StatisticsManager
from config import EYE_TRACKING_CONFIG, ALERT_CONFIG, PDF_CONFIG

def initialize_session_state():
    """Initialise les variables de session Streamlit"""
    if 'eye_tracker' not in st.session_state:
        st.session_state.eye_tracker = EyeTracker(
            ear_threshold=EYE_TRACKING_CONFIG['ear_threshold']
        )

    if 'alert_system' not in st.session_state:
        st.session_state.alert_system = AlertSystem(
            trigger_frames=ALERT_CONFIG['trigger_frames'],
            duration=ALERT_CONFIG['duration'],
            cooldown=ALERT_CONFIG['cooldown']
        )

    if 'pdf_reader' not in st.session_state:
        st.session_state.pdf_reader = PDFReader()

    if 'stats_manager' not in st.session_state:
        st.session_state.stats_manager = StatisticsManager()

    if 'tracking_active' not in st.session_state:
        st.session_state.tracking_active = False

    if 'cap' not in st.session_state:
        st.session_state.cap = None

def render_sidebar():
    """Panneau de contrôle sidebar"""
    st.sidebar.title("⚙️ Paramètres")

    # Section Eye Tracking
    st.sidebar.subheader("👁️ Eye Tracking")
    ear_threshold = st.sidebar.slider(
        "Seuil EAR",
        min_value=0.15,
        max_value=0.30,
        value=0.21,
        step=0.01,
        help="Plus bas = plus sensible à la fermeture des yeux"
    )
    st.session_state.eye_tracker.update_threshold(ear_threshold)

    # Section Alertes
    st.sidebar.subheader("🔔 Alertes")
    sound_enabled = st.sidebar.checkbox("Son activé", value=True)
    if sound_enabled:
        st.session_state.alert_system.enable_sound()
    else:
        st.session_state.alert_system.disable_sound()

    alert_duration = st.sidebar.slider("Durée alerte (s)", 1.0, 5.0, 3.0, 0.5)
    alert_cooldown = st.sidebar.slider("Cooldown (s)", 5.0, 30.0, 10.0, 1.0)
    trigger_frames = st.sidebar.slider("Frames avant alerte", 10, 50, 20, 5)

    st.session_state.alert_system.update_settings(
        duration=alert_duration,
        cooldown=alert_cooldown,
        trigger_frames=trigger_frames
    )

    # Section PDF
    st.sidebar.subheader("📄 Lecture")
    if st.session_state.pdf_reader.document:
        zoom = st.sidebar.slider("Zoom", 1.0, 4.0, 2.0, 0.1)
        st.session_state.pdf_reader.set_zoom(zoom)

    # Bouton Export
    st.sidebar.subheader("💾 Export")
    col1, col2 = st.sidebar.columns(2)

    if col1.button("📊 CSV"):
        export_statistics('csv')

    if col2.button("📄 JSON"):
        export_statistics('json')

    if st.sidebar.button("🔄 Réinitialiser stats"):
        st.session_state.stats_manager.reset()
        st.session_state.eye_tracker.reset_statistics()
        st.sidebar.success("Statistiques réinitialisées!")

def render_eye_tracking_panel():
    """Panneau eye tracking (colonne gauche)"""
    st.subheader("👁️ Eye Tracking")

    # Bouton start/stop
    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button(
            "▶️ Démarrer Tracking" if not st.session_state.tracking_active else "⏸️ Arrêter Tracking",
            use_container_width=True
        ):
            toggle_tracking()

    with col2:
        status_color = "🟢" if st.session_state.tracking_active else "🔴"
        st.write(f"{status_color} {'Actif' if st.session_state.tracking_active else 'Inactif'}")

    # Placeholder pour la webcam
    webcam_placeholder = st.empty()

    # Stats en temps réel
    col_a, col_b, col_c = st.columns(3)
    ear_display = col_a.empty()
    state_display = col_b.empty()
    blinks_display = col_c.empty()

    closed_frames_display = st.empty()
    cooldown_display = st.empty()

    # Mise à jour en temps réel
    if st.session_state.tracking_active:
        update_eye_tracking_display(
            webcam_placeholder,
            ear_display,
            state_display,
            blinks_display,
            closed_frames_display,
            cooldown_display
        )

def render_pdf_viewer():
    """Panneau lecteur PDF (colonne droite)"""
    st.subheader("📖 Lecteur PDF")

    # Upload PDF
    uploaded_file = st.file_uploader("📂 Charger un PDF", type=['pdf'])

    if uploaded_file:
        # Sauvegarder temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        # Charger dans le reader
        if st.session_state.pdf_reader.load_pdf(tmp_path):
            st.success(f"✅ PDF chargé: {uploaded_file.name}")

    # Affichage PDF
    if st.session_state.pdf_reader.document:
        pdf_image = st.session_state.pdf_reader.get_current_page_image()

        if pdf_image is not None:
            # Convertir BGR to RGB si nécessaire
            if len(pdf_image.shape) == 3 and pdf_image.shape[2] == 3:
                st.image(pdf_image, use_container_width=True)

        # Navigation
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("◀️ Précédent", use_container_width=True):
                if st.session_state.pdf_reader.previous_page():
                    st.rerun()

        with col2:
            st.markdown(f"<h3 style='text-align: center;'>Page {st.session_state.pdf_reader.current_page + 1} / {st.session_state.pdf_reader.total_pages}</h3>", 
                       unsafe_allow_html=True)

        with col3:
            if st.button("Suivant ▶️", use_container_width=True):
                if st.session_state.pdf_reader.next_page():
                    st.rerun()

        # Stats de lecture
        reading_stats = st.session_state.pdf_reader.get_reading_statistics()

        st.markdown("---")
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Temps total", f"{reading_stats['total_time']:.0f}s")
        col_r2.metric("Pages visitées", reading_stats['pages_read'])
        col_r3.metric("Progression", f"{reading_stats['progress']:.0f}%")

    else:
        st.info("👆 Chargez un PDF pour commencer la lecture")

def render_statistics_footer():
    """Footer avec statistiques"""
    st.markdown("---")
    st.subheader("📊 Statistiques de session")

    stats = st.session_state.stats_manager.get_summary()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⏱️ Durée", f"{stats['session_duration']:.0f}s")
    col2.metric("👁️ Clignements", stats['total_blinks'])
    col3.metric("🔔 Alertes", stats['total_alerts'])
    col4.metric("⭐ Attention", f"{stats['attention_score']:.0f}%")

def toggle_tracking():
    """Démarre/arrête le tracking"""
    if not st.session_state.tracking_active:
        st.session_state.cap = cv2.VideoCapture(0)
        if st.session_state.cap.isOpened():
            st.session_state.eye_tracker.start()
            st.session_state.tracking_active = True
    else:
        st.session_state.tracking_active = False
        if st.session_state.cap:
            st.session_state.cap.release()
            st.session_state.cap = None
        st.session_state.eye_tracker.stop()

def update_eye_tracking_display(webcam_ph, ear_ph, state_ph, blinks_ph, closed_ph, cooldown_ph):
    """Met à jour l'affichage eye tracking"""

    if st.session_state.cap and st.session_state.cap.isOpened():
        ret, frame = st.session_state.cap.read()

        if ret:
            frame = cv2.flip(frame, 1)

            # Traiter avec eye tracker
            result = st.session_state.eye_tracker.process_frame(frame)

            # Afficher frame (convertir BGR to RGB)
            frame_rgb = cv2.cvtColor(result['frame'], cv2.COLOR_BGR2RGB)
            webcam_ph.image(frame_rgb, use_container_width=True)

            # Afficher stats
            ear_ph.metric("EAR", f"{result['ear_avg']:.3f}")

            state_color = "🟢" if result['eye_state'] == "OUVERT" else "🔴"
            state_ph.metric("État", f"{state_color} {result['eye_state']}")

            blinks_ph.metric("Clignements", result['total_blinks'])
            closed_ph.metric("Frames fermées", result['closed_duration'])

            # Vérifier alerte
            alert_triggered = st.session_state.alert_system.check_and_trigger(
                result['closed_duration']
            )

            if alert_triggered:
                st.warning("⚠️ ALERTE: Yeux fermés détectés! Réveillez-vous! 🔔")

            # Cooldown
            cooldown = st.session_state.alert_system.get_cooldown_remaining()
            cooldown_ph.metric("Cooldown alerte", f"{cooldown:.1f}s")

            # Mettre à jour stats
            stats = st.session_state.eye_tracker.get_statistics()
            st.session_state.stats_manager.update_eye_tracking(stats)
            st.session_state.stats_manager.update_alert(alert_triggered)

            if st.session_state.pdf_reader.document:
                reading_stats = st.session_state.pdf_reader.get_reading_statistics()
                st.session_state.stats_manager.update_reading(reading_stats)

def export_statistics(format_type):
    """Exporte les statistiques"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"no_break_reading_stats_{timestamp}.{format_type}"
    filepath = os.path.join("exports", filename)

    os.makedirs("exports", exist_ok=True)

    if format_type == 'csv':
        success = st.session_state.stats_manager.export_to_csv(filepath)
    else:
        success = st.session_state.stats_manager.export_to_json(filepath)

    if success:
        st.sidebar.success(f"✅ Exporté: {filename}")
    else:
        st.sidebar.error("❌ Erreur lors de l'export")

def main():
    """Point d'entrée principal"""
    st.set_page_config(
        page_title="No Break Reading - Eye Tracking PDF Reader",
        page_icon="👁️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Titre
    st.title("👁️ No Break Reading")
    st.markdown("*Application de lecture PDF avec surveillance oculaire*")

    # Initialisation
    initialize_session_state()

    # Sidebar
    render_sidebar()

    # Layout principal
    col1, col2 = st.columns([1, 2])

    with col1:
        render_eye_tracking_panel()

    with col2:
        render_pdf_viewer()

    # Footer
    render_statistics_footer()

    # Auto-refresh si tracking actif
    if st.session_state.tracking_active:
        time.sleep(0.033)  # ~30 FPS
        st.rerun()

if __name__ == "__main__":
    main()
