# No Break Reading - PyQt6 Desktop Application

Application desktop professionnelle de lecture PDF avec surveillance oculaire.

## 🎯 Fonctionnalités

- ✅ **Interface PyQt6 moderne** : Application desktop native multi-plateforme
- ✅ **Eye Tracking temps réel** : Détection ouverture/fermeture des yeux (30 FPS)
- ✅ **Alertes sonores** : Bip de 3s + cooldown 10s
- ✅ **Lecteur PDF intégré** : Navigation, zoom, statistiques
- ✅ **Dialogs de configuration** : Paramètres EAR, alertes personnalisables
- ✅ **Export CSV/JSON** : Statistiques détaillées
- ✅ **Menu complet** : Raccourcis clavier, fenêtre statistiques

## 📋 Prérequis

- Python 3.8+
- Webcam
- Système audio

## 🚀 Installation

```bash
# 1. Extraire le ZIP
unzip no_break_reading_pyqt.zip
cd no_break_reading_pyqt

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
python main.py
```

## 📖 Utilisation

### Interface

L'application se divise en 2 panneaux :

**Panel gauche - Eye Tracking**
- Webcam avec annotations en temps réel
- Bouton Démarrer/Arrêter
- Statistiques : EAR, état yeux, clignements
- Status des alertes et cooldown

**Panel droit - Lecteur PDF**
- Zone d'affichage du document
- Navigation : Précédent / Suivant
- Statistiques de lecture

### Menu

**📁 Fichier**
- Ouvrir PDF... (Ctrl+O)
- Quitter (Ctrl+Q)

**📊 Statistiques**
- Voir statistiques (Ctrl+S)
- Exporter CSV...
- Exporter JSON...

**❓ Aide**
- À propos

### Raccourcis clavier

- `Ctrl+O` : Ouvrir PDF
- `Ctrl+S` : Voir statistiques
- `Ctrl+Q` : Quitter

### Paramètres ajustables

Via le menu "Paramètres" :
- **Seuil EAR** : Sensibilité détection yeux fermés
- **Durée alerte** : 1-10 secondes
- **Cooldown** : 5-60 secondes
- **Frames déclenchement** : 10-100 frames
- **Activer/désactiver le son**

## 🔧 Résolution de problèmes

### Webcam non détectée
```bash
# Linux : vérifier les permissions
sudo chmod 666 /dev/video0

# Test webcam
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Erreur PyQt6
```bash
# Réinstaller PyQt6
pip uninstall PyQt6
pip install PyQt6
```

### Pas de son
```bash
# Vérifier pygame
python -c "import pygame; pygame.mixer.init(); print('OK')"
```

## 🏗️ Architecture

```
no_break_reading_pyqt/
├── main.py                 # Application PyQt6 principale
├── config.py               # Configuration
├── requirements.txt        # Dépendances
├── core/                   # Modules métier
│   ├── eye_tracker.py     # Eye tracking
│   ├── alert_system.py    # Alertes sonores
│   ├── pdf_reader.py      # Lecteur PDF
│   └── statistics_manager.py  # Statistiques
└── exports/               # Dossier pour exports
```

## 🎨 Avantages PyQt6 vs Streamlit

| Caractéristique | PyQt6 | Streamlit |
|----------------|-------|-----------|
| Type | Application desktop native | Application web |
| Performance | Meilleure (native) | Bonne (web) |
| Interface | Personnalisable à 100% | Templates prédéfinis |
| Distribution | Exécutable standalone | Serveur web requis |
| Offline | ✅ Complet | ❌ Serveur nécessaire |
| Dialogs | ✅ Natifs | ⚠️ Limitées |
| Threading | ✅ Qt Threads | ⚠️ Complexe |
| Menu/Shortcuts | ✅ Complets | ❌ Aucun |

## 📊 Métriques disponibles

- **EAR** (Eye Aspect Ratio) : 0.0-0.4
- **État yeux** : OUVERT 🟢 / FERME 🔴
- **Clignements** : Compteur total
- **Frames fermées** : Nombre consécutif
- **Temps lecture** : Par session
- **Pages visitées** : Nombre
- **Score attention** : 0-100%
- **Vitesse lecture** : Pages/heure

## 💡 Conseils d'utilisation

1. **Calibration initiale** : Ajustez le seuil EAR selon votre morphologie
2. **Éclairage** : Préférez un éclairage frontal homogène
3. **Distance** : Placez-vous à 40-60cm de la webcam
4. **Lunettes** : Compatibles, mais ajustez le seuil si nécessaire
5. **Export régulier** : Sauvegardez vos stats pour analyse

## 🔐 Confidentialité

- Aucune donnée n'est envoyée en ligne
- Traitement 100% local
- Les vidéos ne sont jamais enregistrées
- Exports en local uniquement

## 🤝 Support

Application développée pour projet étudiant en IA.

**Bon courage pour vos lectures ! 📚👁️**
