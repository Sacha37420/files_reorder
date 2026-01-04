import os
from dotenv import load_dotenv
import requests
import json

def get_ai_response(prompt):
    from dotenv import load_dotenv
    load_dotenv()

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_URL = "https://ai.google.de/v1/chat/completions"  # Remplacer par l'URL réelle de l'API Gemini
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gemini-default",  # Remplacer par le nom réel du modèle
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512
    }

    print(f"[DEBUG] GEMINI_API_KEY: {GEMINI_API_KEY}")
    print(f"[DEBUG] Envoi de la requête à GEMINI_URL: {GEMINI_URL}")
    print("[DEBUG] Envoi de la requête à GEMINI_URL avec les données suivantes :", data)
    print("[DEBUG] En-têtes de la requête Gemini :", headers)

    print("[DEBUG] Appel à get_ai_response avec GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("[DEBUG] GEMINI_API_KEY est vide ou non défini")

    try:
        resp = requests.post(GEMINI_URL, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            candidates = resp.json().get("candidates", [])
            if candidates:
                text = candidates[0]["content"]["parts"][0]["text"]
                try:
                    return json.loads(text)
                except Exception as e:
                    print(f"[DEBUG] Erreur de parsing JSON: {e}")
                    return text
        else:
            print(f"[DEBUG] Erreur HTTP Gemini: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[DEBUG] Exception lors de la requête Gemini: {e}")

    # --- Repli Mistral ---
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
    mistral_headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    mistral_data = {
        "model": "mistral-tiny",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512
    }

    print(f"[DEBUG] MISTRAL_API_KEY: {MISTRAL_API_KEY}")
    print(f"[DEBUG] Envoi de la requête à MISTRAL_URL: {MISTRAL_URL}")
    print("[DEBUG] Envoi de la requête à MISTRAL_URL avec les données suivantes :", mistral_data)
    print("[DEBUG] En-têtes de la requête Mistral :", mistral_headers)

    try:
        resp = requests.post(MISTRAL_URL, headers=mistral_headers, json=mistral_data, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            text = result["choices"][0]["message"]["content"]
            try:
                return json.loads(text)
            except Exception as e:
                print(f"[DEBUG] Erreur de parsing JSON: {e}")
                return text
        else:
            print(f"[DEBUG] Erreur HTTP Mistral: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[DEBUG] Exception lors de la requête Mistral: {e}")

    return {}
