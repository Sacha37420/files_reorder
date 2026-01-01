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
    def request_initial_organization(self):
        def on_result(regrouped):
            if regrouped is not None:
                self.last_regrouped = regrouped
        self.chat_panel.request_initial_organization(self.last_files, on_result=on_result)
    def __init__(self, master):
        self.master = master
        master.title("File Organizer")
        master.configure(bg="#23272f")
        self.settings = self.load_settings()
        from organizer.file_organizer import get_all_files
        self.last_files = []
        scan_folders = self.settings.get('scan_folders', [])
        for folder in scan_folders:
            self.last_files.extend(get_all_files(folder))
        print(f"[DEBUG] last_files construit : {len(self.last_files)} fichiers")
        if self.last_files and isinstance(self.last_files[0], dict):
            print(f"[DEBUG] Exemple fichier : {self.last_files[0]}")
        for folder in self.settings.get('scan_folders', []):
            files = get_all_files(folder)
            self.last_files.extend(files)
        self.chat_panel = ChatPanel(master, self.on_send, open_settings_callback=self.open_settings, initial_files=self.last_files)
        self.chat_panel.build()
        # Utilise l'organisation du settings si elle existe
        self.last_regrouped = self.settings.get('organization', {})
        print(f"App: settings['links_photos'] = {self.settings.get('links_photos', [])}")
        # Affiche les boutons liens/photos dans une popup indépendante
        links_photos = self.settings.get('links_photos', [])
        if links_photos:
            self.master.after(500, lambda: Banner(self.master, links_photos).show())
    
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
        self.chat_panel.add_message(f"\nVous : {user_text}\n", tag="user")
        self.chat_panel.set_tag("user", foreground="#7CFC00", font=(get_system_font(), 10, "bold"))
        self.chat_panel.user_entry.delete(0, END)
        # La logique d'organisation est maintenant gérée dans ChatPanel
        print(f"[DEBUG] Transmission à ChatPanel : {len(self.last_files)} fichiers")
        self.chat_panel.handle_user_input(user_text)

if __name__ == "__main__":
    root = Tk()
    app = FileOrganizerApp(root)
    root.mainloop()