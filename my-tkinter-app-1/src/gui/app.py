from tkinter import Tk, END, Frame, filedialog
from tkinter.ttk import Progressbar
import json
import os
import sys
import pathlib
import platform
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from organizer.file_organizer import organize_files
from ai.gemini_validator import GeminiValidator
from banner import Banner
from settings_window import SettingsWindow
from chat_panel import ChatPanel

def get_system_font():
    """Get appropriate font family for the current system."""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    elif system == "Darwin":  # macOS
        return "SF Pro Display"
    else:  # Linux and others
        return "Liberation Sans"

def get_monospace_font():
    """Get appropriate monospace font family for the current system."""
    system = platform.system()
    if system == "Windows":
        return "Consolas"
    elif system == "Darwin":  # macOS
        return "SF Mono"
    else:  # Linux and others
        return "Liberation Mono"

class FileOrganizerApp:
    def __init__(self, master):
        self.master = master
        master.title("File Organizer")
        master.configure(bg="#23272f")

        self.settings = self.load_settings()
        self.chat_panel = ChatPanel(master, self.on_send)
        self.chat_panel.build()

        # Load settings
        self.settings = self.load_settings()
        
        # Show initial loading and reorganization message
        self.show_initial_message()
        print(f"App: settings['links_photos'] = {self.settings.get('links_photos', [])}")
        self.show_links_photos_buttons()
    
    def load_settings(self):
        """Load settings from configuration file."""
        try:
            import json
            with open('settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Default settings - use default user directories
            from organizer.file_organizer import get_default_user_dirs
            default_dirs = get_default_user_dirs()
            return {
                'nas_url': '',
                'scan_folders': default_dirs
            }
    
    def save_settings(self):
        """Save settings to configuration file."""
        try:
            import json
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def open_settings(self):
        def save_callback(new_settings):
            self.settings = new_settings
            self.save_settings()
        win = SettingsWindow(self.master, self.settings, save_callback)
        win.show()
    
    def add_folder(self):
        """Add a folder to the scan list."""
        folder = filedialog.askdirectory(title="Sélectionner un dossier à scanner")
        if folder and folder not in self.get_current_folders_list():
            self.folders_listbox.insert(END, folder)
    
    def remove_folder(self):
        """Remove selected folder from the scan list."""
        selection = self.folders_listbox.curselection()
        if selection:
            self.folders_listbox.delete(selection[0])
    
    def get_current_folders_list(self):
        """Get the current list of folders from the listbox."""
        return [self.folders_listbox.get(i) for i in range(self.folders_listbox.size())]
    
    def save_settings_and_close(self):
        """Save the settings and close the settings window."""
        self.settings['nas_url'] = self.nas_entry.get().strip()
        self.settings['scan_folders'] = self.get_current_folders_list()
        self.save_settings()
        self.settings_window.destroy()

    def on_send(self, user_text=None):
        if user_text is None:
            user_text = self.chat_panel.user_entry.get().strip()
        if not user_text:
            return
        self.chat_panel.chat_text.config(state="normal")
        self.chat_panel.chat_text.insert(END, f"\nVous : {user_text}\n", ("user",))
        self.chat_panel.chat_text.tag_config("user", foreground="#7CFC00", font=(get_system_font(), 10, "bold"))
        self.chat_panel.chat_text.config(state="disabled")
        self.chat_panel.user_entry.delete(0, END)

        # Si l'utilisateur confirme (ex: "oui", "ok", "valider", etc.)
        if user_text.lower() in ["oui", "ok", "valider", "c'est bon", "confirmer", "accepter"]:
            self.apply_organization()
        else:
            # Traiter la demande de modification de l'utilisateur
            self.modify_organization(user_text)

    def apply_organization(self):
        """Applique l'organisation actuelle aux fichiers."""
        if not hasattr(self, 'last_regrouped'):
            return
        
        self.chat_panel.chat_text.config(state="normal")
        self.chat_panel.chat_text.insert(END, "\nAssistant : Organisation en cours...\n", ("system",))
        self.chat_panel.chat_text.tag_config("system", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
        self.chat_panel.chat_text.config(state="disabled")
        
        # Ici on appellerait la fonction d'organisation réelle
        # organize_files(self.last_regrouped, self.last_files)
        
    def modify_organization(self, user_text):
        """Modifie l'organisation selon la demande de l'utilisateur."""
        if not hasattr(self, 'last_regrouped'):
            return
            
        import threading
        import json
        from organizer.file_organizer import get_ai_response
        
        def worker():
            self.chat_panel.chat_text.config(state="normal")
            self.chat_panel.chat_text.insert(END, "\nAssistant : Modification en cours...\n", ("system",))
            self.chat_panel.chat_text.tag_config("system", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
            self.chat_panel.chat_text.config(state="disabled")
            
            # Traiter par batch pour éviter les limites de token
            batch_size = 10
            all_files = []
            for theme, sous_dict in self.last_regrouped.items():
                for sous_theme, files_list in sous_dict.items():
                    all_files.extend(files_list)
                    
            batches = [all_files[i:i+batch_size] for i in range(0, len(all_files), batch_size)]
            all_suggestions = {}
            failed_batches = []
            
            for idx, batch in enumerate(batches):
                # Construit un regrouped réduit pour le batch
                regrouped_batch = {}
                for theme, sous_dict in self.last_regrouped.items():
                    for sous_theme, files_list in sous_dict.items():
                        files_in_batch = [f for f in files_list if f in batch]
                        if files_in_batch:
                            if theme not in regrouped_batch:
                                regrouped_batch[theme] = {}
                            regrouped_batch[theme][sous_theme] = files_in_batch
                prompt = self.build_modification_prompt(user_text, regrouped_batch)
                print(f"[DEBUG] Prompt batch {idx+1} :\n", prompt)
                suggestions = None
                for attempt in range(5):
                    response = get_ai_response(prompt)
                    print(f"[DEBUG] Réponse brute IA batch {idx+1} tentative {attempt+1} :\n", response)
                    try:
                        if isinstance(response, str):
                            suggestions = json.loads(response.replace("'", '"'))
                        else:
                            suggestions = response
                        print(f"[DEBUG] Réponse IA parsée batch {idx+1} tentative {attempt+1} :\n", suggestions)
                        break
                    except Exception as e:
                        print(f"[DEBUG] Erreur parsing JSON IA batch {idx+1} tentative {attempt+1} :", e)
                        suggestions = None
                if suggestions is None:
                    failed_batches.append(batch)
                    continue
                all_suggestions.update(suggestions)

            # Si des lots ont échoué, prévenir l'utilisateur
            if failed_batches:
                from tkinter import messagebox
                failed_files = [f for batch in failed_batches for f in batch]
                msg = (
                    "Attention : certains lots n'ont pas pu être traités après 5 tentatives.\n"
                    "Les fichiers suivants n'ont pas été réorganisés :\n\n"
                    + "\n".join(failed_files)
                )
                messagebox.showwarning("Lots IA échoués", msg)
            print("[DEBUG] Regroupement de la nouvelle organisation...")
            regrouped = {}
            for file_name, info in all_suggestions.items():
                theme = info.get('theme', 'Inconnu') or 'Inconnu'
                sous_theme = info.get('sous_theme', '') or ''
                if theme not in regrouped:
                    regrouped[theme] = {}
                if sous_theme not in regrouped[theme]:
                    regrouped[theme][sous_theme] = []
                regrouped[theme][sous_theme].append(file_name)
            print("[DEBUG] Organisation regroupée :\n", regrouped)
            self.last_regrouped = regrouped
            self.chat_panel.chat_text.config(state="normal")
            self.chat_panel.chat_text.delete(1.0, END)
            self.chat_panel.chat_text.insert(END, "\n===== NOUVELLE ORGANISATION PROPOSÉE =====\n\n")
            for theme, sous_dict in regrouped.items():
                self.chat_panel.chat_text.insert(END, f"Thème : {theme}\n", ("theme",))
                for sous_theme, files_list in sous_dict.items():
                    if sous_theme and sous_theme != "":
                        self.chat_panel.chat_text.insert(END, f"  Sous-thème : {sous_theme}\n", ("sous_theme",))
                        for file_name in files_list:
                            self.chat_panel.chat_text.insert(END, f"    • {file_name}\n", ("file",))
                    else:
                        for file_name in files_list:
                            self.chat_panel.chat_text.insert(END, f"  • {file_name}\n", ("file",))
                self.chat_panel.chat_text.insert(END, "\n")
            self.chat_panel.chat_text.insert(END, "===================================\n")
            self.chat_panel.chat_text.insert(END, "\nMerci de confirmer cette organisation ou de préciser une demande de modification (ex : déplacer un fichier, renommer un thème, etc.).\n", ("confirm",))
            self.chat_panel.chat_text.tag_config("theme", foreground="#FFD700", font=(get_system_font(), 11, "bold"))
            self.chat_panel.chat_text.tag_config("sous_theme", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
            self.chat_panel.chat_text.tag_config("file", foreground="#e0e0e0", font=(get_monospace_font(), 10))
            self.chat_panel.chat_text.tag_config("confirm", foreground="#FFD700", font=(get_system_font(), 11, "italic"))
            self.chat_panel.chat_text.config(state="disabled")
            self.chat_panel.progress['value'] = 100
        threading.Thread(target=worker, daemon=True).start()

    def build_modification_prompt(self, user_text, regrouped):
        prompt = (
            "Voici l'organisation actuelle de mes fichiers. Tu dois uniquement MODIFIER les thèmes ou sous-thèmes des fichiers concernés par la demande utilisateur.\n"
            "Pour chaque fichier, indique le thème et le sous-thème (ou une chaîne vide si non pertinent).\n"
            "ATTENTION :\n"
            "- Réponds STRICTEMENT au format JSON ci-dessous, sans aucun texte avant ou après, sans tableau d'objets, sans clé supplémentaire.\n"
            "- Utilise uniquement des guillemets doubles (\"\") pour le JSON.\n"
            "- Ne modifie que les thèmes/sous-thèmes des fichiers concernés, laisse les autres inchangés.\n"
            "- N'invente pas de nouveaux fichiers.\n"
            "Exemple de réponse attendue :\n"
            "\"{\\\"fichier1.txt\\\": {\\\"theme\\\": \\\"ThèmeA\\\", \\\"sous_theme\\\": \\\"SousA\\\"}, \\\"fichier2.txt\\\": {\\\"theme\\\": \\\"ThèmeB\\\", \\\"sous_theme\\\": \\\"\\\"}}\"\n"
            "Voici l'organisation actuelle :\n"
        )
        for theme, sous_dict in regrouped.items():
            prompt += f"Thème : {theme}\n"
            for sous_theme, files_list in sous_dict.items():
                if sous_theme:
                    prompt += f"  Sous-thème : {sous_theme}\n"
                for file_name in files_list:
                    prompt += f"    - {file_name}\n"
        prompt += ("\nL'utilisateur souhaite la modification suivante :\n" + user_text +
                   "\nRÉPONDS STRICTEMENT PAR UN DICTIONNAIRE JSON VALIDE mapping chaque nom de fichier vers un objet {\"theme\": ..., \"sous_theme\": ...}. PAS DE TABLEAU, PAS DE TEXTE AUTOUR, PAS DE CLÉ 'fichiers'.")
        return prompt


    def show_initial_message(self):
        import threading, time, json
        from organizer.file_organizer import get_default_user_dirs, get_all_files
        self.chat_panel.chat_text.config(state="normal")
        self.chat_panel.chat_text.delete(1.0, END)
        self.chat_panel.chat_text.insert(END, "Assistant : Analyse de la réorganisation en cours")
        self.chat_panel.chat_text.config(state="disabled")

        def loading_and_real_organization():
            for i in range(3):
                self.chat_panel.chat_text.config(state="normal")
                self.chat_panel.chat_text.insert(END, ".")
                self.chat_panel.chat_text.see(END)
                self.chat_panel.chat_text.config(state="disabled")
                time.sleep(0.5)
            # Get real organization suggestion
            self.chat_panel.progress['value'] = 30
            
            # Use configured folders or default ones if none configured
            dirs = self.settings.get('scan_folders', [])
            if not dirs:
                from organizer.file_organizer import get_default_user_dirs
                dirs = get_default_user_dirs()
                # Update settings with default directories for next time
                self.settings['scan_folders'] = dirs
                self.save_settings()
                
            files = []
            for d in dirs:
                if os.path.exists(d):
                    files.extend(get_all_files(d))
                else:
                    print(f"Warning: Directory {d} does not exist")
            self.chat_panel.progress['value'] = 60
            suggestions = self.gemini_validator.suggest_schema(files, batch_size=5)
            self.chat_panel.progress['value'] = 90
            # Regrouper les suggestions par thème et sous-thème
            regrouped = {}
            for file_name, info in suggestions.items():
                theme = info.get('theme', 'Inconnu') or 'Inconnu'
                sous_theme = info.get('sous_theme', '') or ''
                if theme not in regrouped:
                    regrouped[theme] = {}
                if sous_theme not in regrouped[theme]:
                    regrouped[theme][sous_theme] = []
                regrouped[theme][sous_theme].append(file_name)

            self.chat_panel.chat_text.config(state="normal")
            self.chat_panel.chat_text.insert(END, "\n===== RÉORGANISATION PROPOSÉE =====\n\n")
            for theme, sous_dict in regrouped.items():
                self.chat_panel.chat_text.insert(END, f"Thème : {theme}\n", ("theme",))
                for sous_theme, files_list in sous_dict.items():
                    if sous_theme and sous_theme != "":
                        self.chat_panel.chat_text.insert(END, f"  Sous-thème : {sous_theme}\n", ("sous_theme",))
                        for file_name in files_list:
                            self.chat_panel.chat_text.insert(END, f"    • {file_name}\n", ("file",))
                    else:
                        for file_name in files_list:
                            self.chat_panel.chat_text.insert(END, f"  • {file_name}\n", ("file",))
                self.chat_panel.chat_text.insert(END, "\n")
            self.chat_panel.chat_text.insert(END, "===================================\n")
            # Styles pour améliorer la lisibilité
            self.chat_panel.chat_text.tag_config("theme", foreground="#FFD700", font=(get_system_font(), 11, "bold"))
            self.chat_panel.chat_text.tag_config("sous_theme", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
            self.chat_panel.chat_text.tag_config("file", foreground="#e0e0e0", font=(get_monospace_font(), 10))
            # Message de confirmation/modification
            self.chat_panel.chat_text.insert(END, "\nMerci de confirmer cette organisation ou de préciser une demande de modification (ex : déplacer un fichier, renommer un thème, etc.).\n", ("confirm",))
            self.chat_panel.chat_text.tag_config("confirm", foreground="#FFD700", font=(get_system_font(), 11, "italic"))
            self.chat_panel.chat_text.config(state="disabled")
            self.chat_panel.progress['value'] = 100
            # Stocke la dernière organisation pour modification/validation
            self.last_regrouped = regrouped
            self.last_files = files

        threading.Thread(target=loading_and_real_organization, daemon=True).start()




        self.gemini_validator = GeminiValidator()

    def show_links_photos_buttons(self):
        banner = Banner(self.master, self.settings.get('links_photos', []))
        banner.show()

def get_taskbar_height():
    """Get taskbar height for Windows, return 0 for other systems."""
    if platform.system() == "Windows":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hWnd = user32.FindWindowW(u'Shell_TrayWnd', None)
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hWnd, ctypes.byref(rect))
            # Check if taskbar is at the bottom
            screen_width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            return rect.bottom - rect.top if rect.left == 0 and rect.right == screen_width else 0
        except Exception:
            return 40  # fallback default
    return 0

def main():
    root = Tk()

    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    banner_width = 400
    current_os = platform.system()
    
    if current_os == "Windows":
        # Windows: Right vertical banner, no title bar
        taskbar_height = get_taskbar_height()
        banner_height = screen_height - taskbar_height
        x = screen_width - banner_width
        y = 0
        root.geometry(f"{banner_width}x{banner_height}+{x}+{y}")
        
        # Remove window frame (no title bar, no border)
        root.overrideredirect(1)
        
        # Lower the window below all others
        root.lower()
        root.attributes('-topmost', False)
    else:
        # Linux/Mac: Same as Windows - right vertical banner, no title bar
        banner_height = screen_height  # No taskbar consideration on Linux
        x = screen_width - banner_width
        y = 0
        root.geometry(f"{banner_width}x{banner_height}+{x}+{y}")
        
        # Remove window frame (no title bar, no border)
        root.overrideredirect(1)
        
        # Lower the window below all others (may not work on all Linux window managers)
        try:
            root.lower()
            root.attributes('-topmost', False)
        except Exception:
            pass  # Some Linux window managers may not support these attributes

    app = FileOrganizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()