import os
import json
import requests

class GeminiValidator:
    def propose_global_organization(self, file_theme_dict):
        """
        Envoie à l'IA la liste complète des fichiers, thèmes et sous-thèmes pour obtenir une organisation globale hiérarchique.
        """
        try:
            from api.gemini import get_ai_response
        except ImportError:
            from ..api.gemini import get_ai_response

        prompt = (
            "Voici la liste des fichiers, leur thème principal et leur sous-thème proposé :\n"
        )
        for filename, info in file_theme_dict.items():
            if isinstance(info, dict):
                theme = info.get('theme', '')
                sous_theme = info.get('sous_theme', '')
                prompt += f"- {filename} : Thème = {theme} ; Sous-thème = {sous_theme}\n"
            else:
                prompt += f"- {filename} : {info}\n"
        prompt += (
            "\n1. Propose une organisation globale hiérarchique (par exemple, structure de dossiers ou regroupements thématiques et sous-thématiques) "
            "sous forme de dictionnaire JSON imbriqué où chaque clé de premier niveau est un thème, chaque clé de second niveau est un sous-thème (ou '' si non pertinent), et la valeur est la liste des fichiers correspondants.\n"
            "Exemple :\n"
            "{\n  'Factures': { 'EDF': ['facture1.pdf', 'facture2.pdf'], 'GDF': ['facture3.pdf'] },\n  'Cours': { '': ['cours1.docx', 'cours2.pdf'] }\n}\n"
            "\n2. Propose une nomenclature adaptée pour chaque fichier (nommage clair, homogène, sans caractères spéciaux inutiles, extension préservée). "
            "Retourne un dictionnaire JSON où chaque clé est le nom d'origine et la valeur est le nom suggéré.\n"
            "Exemple :\n"
            "{\n  'facture1.pdf': 'Facture_EDF_2023-01.pdf',\n  'cours1.docx': 'Cours_Mathématiques_2022.docx'\n}\n"
        )
        if self.debug:
            print(f"\n--- Prompt organisation globale ---\n{prompt}\n---")
        response = get_ai_response(prompt)
        # On suppose que la réponse contient un JSON avec l'organisation globale
        if isinstance(response, dict):
            return response
        elif isinstance(response, str):
            try:
                return json.loads(response)
            except Exception:
                return {}
        return {}
    def __init__(self, debug=False):
        self.debug = debug
        self.previous_suggestions = {}  # Historique des suggestions (nom_fichier: {theme, sous_theme})
        try:
            self.schema = self.load_schema()
        except Exception:
            self.schema = None

    def load_schema(self):
        with open('src/data/schema.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    def suggest_schema(self, files, batch_size=1, max_files=10):
        # files est une liste de dicts avec name, path, date, excerpt
        # On traite par lots pour éviter de dépasser la limite de tokens
        import math
        try:
            from api.gemini import get_ai_response
        except ImportError:
            from ..api.gemini import get_ai_response

        all_results = {}
        n = len(files)
        import re
        for batch_num, i in enumerate(range(0, n, batch_size), 1):
            batch = files[i:i+batch_size]
            # Prépare la liste des thèmes/sous-thèmes déjà proposés
            existing_themes = set()
            existing_subthemes = set()
            for v in self.previous_suggestions.values():
                if isinstance(v, dict):
                    theme = v.get('theme', '')
                    sous_theme = v.get('sous_theme', '')
                    if theme:
                        existing_themes.add(theme)
                    if sous_theme:
                        existing_subthemes.add(sous_theme)
            prompt = (
                f"Batch {batch_num} (ID unique {batch_num}) :\n"
                "Voici une liste de fichiers avec pour chacun : nom, chemin, date de création et un extrait du contenu s'il est lisible.\n"
                "Pour chaque fichier, propose :\n"
                "- un thème principal (ex : Factures, Cours, Photos, Logiciels, etc.)\n"
                "- un sous-thème (optionnel, ou vide si non pertinent)\n"
                "Voici la liste des thèmes déjà utilisés : " + ', '.join(sorted(existing_themes)) + "\n"
                "Voici la liste des sous-thèmes déjà utilisés : " + ', '.join(sorted(existing_subthemes)) + "\n"
                "Si tu penses qu'un thème ou sous-thème existant doit être modifié ou fusionné, propose-le dans ta réponse.\n"
                "Retourne un dictionnaire JSON où chaque clé est le nom du fichier et la valeur est un objet avec les clés 'theme' et 'sous_theme'.\n"
                "Exemple :\n"
                "{\n  'monfichier.pdf': { 'theme': 'Factures', 'sous_theme': 'EDF' },\n  'autre.docx': { 'theme': 'Cours', 'sous_theme': '' }\n}\n\n"
            )
            for f in batch:
                prompt += f"Nom : {f['name']} | Chemin : {f['path']} | Date : {f['date']} | Extrait : {f['excerpt'][:50]}\n"
            if self.debug:
                print(f"\n--- Prompt envoyé au batch {batch_num} ---\n{prompt}\n---")
            response = get_ai_response(prompt)
            if self.debug:
                print(f"Réponse brute IA : {response}\n")
            # On suppose que la réponse contient un JSON avec le mapping fichier->{theme, sous_theme}
            batch_suggestions = {}
            if isinstance(response, dict):
                batch_suggestions = response
            elif isinstance(response, str):
                # Nettoyage de la réponse pour extraire le bloc JSON
                json_str = None
                # Cherche un bloc ```json ... ``` ou ``` ... ```
                match = re.search(r"```json(.*?)```", response, re.DOTALL)
                if not match:
                    match = re.search(r"```(.*?)```", response, re.DOTALL)
                if match:
                    json_str = match.group(1)
                else:
                    # Sinon, cherche le premier bloc {...}
                    match = re.search(r"\{[\s\S]*\}", response)
                    if match:
                        json_str = match.group(0)
                if json_str:
                    try:
                        # Remplace les quotes simples par des doubles si besoin (pour compatibilité JSON)
                        json_str_clean = json_str.replace("'", '"')
                        batch_suggestions = json.loads(json_str_clean)
                    except Exception as e:
                        if self.debug:
                            print(f"Erreur parsing JSON extrait : {e}\n")
                else:
                    if self.debug:
                        print("Aucun bloc JSON trouvé dans la réponse IA.\n")
            # Ajoute les suggestions du batch à l'historique et au résultat global
            if batch_suggestions:
                self.previous_suggestions.update(batch_suggestions)
                all_results.update(batch_suggestions)
        return all_results

    def send_feedback(self, feedback):
        # Code to send user feedback to Gemini AI
        pass

    def receive_suggestions(self):
        # Code to receive organization suggestions from Gemini AI
        pass

    def validate_structure(self, proposed_structure):
        # Code to validate the proposed file structure against the loaded schema
        pass