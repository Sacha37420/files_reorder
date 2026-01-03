from tkinter import Tk, END, Frame, filedialog
from tkinter.ttk import Progressbar
import json
import os
import sys
import pathlib
import platform
import subprocess
import traceback

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from organizer.file_organizer import organize_files
from ai.gemini_validator import GeminiValidator
from banner import Banner
from settings_window import SettingsWindow
from chat_panel import ChatPanel

# Ensure dependencies are installed
install_script = os.path.join(os.path.dirname(__file__), '..', 'install', 'install_dependencies.py')
subprocess.check_call([sys.executable, install_script])

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
        print("[DEBUG] Initializing FileOrganizerApp...")
        self.master = master
        master.title("File Organizer")
        print("[DEBUG] Window title set.")
        master.configure(bg="#23272f")
        print("[DEBUG] Window background configured.")
        self.settings = self.load_settings()
        print("[DEBUG] Settings loaded.")

        # Initialize ChatPanel early
        print("[DEBUG] Initializing ChatPanel...")
        self.chat_panel = ChatPanel(master, self.on_send, open_settings_callback=self.open_settings, initial_files=[])
        print("[DEBUG] ChatPanel initialized.")
        print("[DEBUG] Building ChatPanel...")
        self.chat_panel.build()
        print("[DEBUG] ChatPanel built.")

        # Display the window before scanning folders
        self.master.update()

        # Display banner early and force UI update
        links_photos = self.settings.get('links_photos', [])
        if links_photos:
            print("[DEBUG] Links/photos found, displaying banner.")
            Banner(self.master, links_photos).show()
            self.master.update()  # Force immediate UI update

        from organizer.file_organizer import get_all_files
        self.last_files = []
        scan_folders = self.settings.get('scan_folders', [])
        print(f"[DEBUG] Scan folders: {scan_folders}")

        # Use the existing progress bar in ChatPanel
        if hasattr(self.chat_panel, 'progress'):
            self.chat_panel.progress['maximum'] = len(scan_folders)
        else:
            print("[ERROR] ChatPanel does not have a progress bar.")

        for i, folder in enumerate(scan_folders):
            try:
                print(f"[DEBUG] Scanning folder: {folder}")
                files = get_all_files(folder)
                print(f"[DEBUG] Found {len(files)} files in {folder}")
                self.last_files.extend(files)
            except Exception as e:
                print(f"[ERROR] Failed to scan folder {folder}: {e}")
            finally:
                if hasattr(self.chat_panel, 'progress'):
                    self.chat_panel.set_progress(i + 1)
                self.master.update_idletasks()

        print(f"[DEBUG] Total files scanned: {len(self.last_files)}")
        if self.last_files and isinstance(self.last_files[0], dict):
            print(f"[DEBUG] Example file: {self.last_files[0]}")

        self.last_regrouped = self.settings.get('organization', {})
        print(f"[DEBUG] Last regrouped settings: {self.last_regrouped}")
    
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
    try:
        print("[DEBUG] Starting the application...")
        root = Tk()
        print("[DEBUG] Tkinter root window initialized.")
        app = FileOrganizerApp(root)
        print("[DEBUG] FileOrganizerApp initialized.")
        root.mainloop()
        print("[DEBUG] Application main loop started.")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        traceback.print_exc()