
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import json
import unittest
from organizer.file_organizer import get_default_user_dirs, get_all_files
from ai.gemini_validator import GeminiValidator

class TestGeminiOrganization(unittest.TestCase):
    def test_first_organization_suggestion(self):
        # Récupère les fichiers des dossiers par défaut (Documents, Downloads, Desktop)
        dirs = get_default_user_dirs()
        files = []
        for d in dirs:
            files.extend(get_all_files(d))
        gemini = GeminiValidator(debug=True)
        batch_size = 5
        suggestions = gemini.suggest_schema(files, batch_size=batch_size)
        # Écrit la suggestion dans un fichier txt dans le dossier test
        os.makedirs('test', exist_ok=True)
        with open(os.path.join('test', 'first_organization_suggestion.txt'), 'w', encoding='utf-8') as f:
            f.write(json.dumps(suggestions, indent=2, ensure_ascii=False))
        # Vérifie que le fichier a bien été créé
        self.assertTrue(os.path.isfile(os.path.join('test', 'first_organization_suggestion.txt')))

if __name__ == '__main__':
    unittest.main()
