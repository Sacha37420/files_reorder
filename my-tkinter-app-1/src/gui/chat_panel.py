from tkinter import Frame, Label, Text, Scrollbar, Entry, Button, END
from tkinter.ttk import Progressbar

def get_system_font():
    import platform
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    elif system == "Darwin":
        return "SF Pro Display"
    else:
        return "Liberation Sans"

def get_monospace_font():
    import platform
    system = platform.system()
    if system == "Windows":
        return "Consolas"
    elif system == "Darwin":
        return "SF Mono"
    else:
        return "Liberation Mono"

class ChatPanel:
    def apply_organization(self, last_regrouped, settings, save_settings_callback=None):
        settings['organization'] = last_regrouped
        if save_settings_callback:
            save_settings_callback()
        self.add_message("\nAssistant : Organisation en cours...\n", tag="system")
        self.set_tag("system", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))

    def modify_organization(self, user_text, last_regrouped, update_callback=None):
        import threading
        import json
        from api.gemini import get_ai_response
        def worker():
            self.add_message("\nAssistant : Modification en cours...\n", tag="system")
            self.set_tag("system", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
            batch_size = 10
            all_files = []
            for theme, sous_dict in last_regrouped.items():
                for sous_theme, files_list in sous_dict.items():
                    all_files.extend(files_list)
            batches = [all_files[i:i+batch_size] for i in range(0, len(all_files), batch_size)]
            all_suggestions = {}
            failed_batches = []
            for idx, batch in enumerate(batches):
                regrouped_batch = {}
                for theme, sous_dict in last_regrouped.items():
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
                    print("[DEBUG] Appel à modify_organization avec le batch")
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
            if update_callback:
                update_callback(regrouped)
            self.add_message("\n===== NOUVELLE ORGANISATION PROPOSÉE =====\n\n", clear=True)
            for theme, sous_dict in regrouped.items():
                self.add_message(f"Thème : {theme}\n", tag="theme")
                for sous_theme, files_list in sous_dict.items():
                    if sous_theme and sous_theme != "":
                        self.add_message(f"  Sous-thème : {sous_theme}\n", tag="sous_theme")
                        for file_name in files_list:
                            self.add_message(f"    • {file_name}\n", tag="file")
                    else:
                        for file_name in files_list:
                            self.add_message(f"  • {file_name}\n", tag="file")
                self.add_message("\n")
            self.add_message("===================================\n")
            self.add_message("\nMerci de confirmer cette organisation ou de préciser une demande de modification (ex : déplacer un fichier, renommer un thème, etc.).\n", tag="confirm")
            self.set_tag("theme", foreground="#FFD700", font=(get_system_font(), 11, "bold"))
            self.set_tag("sous_theme", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
            self.set_tag("file", foreground="#e0e0e0", font=(get_monospace_font(), 10))
            self.set_tag("confirm", foreground="#FFD700", font=(get_system_font(), 11, "italic"))
            self.set_progress(100)
        threading.Thread(target=worker, daemon=True).start()

    def __init__(self, master, on_send_callback, open_settings_callback=None, initial_files=None):
        self.master = master
        self.on_send_callback = on_send_callback
        self.open_settings_callback = open_settings_callback
        self.initial_files = initial_files
        self.frame = None
        self.chat_text = None
        self.user_entry = None
        self.send_button = None
        self.settings_button = None
        self.scrollbar = None
        self.progress = None

    def add_message(self, text, tag=None, clear=False):
        def _do_add():
            self.chat_text.config(state="normal")
            if clear:
                self.chat_text.delete(1.0, END)
            self.chat_text.insert(END, text, (tag,) if tag else ())
            self.chat_text.config(state="disabled")
        try:
            # Si on n'est pas dans le thread principal, utiliser .after
            import threading
            if threading.current_thread() is threading.main_thread():
                _do_add()
            else:
                self.chat_text.after(0, _do_add)
        except Exception as e:
            print(f"[DEBUG] Erreur add_message: {e}")

    def set_tag(self, tag, **kwargs):
        self.chat_text.tag_config(tag, **kwargs)

    def set_progress(self, value):
        self.progress['value'] = value

    def request_initial_organization(self, files, on_result=None):
        import threading
        from ai.gemini_validator import GeminiValidator
        import json
        def worker():
            try:
                print("[DEBUG] worker() lancé pour organisation initiale")
                if not hasattr(self, 'chat_text') or self.chat_text is None:
                    print("[DEBUG][ERREUR] self.chat_text n'est pas initialisé dans worker() !")
                    return
                self.add_message("\nAssistant : Organisation initiale en cours...\n", tag="system")
                self.set_tag("system", foreground="#FFD700", font=(get_system_font(), 10, "italic"))
                self.set_progress(10)
                gemini = GeminiValidator(debug=True)
                batch_size = 5
                existing_themes = set()
                existing_subthemes = set()
                try:
                    with open('settings.json', 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    org = settings.get('organization', {})
                    for theme, sous_dict in org.items():
                        existing_themes.add(theme)
                        for sous_theme in sous_dict:
                            if sous_theme:
                                existing_subthemes.add(sous_theme)
                except Exception:
                    pass
                # DEBUG: Affiche le nombre de fichiers transmis
                self.add_message(f"[DEBUG] Nombre de fichiers transmis à l'IA : {len(files)}\n", tag="system")
                if files and isinstance(files[0], dict):
                    self.add_message(f"[DEBUG] Exemple fichier : {files[0]}\n", tag="system")
                # DEBUG: Affiche le prompt envoyé
                import io
                import sys
                # Appel sans redirection pour laisser passer les prints de debug
                def progress_callback(p):
                    # Appel thread-safe
                    self.set_progress(p)
                suggestions = gemini.suggest_schema(
                    files,
                    batch_size=batch_size,
                    existing_themes=existing_themes,
                    existing_subthemes=existing_subthemes,
                    progress_callback=progress_callback
                )
                # On refait le prompt pour affichage dans le chat (optionnel)
                # Si tu veux absolument capturer le prompt, il faut le retourner explicitement par suggest_schema
                prompt_debug = "[Prompt non capturé, voir console pour debug]"
                self.add_message(f"[DEBUG] Prompt envoyé à l'IA :\n{prompt_debug}\n", tag="system")
                self.set_progress(50)
                # DEBUG: Affiche la réponse brute
                self.add_message(f"[DEBUG] Réponse brute IA : {suggestions}\n", tag="system")
                if not suggestions:
                    self.add_message("\n===== ORGANISATION INITIALE PROPOSÉE (RAW) =====\n\n", clear=True)
                    self.add_message("Aucune suggestion n'a pu être générée par l'IA.\n")
                    self.add_message("===================================\n")
                    self.add_message("\nMerci de préciser une demande de modification ou de relancer l'organisation.\n", tag="confirm")
                    self.set_tag("confirm", foreground="#FFD700", font=(get_system_font(), 11, "italic"))
                    self.set_progress(100)
                    if on_result:
                        on_result(None)
                    return
                regrouped = {}
                for file_name, info in suggestions.items():
                    theme = info.get('theme', 'Divers') if isinstance(info, dict) else info or 'Divers'
                    sous_theme = info.get('sous_theme', '') if isinstance(info, dict) else ''
                    if theme not in regrouped:
                        regrouped[theme] = {}
                    if sous_theme not in regrouped[theme]:
                        regrouped[theme][sous_theme] = []
                    regrouped[theme][sous_theme].append(file_name)
                self.set_progress(80)
                self.add_message("\n===== ORGANISATION INITIALE PROPOSÉE =====\n\n", clear=True)
                for theme, sous_dict in regrouped.items():
                    self.add_message(f"Thème : {theme}\n", tag="theme")
                    for sous_theme, files_list in sous_dict.items():
                        if sous_theme and sous_theme != "":
                            self.add_message(f"  Sous-thème : {sous_theme}\n", tag="sous_theme")
                            for file_name in files_list:
                                self.add_message(f"    • {file_name}\n", tag="file")
                        else:
                            for file_name in files_list:
                                self.add_message(f"  • {file_name}\n", tag="file")
                    self.add_message("\n")
                self.add_message("===================================\n")
                self.add_message("\nMerci de confirmer cette organisation ou de préciser une demande de modification (ex : déplacer un fichier, renommer un thème, etc.).\n", tag="confirm")
                self.set_tag("theme", foreground="#FFD700", font=(get_system_font(), 11, "bold"))
                self.set_tag("sous_theme", foreground="#87CEEB", font=(get_system_font(), 10, "italic"))
                self.set_tag("file", foreground="#e0e0e0", font=(get_monospace_font(), 10))
                self.set_tag("confirm", foreground="#FFD700", font=(get_system_font(), 11, "italic"))
                self.set_progress(100)
                if on_result:
                    on_result(regrouped)
            except Exception as e:
                import traceback
                print(f"[DEBUG][EXCEPTION] Exception dans worker() : {e}")
                traceback.print_exc()
        threading.Thread(target=worker, daemon=True).start()

    def build(self):
        # Fenêtre sans bordure, bandeau à droite
        self.master.overrideredirect(True)
        self.master.update_idletasks()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        bandeau_width = 400
        bandeau_height = screen_height - 50
        x = screen_width - bandeau_width
        y = 0
        self.master.geometry(f"{bandeau_width}x{bandeau_height}+{x}+{y}")
        self.master.configure(bg="#23272f")

        self.frame = Frame(self.master, bg="#23272f")
        self.frame.pack(fill="both", expand=True)

        # Zone de chat + scrollbar
        chat_frame = Frame(self.frame, bg="#23272f")
        chat_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0,0))
        self.chat_text = Text(chat_frame, wrap="word", bg="#23272f", fg="#e0e0e0", font=(get_system_font(), 10), borderwidth=0, highlightthickness=0)
        self.chat_text.pack(side="left", fill="both", expand=True)
        self.scrollbar = Scrollbar(chat_frame, command=self.chat_text.yview)
        self.chat_text.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        # Zone d'entrée + boutons
        input_frame = Frame(self.frame, bg="#23272f")
        input_frame.pack(side="top", fill="x", padx=10, pady=(5,5))
        self.user_entry = Entry(input_frame, font=(get_system_font(), 10), bg="#23272f", fg="#e0e0e0", borderwidth=0, highlightthickness=0)
        self.user_entry.pack(side="left", fill="x", expand=True)
        self.send_button = Button(input_frame, text="Envoyer", command=self.on_send, bg="#FFD700", fg="#23272f", font=(get_system_font(), 10, "bold"), borderwidth=0, highlightthickness=0)
        self.send_button.pack(side="left", padx=10)
        self.settings_button = Button(input_frame, text="⚙", command=self._open_settings, bg="#23272f", fg="#FFD700", font=(get_system_font(), 10), borderwidth=0, highlightthickness=0)
        self.settings_button.pack(side="left", padx=(0,10))

        # Barre de progression en bas
        self.progress = Progressbar(self.frame, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(side="bottom", fill="x", padx=10, pady=(0,10))

        # Récupère et affiche l'organisation initiale via l'IA (après création des widgets)
        if self.initial_files:
            print(f"[DEBUG] Contenu de self.initial_files avant organisation initiale : {len(self.initial_files)} fichiers")
            self.frame.after(0, lambda: self.request_initial_organization(self.initial_files))

    def on_send(self):
        user_text = self.user_entry.get().strip()
        if not user_text:
            return
        self.chat_text.config(state="normal")
        self.chat_text.insert(END, f"\nVous : {user_text}\n", ("user",))
        self.chat_text.tag_config("user", foreground="#7CFC00", font=(get_system_font(), 10, "bold"))
        self.chat_text.config(state="disabled")
        self.user_entry.delete(0, END)
        self.on_send_callback(user_text)
    def _open_settings(self):
        if self.open_settings_callback:
            self.open_settings_callback()
