from tkinter import Tk, Label, Entry, Button, Text, Scrollbar, END, Frame, Listbox, Toplevel, filedialog
from tkinter.ttk import Progressbar
import json
import os
import sys
import pathlib
import platform
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from organizer.file_organizer import organize_files
from ai.gemini_validator import GeminiValidator

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




        # Chat display area (proposition d'organisation)
        self.chat_label = Label(master, text="Proposition d'organisation :", font=(get_system_font(), 12, "bold"), fg="#fff", bg="#23272f")
        self.chat_label.pack(padx=18, anchor="w")



        # Main container to manage chat and input area
        # Add top, right, and bottom margins
        margin_top = 40
        margin_bottom = 24
        margin_right = 32
        margin_left = 32
        main_container = Frame(master, bg="#23272f")
        main_container.place(x=margin_left, y=margin_top, relwidth=1, relheight=1, height=-(margin_top+margin_bottom), width=-(margin_left+margin_right))

        # Layout: vertical (progress bar, chat, input)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        # Progress bar above chat
        self.progress = Progressbar(main_container, orient="horizontal", mode="determinate", length=200)
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.progress['value'] = 0

        chat_frame = Frame(main_container, bg="#23272f")
        chat_frame.grid(row=1, column=0, sticky="nsew")

        self.chat_text = Text(chat_frame, font=(get_monospace_font(), 11), bg="#181a20", fg="#e0e0e0", relief="flat", wrap="word", state="disabled", borderwidth=0, highlightthickness=1, highlightbackground="#444")
        self.chat_text.pack(side="left", fill="both", expand=True)

        self.scrollbar = Scrollbar(chat_frame, command=self.chat_text.yview, bg="#23272f", troughcolor="#23272f", bd=0, relief="flat")
        self.scrollbar.pack(side='right', fill='y')
        self.chat_text.config(yscrollcommand=self.scrollbar.set)

        # Input area (Entry + Buttons) just below chat, always visible
        input_frame = Frame(main_container, bg="#23272f")
        input_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.user_entry = Entry(input_frame, font=(get_system_font(), 11), bg="#23272f", fg="#fff", insertbackground="#fff", relief="flat", width=32)
        self.user_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        # Settings button
        self.settings_button = Button(input_frame, text="⚙️", font=(get_system_font(), 10, "bold"), bg="#6c757d", fg="#fff", relief="flat", command=self.open_settings, width=3)
        self.settings_button.pack(side="right", padx=(0, 4))
        
        self.send_button = Button(input_frame, text="Envoyer", font=(get_system_font(), 10, "bold"), bg="#FFD700", fg="#23272f", relief="flat", command=self.on_send)
        self.send_button.pack(side="right")

        # Load settings
        self.settings = self.load_settings()
        
        # Show initial loading and reorganization message
        self.show_initial_message()
    
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
        """Open the settings configuration window."""
        self.settings_window = Toplevel(self.master)
        self.settings_window.title("Paramètres")
        self.settings_window.configure(bg="#23272f")
        self.settings_window.geometry("500x400")
        self.settings_window.resizable(False, False)
        
        # Center the settings window
        self.settings_window.transient(self.master)
        self.settings_window.grab_set()
        
        # Position relative to parent window
        x = self.master.winfo_x() - 520  # Place to the left of main window
        y = self.master.winfo_y()
        self.settings_window.geometry(f"500x400+{x}+{y}")
        
        # NAS URL section
        nas_label = Label(self.settings_window, text="URL du NAS:", font=(get_system_font(), 12, "bold"), fg="#fff", bg="#23272f")
        nas_label.pack(pady=(20, 5), anchor="w", padx=20)
        
        self.nas_entry = Entry(self.settings_window, font=(get_system_font(), 11), bg="#181a20", fg="#e0e0e0", insertbackground="#fff", relief="flat", width=60)
        self.nas_entry.pack(pady=(0, 15), padx=20, fill="x")
        self.nas_entry.insert(0, self.settings.get('nas_url', ''))
        
        # Scan folders section
        folders_label = Label(self.settings_window, text="Dossiers à scanner:", font=(get_system_font(), 12, "bold"), fg="#fff", bg="#23272f")
        folders_label.pack(pady=(0, 5), anchor="w", padx=20)
        
        # Frame for folders list and buttons
        folders_frame = Frame(self.settings_window, bg="#23272f")
        folders_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Listbox for folders
        self.folders_listbox = Listbox(folders_frame, font=(get_monospace_font(), 10), bg="#181a20", fg="#e0e0e0", selectbackground="#FFD700", selectforeground="#23272f", relief="flat", height=8)
        self.folders_listbox.pack(side="left", fill="both", expand=True)
        
        # Scrollbar for listbox
        folders_scrollbar = Scrollbar(folders_frame, command=self.folders_listbox.yview, bg="#23272f", troughcolor="#23272f")
        folders_scrollbar.pack(side="right", fill="y")
        self.folders_listbox.config(yscrollcommand=folders_scrollbar.set)
        
        # Populate listbox with current folders
        for folder in self.settings.get('scan_folders', []):
            self.folders_listbox.insert(END, folder)
        
        # Buttons frame
        buttons_frame = Frame(self.settings_window, bg="#23272f")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Add folder button
        add_button = Button(buttons_frame, text="Ajouter dossier", font=(get_system_font(), 10), bg="#28a745", fg="#fff", relief="flat", command=self.add_folder)
        add_button.pack(side="left", padx=(0, 10))
        
        # Remove folder button
        remove_button = Button(buttons_frame, text="Supprimer", font=(get_system_font(), 10), bg="#dc3545", fg="#fff", relief="flat", command=self.remove_folder)
        remove_button.pack(side="left", padx=(0, 10))
        
        # Save and Cancel buttons
        action_frame = Frame(self.settings_window, bg="#23272f")
        action_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        cancel_button = Button(action_frame, text="Annuler", font=(get_system_font(), 10), bg="#6c757d", fg="#fff", relief="flat", command=self.settings_window.destroy)
        cancel_button.pack(side="right", padx=(10, 0))
        
        save_button = Button(action_frame, text="Sauvegarder", font=(get_system_font(), 10, "bold"), bg="#FFD700", fg="#23272f", relief="flat", command=self.save_settings_and_close)
        save_button.pack(side="right")
    
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

    def on_send(self):
        user_text = self.user_entry.get().strip()
        if not user_text:
            return
        self.chat_text.config(state="normal")
        self.chat_text.insert(END, f"\nVous : {user_text}\n", ("user",))
        self.chat_text.tag_config("user", foreground="#7CFC00", font=(get_system_font(), 10, "bold"))
        self.chat_text.config(state="disabled")
        self.user_entry.delete(0, END)

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
        
        self.chat_text.config(state="normal")
        self.chat_text.insert(END, "\nAssistant : Organisation en cours...\n", ("system",))
        self.chat_text.tag_config("system", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
        self.chat_text.config(state="disabled")
        
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
            self.chat_text.config(state="normal")
            self.chat_text.insert(END, "\nAssistant : Modification en cours...\n", ("system",))
            self.chat_text.tag_config("system", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
            self.chat_text.config(state="disabled")
            
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
            self.progress['value'] = 80
            self.chat_text.config(state="normal")
            self.chat_text.delete(1.0, END)
            self.chat_text.insert(END, "\n===== NOUVELLE ORGANISATION PROPOSÉE =====\n\n")
            for theme, sous_dict in regrouped.items():
                self.chat_text.insert(END, f"Thème : {theme}\n", ("theme",))
                for sous_theme, files_list in sous_dict.items():
                    if sous_theme and sous_theme != "":
                        self.chat_text.insert(END, f"  Sous-thème : {sous_theme}\n", ("sous_theme",))
                        for file_name in files_list:
                            self.chat_text.insert(END, f"    • {file_name}\n", ("file",))
                    else:
                        for file_name in files_list:
                            self.chat_text.insert(END, f"  • {file_name}\n", ("file",))
                self.chat_text.insert(END, "\n")
            self.chat_text.insert(END, "===================================\n")
            self.chat_text.insert(END, "\nMerci de confirmer cette organisation ou de préciser une demande de modification (ex : déplacer un fichier, renommer un thème, etc.).\n", ("confirm",))
            self.chat_text.tag_config("theme", foreground="#FFD700", font=(get_system_font(), 11, "bold"))
            self.chat_text.tag_config("sous_theme", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
            self.chat_text.tag_config("file", foreground="#e0e0e0", font=(get_monospace_font(), 10))
            self.chat_text.tag_config("confirm", foreground="#FFD700", font=(get_system_font(), 11, "italic"))
            self.chat_text.config(state="disabled")
            self.progress['value'] = 100
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
        self.chat_text.config(state="normal")
        self.chat_text.delete(1.0, END)
        self.chat_text.insert(END, "Assistant : Analyse de la réorganisation en cours")
        self.chat_text.config(state="disabled")

        def loading_and_real_organization():
            for i in range(3):
                self.chat_text.config(state="normal")
                self.chat_text.insert(END, ".")
                self.chat_text.see(END)
                self.chat_text.config(state="disabled")
                time.sleep(0.5)
            # Get real organization suggestion
            self.progress['value'] = 30
            
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
            self.progress['value'] = 60
            suggestions = self.gemini_validator.suggest_schema(files, batch_size=5)
            self.progress['value'] = 90
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

            self.chat_text.config(state="normal")
            self.chat_text.insert(END, "\n===== RÉORGANISATION PROPOSÉE =====\n\n")
            for theme, sous_dict in regrouped.items():
                self.chat_text.insert(END, f"Thème : {theme}\n", ("theme",))
                for sous_theme, files_list in sous_dict.items():
                    if sous_theme and sous_theme != "":
                        self.chat_text.insert(END, f"  Sous-thème : {sous_theme}\n", ("sous_theme",))
                        for file_name in files_list:
                            self.chat_text.insert(END, f"    • {file_name}\n", ("file",))
                    else:
                        for file_name in files_list:
                            self.chat_text.insert(END, f"  • {file_name}\n", ("file",))
                self.chat_text.insert(END, "\n")
            self.chat_text.insert(END, "===================================\n")
            # Styles pour améliorer la lisibilité
            self.chat_text.tag_config("theme", foreground="#FFD700", font=(get_system_font(), 11, "bold"))
            self.chat_text.tag_config("sous_theme", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
            self.chat_text.tag_config("file", foreground="#e0e0e0", font=(get_monospace_font(), 10))
            # Message de confirmation/modification
            self.chat_text.insert(END, "\nMerci de confirmer cette organisation ou de préciser une demande de modification (ex : déplacer un fichier, renommer un thème, etc.).\n", ("confirm",))
            self.chat_text.tag_config("confirm", foreground="#FFD700", font=(get_system_font(), 11, "italic"))
            self.chat_text.config(state="disabled")
            self.progress['value'] = 100
            # Stocke la dernière organisation pour modification/validation
            self.last_regrouped = regrouped
            self.last_files = files

        threading.Thread(target=loading_and_real_organization, daemon=True).start()




        self.gemini_validator = GeminiValidator()

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