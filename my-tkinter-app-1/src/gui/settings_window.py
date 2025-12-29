from tkinter import Toplevel, Label, Entry, Button, Frame, Listbox, Scrollbar, END, filedialog

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

class SettingsWindow:
    def __init__(self, master, settings, save_callback):
        self.master = master
        self.settings = settings
        self.save_callback = save_callback
        self.settings_window = None

    def show(self):
        self.settings_window = Toplevel(self.master)
        self.settings_window.title("Paramètres")
        self.settings_window.configure(bg="#23272f")
        self.settings_window.geometry("540x600")
        self.settings_window.resizable(True, False)
        self.settings_window.transient(self.master)
        self.settings_window.grab_set()
        x = self.master.winfo_x() - 520
        y = self.master.winfo_y()
        self.settings_window.geometry(f"540x600+{x}+{y}")
        nas_label = Label(self.settings_window, text="URL du NAS:", font=(get_system_font(), 12, "bold"), fg="#fff", bg="#23272f")
        nas_label.pack(pady=(20, 5), anchor="w", padx=20)
        self.nas_entry = Entry(self.settings_window, font=(get_system_font(), 11), bg="#181a20", fg="#e0e0e0", insertbackground="#fff", relief="flat", width=60)
        self.nas_entry.pack(pady=(0, 15), padx=20, fill="x")
        self.nas_entry.insert(0, self.settings.get('nas_url', ''))
        folders_label = Label(self.settings_window, text="Dossiers à scanner:", font=(get_system_font(), 12, "bold"), fg="#fff", bg="#23272f")
        folders_label.pack(pady=(0, 5), anchor="w", padx=20)
        folders_frame = Frame(self.settings_window, bg="#23272f")
        folders_frame.pack(fill="x", expand=False, padx=20, pady=(0, 10))
        self.folders_listbox = Listbox(folders_frame, font=(get_monospace_font(), 10), bg="#181a20", fg="#e0e0e0", selectbackground="#FFD700", selectforeground="#23272f", relief="flat", height=6)
        self.folders_listbox.pack(side="left", fill="both", expand=True)
        folders_scrollbar = Scrollbar(folders_frame, command=self.folders_listbox.yview, bg="#23272f", troughcolor="#23272f")
        folders_scrollbar.pack(side="right", fill="y")
        self.folders_listbox.config(yscrollcommand=folders_scrollbar.set)
        for folder in self.settings.get('scan_folders', []):
            self.folders_listbox.insert(END, folder)
        buttons_frame = Frame(self.settings_window, bg="#23272f")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 10))
        add_button = Button(buttons_frame, text="Ajouter dossier", font=(get_system_font(), 10), bg="#28a745", fg="#fff", relief="flat", command=self.add_folder)
        add_button.pack(side="left", padx=(0, 10))
        remove_button = Button(buttons_frame, text="Supprimer", font=(get_system_font(), 10), bg="#dc3545", fg="#fff", relief="flat", command=self.remove_folder)
        remove_button.pack(side="left", padx=(0, 10))
        links_label = Label(self.settings_window, text="Liens et photos:", font=(get_system_font(), 12, "bold"), fg="#fff", bg="#23272f")
        links_label.pack(pady=(10, 5), anchor="w", padx=20)
        links_frame = Frame(self.settings_window, bg="#23272f")
        links_frame.pack(fill="x", expand=False, padx=20, pady=(0, 0))
        self.links_listbox = Listbox(links_frame, font=(get_monospace_font(), 10), bg="#181a20", fg="#e0e0e0", selectbackground="#FFD700", selectforeground="#23272f", relief="flat", height=8)
        self.links_listbox.pack(side="left", fill="both", expand=True)
        links_scrollbar = Scrollbar(links_frame, command=self.links_listbox.yview, bg="#23272f", troughcolor="#23272f")
        links_scrollbar.pack(side="right", fill="y")
        self.links_listbox.config(yscrollcommand=links_scrollbar.set)
        for item in self.settings.get('links_photos', []):
            self.links_listbox.insert(END, f"{item['url']} | {item['photo']}")
        links_btn_frame = Frame(self.settings_window, bg="#23272f")
        links_btn_frame.pack(fill="x", padx=20, pady=(2, 10))
        add_link_btn = Button(links_btn_frame, text="Ajouter", font=(get_system_font(), 10), bg="#28a745", fg="#fff", relief="flat", command=self.add_link_photo)
        add_link_btn.pack(side="left", padx=(0, 10))
        del_link_btn = Button(links_btn_frame, text="Supprimer", font=(get_system_font(), 10), bg="#dc3545", fg="#fff", relief="flat", command=self.remove_link_photo)
        del_link_btn.pack(side="left", padx=(0, 10))
        action_frame = Frame(self.settings_window, bg="#23272f")
        action_frame.pack(fill="x", padx=20, pady=(0, 20))
        cancel_button = Button(action_frame, text="Annuler", font=(get_system_font(), 10), bg="#6c757d", fg="#fff", relief="flat", command=self.settings_window.destroy)
        cancel_button.pack(side="right", padx=(10, 0))
        save_button = Button(action_frame, text="Sauvegarder", font=(get_system_font(), 10, "bold"), bg="#FFD700", fg="#23272f", relief="flat", command=self.save_settings_and_close)
        save_button.pack(side="right")

    def add_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner un dossier à scanner")
        if folder and folder not in self.get_current_folders_list():
            self.folders_listbox.insert(END, folder)

    def remove_folder(self):
        selection = self.folders_listbox.curselection()
        if selection:
            self.folders_listbox.delete(selection[0])

    def get_current_folders_list(self):
        return [self.folders_listbox.get(i) for i in range(self.folders_listbox.size())]

    def add_link_photo(self):
        popup = Toplevel(self.settings_window)
        popup.title("Ajouter un lien et une photo")
        popup.configure(bg="#23272f")
        popup.geometry("400x220")
        popup.resizable(False, False)
        Label(popup, text="Lien (URL à ouvrir dans le navigateur):", font=(get_system_font(), 11), fg="#fff", bg="#23272f").pack(pady=(10, 2), anchor="w", padx=20)
        url_entry = Entry(popup, font=(get_system_font(), 10), bg="#181a20", fg="#e0e0e0", relief="flat", width=50)
        url_entry.pack(pady=(0, 10), padx=20, fill="x")
        Label(popup, text="Image associée:", font=(get_system_font(), 11), fg="#fff", bg="#23272f").pack(pady=(0, 2), anchor="w", padx=20)
        photo_entry = Entry(popup, font=(get_system_font(), 10), bg="#181a20", fg="#e0e0e0", relief="flat", width=50)
        photo_entry.pack(pady=(0, 10), padx=20, fill="x")
        def choose_photo():
            path = filedialog.askopenfilename(title="Choisir une image", filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif")])
            if path:
                photo_entry.delete(0, END)
                photo_entry.insert(0, path)
        choose_photo_btn = Button(popup, text="Parcourir", font=(get_system_font(), 10), bg="#007bff", fg="#fff", relief="flat", command=choose_photo)
        choose_photo_btn.pack(pady=(0, 10), padx=20)
        def validate():
            url = url_entry.get().strip()
            photo = photo_entry.get().strip()
            if url:
                if not photo:
                    try:
                        from banner import fetch_favicon_base64
                        photo = fetch_favicon_base64(url) or ''
                    except Exception as e:
                        print(f"Erreur récupération favicon : {e}")
                self.links_listbox.insert(END, f"{url} | {photo}")
                popup.destroy()
                # Rafraîchit le bandeau si la méthode existe sur le parent
                parent = self.settings_window.master
                while parent:
                    if hasattr(parent, 'show_links_photos_buttons'):
                        parent.show_links_photos_buttons()
                        break
                    if hasattr(parent, 'master'):
                        parent = parent.master
                    else:
                        break
        Button(popup, text="Ajouter", font=(get_system_font(), 10, "bold"), bg="#FFD700", fg="#23272f", relief="flat", command=validate).pack(pady=(0, 10))

    def remove_link_photo(self):
        selection = self.links_listbox.curselection()
        if selection:
            self.links_listbox.delete(selection[0])

    def get_links_photos_list(self):
        result = []
        for i in range(self.links_listbox.size()):
            txt = self.links_listbox.get(i)
            if '|' in txt:
                url, photo = txt.split('|', 1)
                result.append({'url': url.strip(), 'photo': photo.strip()})
        return result

    def save_settings_and_close(self):
        self.settings['nas_url'] = self.nas_entry.get().strip()
        self.settings['scan_folders'] = self.get_current_folders_list()
        self.settings['links_photos'] = self.get_links_photos_list()
        self.save_callback(self.settings)
        self.settings_window.destroy()
