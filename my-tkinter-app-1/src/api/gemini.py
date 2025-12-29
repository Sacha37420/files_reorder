
import os
from dotenv import load_dotenv
import requests
import json

def get_ai_response(prompt):
    """
    Appelle d'abord Gemini (Google AI Studio). Si échec, tente Mistral.
    Retourne le mapping fichier -> sujet (dict) ou une chaîne JSON.
    """
    # Charger les variables d'environnement depuis .env
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        resp = requests.post(GEMINI_URL, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            candidates = resp.json().get("candidates", [])
            if candidates:
                text = candidates[0]["content"]["parts"][0]["text"]
                try:
                    return json.loads(text)
                except Exception:
                    return text
        # else: pass  # Suppression affichage erreur Gemini
    except Exception:
        pass  # Suppression affichage erreur Gemini

    # --- Mistral (HuggingFace Inference API ou autre) ---
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"  # Adapter si besoin
    mistral_headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    mistral_data = {
        "model": "mistral-tiny",  # Adapter selon le modèle
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512
    }
    try:
        resp = requests.post(MISTRAL_URL, headers=mistral_headers, json=mistral_data, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            text = result["choices"][0]["message"]["content"]
            try:
                return json.loads(text)
            except Exception:
                return text
        # else: pass  # Suppression affichage erreur Mistral
    except Exception:
        pass  # Suppression affichage erreur Mistral

    return {}
