# No Break Reading - Eye Tracking PDF Reader

Application de lecture PDF avec surveillance oculaire pour éviter l'endormissement pendant la lecture.

## 🎯 Fonctionnalités

- ✅ **Eye Tracking en temps réel** : Détection de l'ouverture/fermeture des yeux via webcam
- ✅ **Alertes sonores** : Bip sonore de 3 secondes quand vous fermez les yeux trop longtemps
- ✅ **Lecteur PDF intégré** : Navigation facile dans vos documents
- ✅ **Statistiques détaillées** : Clignements, temps de lecture, score d'attention
- ✅ **Export de données** : CSV et JSON pour analyse ultérieure
- ✅ **Paramètres ajustables** : Personnalisez les seuils selon vos besoins

## 📋 Prérequis

- Python 3.8 ou supérieur
- Webcam fonctionnelle
- Système audio pour les alertes

## 🚀 Installation

1. **Extraire le fichier ZIP**

2. **Installer les dépendances**
```bash
cd no_break_reading
pip install -r requirements.txt
```

3. **Lancer l'application**
```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

## 📖 Utilisation

### Démarrage rapide

1. **Charger un PDF** : Utilisez le bouton "📂 Charger un PDF" dans la section droite
2. **Démarrer le tracking** : Cliquez sur "▶️ Démarrer Tracking" dans la section gauche
3. **Ajuster les paramètres** : Utilisez la sidebar pour personnaliser les seuils
4. **Lire votre document** : L'application vous alertera si vous fermez les yeux

### Paramètres disponibles

#### Eye Tracking
- **Seuil EAR** (0.15-0.30) : Plus bas = plus sensible à la fermeture des yeux
  - Recommandé : 0.21
  - Si trop d'alertes : augmenter à 0.23-0.25
  - Si pas assez d'alertes : diminuer à 0.18-0.20

#### Alertes
- **Son activé** : Active/désactive les alertes sonores
- **Durée alerte** (1-5s) : Durée du bip sonore
- **Cooldown** (5-30s) : Temps d'attente avant une nouvelle alerte
- **Frames avant alerte** (10-50) : Nombre de frames yeux fermés avant déclenchement

#### Lecture PDF
- **Zoom** (1.0-4.0) : Niveau de zoom du PDF
- Navigation avec les boutons ◀️ Précédent / Suivant ▶️

### Export des statistiques

Cliquez sur les boutons dans la sidebar :
- **📊 CSV** : Exporte les données brutes pour Excel/Google Sheets
- **📄 JSON** : Exporte au format JSON pour analyse programmatique

Les fichiers sont sauvegardés dans le dossier `exports/`

## 📊 Métriques

### Eye Tracking
- **EAR** : Eye Aspect Ratio (0.0-0.4 typiquement)
- **État** : OUVERT 🟢 / FERME 🔴
- **Clignements** : Nombre total de clignements détectés
- **Frames fermées** : Nombre de frames consécutives avec yeux fermés

### Lecture
- **Temps total** : Durée totale de la session
- **Pages visitées** : Nombre de pages différentes consultées
- **Progression** : Pourcentage du document lu

### Session
- **Score d'attention** : 0-100% (diminue avec les alertes)
- **Alertes** : Nombre total d'alertes déclenchées

## 🔧 Résolution de problèmes

### La webcam ne fonctionne pas
- Vérifiez que votre webcam est connectée et autorisée
- Essayez de fermer d'autres applications utilisant la webcam
- Sur Linux : installez `v4l-utils`

### Les alertes ne se déclenchent pas
- Diminuez le seuil EAR dans la sidebar
- Vérifiez que le son est activé
- Assurez-vous que votre visage est bien détecté (rectangles verts sur les yeux)

### Le PDF ne s'affiche pas
- Vérifiez que le fichier est un PDF valide
- Essayez de réduire le zoom si le document est très volumineux

### Performance lente
- Fermez d'autres applications
- Réduisez la résolution de la webcam dans `config.py`
- Désactivez le tracking quand vous ne lisez pas

## 🏗️ Architecture

```
no_break_reading/
├── app.py                      # Application Streamlit principale
├── config.py                   # Configuration globale
├── requirements.txt            # Dépendances Python
├── core/
│   ├── eye_tracker.py         # Module eye tracking
│   ├── alert_system.py        # Système d'alertes sonores
│   ├── pdf_reader.py          # Lecteur PDF
│   └── statistics_manager.py  # Gestion des statistiques
└── exports/                    # Dossier pour les exports
```

## 🎓 Développé pour

Ce projet a été développé comme outil d'aide à la lecture pour étudiants et professionnels qui ont besoin de rester concentrés pendant de longues sessions de lecture.

## 📝 License

Projet étudiant - Usage libre

## 🤝 Contribution

Développé avec ❤️ pour améliorer la concentration en lecture !

---

**Bon courage pour vos lectures ! 📚👁️**
