#!/bin/bash
# Script pour lancer l'application Tkinter sous Linux

# Aller dans le dossier du script
cd "$(dirname "$0")"

# Activer un éventuel environnement virtuel (décommentez si besoin)
# source venv/bin/activate

# Lancer l'application principale
python3 src/gui/app.py
