
import os
from dotenv import load_dotenv
import requests
import json

def get_ai_response(prompt):
    from dotenv import load_dotenv
    load_dotenv()
    print(f"[DEBUG] get_ai_response appelé")
    # --- Gemini ---
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
    except Exception:
        pass  # Suppression affichage erreur Gemini

    # --- Mistral (toujours tenté si Gemini échoue) ---
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    print(f"[DEBUG][MISTRAL] Clé API lue : {MISTRAL_API_KEY}")
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
        print("[DEBUG][MISTRAL] Tentative d'appel à l'API Mistral...")
        resp = requests.post(MISTRAL_URL, headers=mistral_headers, json=mistral_data, timeout=30)
        print(f"[DEBUG][MISTRAL] Status code: {resp.status_code}")
        print(f"[DEBUG][MISTRAL] Response text: {resp.text[:500]}")
        if resp.status_code == 200:
            result = resp.json()
            text = result["choices"][0]["message"]["content"]
            try:
                return json.loads(text)
            except Exception:
                return text
        else:
            print(f"[DEBUG][MISTRAL] Erreur HTTP: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[DEBUG][MISTRAL] Exception lors de l'appel à l'API : {e}")
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
