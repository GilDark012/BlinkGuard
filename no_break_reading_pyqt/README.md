# No Break Reading - PyQt6 Desktop Application

Application desktop professionnelle de lecture PDF avec surveillance oculaire.

## 🎯 Fonctionnalités

- ✅ **Interface PyQt6 moderne** : Application desktop native multi-plateforme
- ✅ **Eye Tracking temps réel** : Détection ouverture/fermeture des yeux (30 FPS)
- ✅ **Alertes sonores progressives** : son de 5s, puis 10s d'attente ; chaque alerte suivante est 20% plus forte
- ✅ **Alerte « visage absent »** : si la tête tombe et que le visage sort du champ pendant 5s
- ✅ **Lecteur PDF intégré** : Navigation (boutons ou flèches / PageUp / PageDown), zoom 50–300%, statistiques
- ✅ **Export CSV/JSON** : Statistiques détaillées
- ✅ **Menu complet** : Raccourcis clavier, fenêtre statistiques

## 📋 Prérequis

- Python 3.9 – 3.12 (MediaPipe ne supporte pas encore les versions plus récentes)
- Webcam
- Système audio

## 🚀 Installation

```bash
cd no_break_reading_pyqt

# 1. Créer un environnement virtuel Python 3.11 dans un chemin SANS accents
#    (MediaPipe n'arrive pas à charger ses modèles si le chemin contient é, è...)
py -3.11 -m venv C:\venvs\blinkguard          # Windows
C:\venvs\blinkguard\Scripts\activate

# 2. Installer les dépendances (versions figées et compatibles)
pip install -r requirements.txt

# 3. Lancer l'application
python main.py
```

> ⚠️ Utilisez un environnement dédié : un `protobuf` récent installé par d'autres
> paquets (Streamlit, TensorBoard...) fait planter MediaPipe 0.10.x.

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
- `→` / `PageDown` : Page suivante
- `←` / `PageUp` : Page précédente

### Paramètres ajustables

Pour l'instant, les réglages se font dans `config.py` (un écran de réglages est prévu) :
- **`ear_threshold`** : sensibilité de détection des yeux fermés
- **`trigger_seconds`** : yeux fermés depuis combien de secondes avant l'alerte
- **`duration`** / **`cooldown`** : durée du son et attente avant la relance
- **`face_lost_alert`** / **`face_lost_seconds`** : alerte quand le visage disparaît
- **`webcam_index`** : choix de la caméra

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

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
- **Yeux fermés depuis** : durée en secondes
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
