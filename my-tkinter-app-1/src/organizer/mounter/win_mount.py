import subprocess
import os
import sys
import urllib.request
import tempfile
import winreg
from pathlib import Path
import time

class SFTPMounterWindows:
    def __init__(self):
        self.winfsp_url = "https://github.com/winfsp/winfsp/releases/download/v2.0/winfsp-2.0.23075.msi"
        
    def is_admin(self):
        """Vérifie si le script tourne avec les droits admin"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def run_as_admin(self):
        """Relance le script avec les droits administrateur"""
        if not self.is_admin():
            print("Demande des droits administrateur...")
            import ctypes
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    
    def is_winfsp_installed(self):
        """Vérifie si WinFsp est installé"""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\WinFsp", 0, winreg.KEY_READ)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
    
    def download_file(self, url, filename):
        """Télécharge un fichier avec barre de progression"""
        print(f"Téléchargement de {filename}...")
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        
        def reporthook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            sys.stdout.write(f"\r{percent}% ")
            sys.stdout.flush()
        
        urllib.request.urlretrieve(url, temp_path, reporthook)
        print("\nTéléchargement terminé.")
        return temp_path
    
    def install_msi(self, msi_path):
        """Installe un fichier MSI silencieusement"""
        print(f"Installation de {os.path.basename(msi_path)}...")
        result = subprocess.run(
            ["msiexec", "/i", msi_path, "/quiet", "/norestart"],
            capture_output=True
        )
        if result.returncode == 0:
            print("Installation réussie.")
            return True
        else:
            print(f"Erreur d'installation: {result.stderr.decode()}")
            return False
    
    def install_dependencies(self):
        """Installe WinFsp si nécessaire"""
        if not self.is_winfsp_installed():
            print("\n=== Installation de WinFsp ===")
            winfsp_msi = self.download_file(self.winfsp_url, "winfsp.msi")
            if not self.install_msi(winfsp_msi):
                return False
            os.remove(winfsp_msi)
        else:
            print("✓ WinFsp déjà installé")
        
        return True
    
    def get_available_drive_letter(self):
        """Trouve une lettre de lecteur disponible"""
        import string
        used_drives = [f"{d}:" for d in string.ascii_uppercase 
                      if os.path.exists(f"{d}:")]
        for letter in string.ascii_uppercase[::-1]:
            drive = f"{letter}:"
            if drive not in used_drives:
                return drive
        return None
    
    def check_rclone(self):
        """Vérifie si rclone est installé, sinon le télécharge"""
        rclone_path = Path.home() / ".rclone" / "rclone.exe"
        
        if rclone_path.exists():
            print("✓ Rclone déjà installé")
            return str(rclone_path)
        
        print("\n=== Installation de Rclone ===")
        rclone_dir = Path.home() / ".rclone"
        rclone_dir.mkdir(exist_ok=True)
        
        # URL de téléchargement rclone
        rclone_url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
        zip_path = self.download_file(rclone_url, "rclone.zip")
        
        # Extraire le zip
        import zipfile
        print("Extraction de rclone...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Trouver rclone.exe dans le zip
            for file in zip_ref.namelist():
                if file.endswith('rclone.exe'):
                    zip_ref.extract(file, tempfile.gettempdir())
                    extracted_path = Path(tempfile.gettempdir()) / file
                    extracted_path.rename(rclone_path)
                    break
        
        os.remove(zip_path)
        print(f"✓ Rclone installé dans {rclone_path}")
        return str(rclone_path)
    
    def create_rclone_config(self, name, host, username, password, port, rclone_path):
        """Crée une configuration rclone pour SFTP"""
        config_dir = Path.home() / ".config" / "rclone"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "rclone.conf"
        
        # Obscurcir le mot de passe avec rclone
        obscured_pass = self.obscure_password(password, rclone_path)
        if not obscured_pass:
            print("Erreur: Impossible d'obscurcir le mot de passe")
            return None
        
        # Configuration SFTP
        config_content = f"""[{name}]
type = sftp
host = {host}
user = {username}
port = {port}
pass = {obscured_pass}
shell_type = unix
md5sum_command = md5
sha1sum_command = sha1
"""
        
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        return str(config_file)
    
    def obscure_password(self, password, rclone_path):
        """Obscurcit le mot de passe pour rclone"""
        try:
            result = subprocess.run(
                [rclone_path, "obscure", password],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Erreur lors de l'obscurcissement du mot de passe: {e}")
            return None
    
    def mount_with_rclone(self, host, username, password, remote_path="/", 
                         drive_letter=None, port=22):
        """Monte le partage SFTP avec rclone"""
        # Vérifier/installer rclone
        rclone_path = self.check_rclone()
        
        if drive_letter is None:
            drive_letter = self.get_available_drive_letter()
            if drive_letter is None:
                print("Erreur: Aucune lettre de lecteur disponible")
                return False
        
        print(f"\n=== Montage du partage SFTP sur {drive_letter} ===")
        
        # Vérifier si le lecteur existe déjà et le nettoyer
        if os.path.exists(drive_letter):
            print(f"⚠ Le lecteur {drive_letter} existe déjà")
            print("Nettoyage en cours...")
            self.unmount(drive_letter)
            time.sleep(2)
        
        # Créer la configuration rclone
        remote_name = "truenas_sftp"
        config_file = self.create_rclone_config(remote_name, host, username, password, port, rclone_path)
        
        if not config_file:
            return False
        
        # Commande rclone mount
        cmd = [
            rclone_path,
            "mount",
            f"{remote_name}:{remote_path}",
            drive_letter,
            "--vfs-cache-mode", "writes",
            "--vfs-cache-max-age", "1h",
            "--dir-cache-time", "5m",
            "--no-checksum",
            "--no-modtime"
        ]
        
        print(f"Montage en cours...")
        
        try:
            # Créer un fichier batch pour lancer rclone
            batch_file = Path(tempfile.gettempdir()) / "rclone_mount.bat"
            batch_content = f'''@echo off
title Rclone SFTP Mount - {drive_letter}
echo ============================================
echo Montage SFTP sur {drive_letter}
echo ============================================
echo.
echo Connexion à {host}:{remote_path}
echo.
echo IMPORTANT: Ne fermez pas cette fenêtre !
echo Le montage restera actif tant que cette fenêtre est ouverte.
echo.
echo Pour démonter : fermez cette fenêtre ou appuyez sur Ctrl+C
echo ============================================
echo.
"{rclone_path}" mount {remote_name}:{remote_path} {drive_letter} --vfs-cache-mode writes --vfs-cache-max-age 1h --dir-cache-time 5m --no-checksum --no-modtime
echo.
echo Le montage a été démonté.
pause
'''
            
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            # Lancer le fichier batch dans une nouvelle fenêtre qui reste ouverte
            print("Démarrage de rclone dans une nouvelle fenêtre...")
            
            process = subprocess.Popen(
                ["cmd.exe", "/c", "start", "cmd.exe", "/k", str(batch_file)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            print("Attente du montage (peut prendre 10 secondes)...")
            
            # Attendre que le montage soit prêt
            max_wait = 15
            for i in range(max_wait):
                time.sleep(1)
                if os.path.exists(drive_letter):
                    print(f"✓ Lecteur {drive_letter} détecté !")
                    break
                sys.stdout.write(f"\rAttente... {i+1}/{max_wait}s")
                sys.stdout.flush()
            
            print()  # Nouvelle ligne
            
            # Vérifier si le lecteur existe
            if os.path.exists(drive_letter):
                # Test d'accès
                try:
                    os.listdir(drive_letter)
                    print(f"✓ Partage SFTP monté avec succès sur {drive_letter}")
                    print(f"✓ Accès au lecteur confirmé")
                    print(f"\nVous pouvez maintenant accéder à vos fichiers via {drive_letter}")
                    print(f"\n⚠ IMPORTANT : Une fenêtre CMD Rclone est ouverte")
                    print(f"   >> NE LA FERMEZ PAS pour garder le montage actif <<")
                    print(f"   >> Le lecteur {drive_letter} disparaîtra si vous la fermez <<")
                    print(f"\nPour démonter proprement :")
                    print(f"   - Option 1 : Fermez la fenêtre Rclone")
                    print(f"   - Option 2 : Relancez ce script et choisissez l'option 2")
                    return True
                except Exception as e:
                    print(f"✗ Le lecteur {drive_letter} existe mais n'est pas accessible: {e}")
                    return False
            else:
                print(f"\n✗ Erreur: Le lecteur {drive_letter} n'a pas été créé")
                print(f"Vérifiez la fenêtre Rclone pour voir les erreurs")
                return False
                
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    def mount_with_net_use(self, host, username, password, remote_path="/", 
                          drive_letter=None, port=22):
        """Tente de monter via net use (solution simple mais limitée)"""
        if drive_letter is None:
            drive_letter = self.get_available_drive_letter()
            if drive_letter is None:
                print("Erreur: Aucune lettre de lecteur disponible")
                return False
        
        print(f"\n=== Montage du partage SFTP sur {drive_letter} ===")
        print("⚠ Cette méthode utilise un tunnel SSH local...")
        
        # On ne peut pas utiliser net use directement pour SFTP
        # Il faudrait un tunnel SSH
        print("❌ net use ne supporte pas SFTP directement")
        print("💡 Utilisez plutôt WinSCP, FileZilla ou configurez une clé SSH")
        return False
    
    def unmount(self, drive_letter):
        """Démonte le partage"""
        print(f"\n=== Démontage de {drive_letter} ===")
        
        # Méthode 1: Tuer tous les processus rclone
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "rclone.exe"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                print("✓ Processus rclone arrêté")
            time.sleep(2)
        except Exception as e:
            print(f"Note: {e}")
        
        # Méthode 2: Utiliser net use pour démonter
        try:
            result = subprocess.run(
                ["net", "use", drive_letter, "/delete", "/y"],
                capture_output=True,
                check=False
            )
            time.sleep(1)
        except Exception as e:
            print(f"Note: {e}")
        
        # Méthode 3: Forcer avec rmdir si c'est un point de montage vide
        try:
            if os.path.exists(drive_letter) and os.path.isdir(drive_letter):
                # Vérifier si c'est un dossier vide (point de montage orphelin)
                try:
                    if not os.listdir(drive_letter):
                        os.rmdir(drive_letter)
                except:
                    pass
        except Exception as e:
            print(f"Note: {e}")
        
        # Vérifier le résultat
        time.sleep(1)
        if not os.path.exists(drive_letter):
            print(f"✓ {drive_letter} démonté avec succès")
            return True
        else:
            print(f"⚠ {drive_letter} pourrait encore exister")
            print(f"Si le problème persiste, redémarrez votre ordinateur")
            return False


def main():
    """Fonction principale"""
    import ctypes
    
    mounter = SFTPMounterWindows()
    
    # Vérifier les droits admin pour l'installation
    if not mounter.is_winfsp_installed():
        if not mounter.is_admin():
            print("WinFsp doit être installé.")
            print("Relance avec les droits administrateur...")
            mounter.run_as_admin()
            return
    
    # Installer WinFsp si nécessaire
    if not mounter.install_dependencies():
        print("\nÉchec de l'installation des dépendances.")
        return
    
    print("\n" + "="*60)
    print("Montage SFTP sous Windows (avec mot de passe)")
    print("="*60)
    
    print("\nCe script utilise Rclone pour monter le partage SFTP.")
    print("Rclone supporte l'authentification par mot de passe.")
    
    # Menu
    print("\n1. Monter un partage SFTP")
    print("2. Démonter un partage SFTP")
    print("3. Quitter")
    
    choice = input("\nVotre choix (1-3): ")
    
    if choice == "1":
        print("\n" + "="*60)
        print("Configuration du montage SFTP")
        print("="*60)
        
        host = input("\nAdresse IP/hostname du serveur: ")
        port = input("Port SSH (22 par défaut): ") or "22"
        username = input("Nom d'utilisateur: ")
        password = input("Mot de passe: ")
        remote_path = input("Chemin distant (/ par défaut): ") or "/"
        drive_letter = input("Lettre de lecteur (vide pour auto): ") or None
        
        if drive_letter and not drive_letter.endswith(":"):
            drive_letter += ":"
        
        # Monter avec rclone
        if mounter.mount_with_rclone(host, username, password, remote_path, 
                                     drive_letter, int(port)):
            print("\n✓ Configuration terminée avec succès!")
            input("\nAppuyez sur Entrée pour continuer (le montage restera actif)...")
        else:
            print("\n✗ Échec du montage")
            print("\n💡 Alternatives recommandées :")
            print("   - WinSCP (interface graphique)")
            print("   - FileZilla (client FTP/SFTP)")
            print("   - Configuration de clés SSH avec SSHFS-Win")
            input("\nAppuyez sur Entrée pour quitter...")
    
    elif choice == "2":
        drive_letter = input("\nLettre de lecteur à démonter (ex: Z:): ")
        if not drive_letter.endswith(":"):
            drive_letter += ":"
        mounter.unmount(drive_letter)
        input("\nAppuyez sur Entrée pour quitter...")
    
    elif choice == "3":
        print("Au revoir!")
        return


if __name__ == "__main__":
    main()