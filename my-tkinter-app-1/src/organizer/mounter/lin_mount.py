#!/usr/bin/env python3
import subprocess
import os
import sys
import shutil
from pathlib import Path

class SFTPMounterLinux:
    def __init__(self):
        self.package_manager = self.detect_package_manager()
        
    def detect_package_manager(self):
        """Détecte le gestionnaire de paquets de la distribution"""
        if shutil.which("apt-get"):
            return "apt"
        elif shutil.which("dnf"):
            return "dnf"
        elif shutil.which("yum"):
            return "yum"
        elif shutil.which("pacman"):
            return "pacman"
        elif shutil.which("zypper"):
            return "zypper"
        else:
            return None
    
    def is_root(self):
        """Vérifie si le script tourne en root"""
        return os.geteuid() == 0
    
    def run_as_root(self):
        """Relance le script avec sudo"""
        if not self.is_root():
            print("Les permissions root sont nécessaires pour l'installation.")
            print("Relance avec sudo...")
            os.execvp("sudo", ["sudo", "python3"] + sys.argv)
    
    def is_sshfs_installed(self):
        """Vérifie si sshfs est installé"""
        return shutil.which("sshfs") is not None
    
    def is_fuse_installed(self):
        """Vérifie si FUSE est installé"""
        return os.path.exists("/dev/fuse")
    
    def install_sshfs(self):
        """Installe sshfs selon la distribution"""
        if self.is_sshfs_installed():
            print("✓ sshfs déjà installé")
            return True
        
        print("\n=== Installation de sshfs ===")
        
        if not self.is_root():
            self.run_as_root()
        
        commands = {
            "apt": ["apt-get", "update", "&&", "apt-get", "install", "-y", "sshfs"],
            "dnf": ["dnf", "install", "-y", "fuse-sshfs"],
            "yum": ["yum", "install", "-y", "fuse-sshfs"],
            "pacman": ["pacman", "-S", "--noconfirm", "sshfs"],
            "zypper": ["zypper", "install", "-y", "sshfs"]
        }
        
        if self.package_manager not in commands:
            print(f"Gestionnaire de paquets non supporté: {self.package_manager}")
            print("Veuillez installer 'sshfs' manuellement.")
            return False
        
        try:
            if self.package_manager == "apt":
                # Pour apt, on fait deux commandes séparées
                subprocess.run(["apt-get", "update"], check=True)
                subprocess.run(["apt-get", "install", "-y", "sshfs"], check=True)
            else:
                cmd = commands[self.package_manager]
                subprocess.run(cmd, check=True)
            
            print("✓ sshfs installé avec succès")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'installation: {e}")
            return False
    
    def create_mount_point(self, path):
        """Crée le point de montage s'il n'existe pas"""
        mount_path = Path(path).expanduser()
        if not mount_path.exists():
            try:
                mount_path.mkdir(parents=True, exist_ok=True)
                print(f"✓ Point de montage créé: {mount_path}")
                return True
            except PermissionError:
                print(f"Erreur: Permission refusée pour créer {mount_path}")
                return False
        else:
            print(f"✓ Point de montage existe: {mount_path}")
            return True
    
    def is_mounted(self, mount_point):
        """Vérifie si un point de montage est déjà utilisé"""
        try:
            result = subprocess.run(
                ["mountpoint", "-q", str(mount_point)],
                capture_output=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def mount_sftp(self, host, username, password, remote_path="/", 
                   mount_point=None, port=22):
        """Monte le partage SFTP"""
        if mount_point is None:
            mount_point = Path.home() / "sftp_mount"
        else:
            mount_point = Path(mount_point).expanduser()
        
        # Créer le point de montage
        if not self.create_mount_point(mount_point):
            return False
        
        # Vérifier si déjà monté
        if self.is_mounted(mount_point):
            print(f"Attention: {mount_point} est déjà monté")
            response = input("Démonter et remonter? (o/n): ")
            if response.lower() == 'o':
                self.unmount_sftp(mount_point)
            else:
                return False
        
        print(f"\n=== Montage du partage SFTP sur {mount_point} ===")
        
        # Options de montage
        options = [
            "password_stdin",
            "StrictHostKeyChecking=no",
            "UserKnownHostsFile=/dev/null",
            f"port={port}",
            "reconnect",
            "ServerAliveInterval=15",
            "ServerAliveCountMax=3"
        ]
        
        # Construire la commande
        cmd = [
            "sshfs",
            f"{username}@{host}:{remote_path}",
            str(mount_point),
            "-o", ",".join(options)
        ]
        
        try:
            # Utiliser echo pour passer le mot de passe via pipe
            echo_process = subprocess.Popen(
                ["echo", password],
                stdout=subprocess.PIPE
            )
            
            sshfs_process = subprocess.Popen(
                cmd,
                stdin=echo_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            echo_process.stdout.close()
            stdout, stderr = sshfs_process.communicate(timeout=15)
            
            if sshfs_process.returncode == 0:
                print(f"✓ Partage SFTP monté avec succès sur {mount_point}")
                print(f"Vous pouvez maintenant accéder à vos fichiers via: {mount_point}")
                
                # Vérifier que c'est bien monté
                if self.is_mounted(mount_point):
                    return True
                else:
                    print("Avertissement: Le montage semble avoir échoué silencieusement")
                    return False
            else:
                error_msg = stderr.decode() if stderr else "Erreur inconnue"
                print(f"Erreur lors du montage: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            print("Erreur: Timeout lors de la connexion")
            sshfs_process.kill()
            return False
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    def unmount_sftp(self, mount_point):
        """Démonte le partage SFTP"""
        mount_point = Path(mount_point).expanduser()
        
        print(f"\n=== Démontage de {mount_point} ===")
        
        if not self.is_mounted(mount_point):
            print(f"{mount_point} n'est pas monté")
            return True
        
        try:
            # Essayer fusermount d'abord (méthode recommandée)
            result = subprocess.run(
                ["fusermount", "-u", str(mount_point)],
                capture_output=True
            )
            
            if result.returncode == 0:
                print(f"✓ {mount_point} démonté avec succès")
                return True
            else:
                # Fallback sur umount
                result = subprocess.run(
                    ["umount", str(mount_point)],
                    capture_output=True
                )
                if result.returncode == 0:
                    print(f"✓ {mount_point} démonté avec succès")
                    return True
                else:
                    print(f"Erreur lors du démontage: {result.stderr.decode()}")
                    return False
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    def create_fstab_entry(self, host, username, remote_path, mount_point, port=22):
        """Crée une entrée dans /etc/fstab pour montage automatique au démarrage"""
        if not self.is_root():
            print("Les permissions root sont nécessaires pour modifier /etc/fstab")
            return False
        
        fstab_line = (
            f"{username}@{host}:{remote_path} {mount_point} fuse.sshfs "
            f"noauto,x-systemd.automount,_netdev,users,idmap=user,"
            f"IdentityFile=/home/{username}/.ssh/id_rsa,allow_other,"
            f"reconnect,port={port} 0 0"
        )
        
        print("\nLigne à ajouter à /etc/fstab:")
        print(fstab_line)
        print("\nNote: Ceci nécessite une clé SSH configurée (sans mot de passe)")
        
        response = input("\nAjouter cette ligne à /etc/fstab? (o/n): ")
        if response.lower() == 'o':
            try:
                with open('/etc/fstab', 'a') as f:
                    f.write(f"\n# SFTP mount ajouté par script\n")
                    f.write(fstab_line + "\n")
                print("✓ Entrée ajoutée à /etc/fstab")
                return True
            except Exception as e:
                print(f"Erreur: {e}")
                return False
        return False


def main():
    """Fonction principale"""
    mounter = SFTPMounterLinux()
    
    print("="*60)
    print("Montage automatique SFTP sous Linux")
    print("="*60)
    
    # Installer sshfs si nécessaire
    if not mounter.install_sshfs():
        print("\nÉchec de l'installation de sshfs.")
        return
    
    print("\n" + "="*60)
    print("Configuration du montage SFTP")
    print("="*60)
    
    # Menu principal
    print("\nOptions:")
    print("1. Monter un partage SFTP")
    print("2. Démonter un partage SFTP")
    print("3. Quitter")
    
    choice = input("\nVotre choix (1-3): ")
    
    if choice == "1":
        # Demander les informations de connexion
        host = input("\nAdresse IP/hostname du serveur: ")
        port = input("Port SSH (22 par défaut): ") or "22"
        username = input("Nom d'utilisateur: ")
        password = input("Mot de passe: ")
        remote_path = input("Chemin distant (/ par défaut): ") or "/"
        mount_point = input(f"Point de montage (~/sftp_mount par défaut): ") or None
        
        # Monter le partage
        if mounter.mount_sftp(host, username, password, remote_path, 
                             mount_point, int(port)):
            print("\n✓ Configuration terminée avec succès!")
            
            # Proposer l'ajout au fstab
            response = input("\nVoulez-vous configurer le montage automatique au démarrage? (o/n): ")
            if response.lower() == 'o':
                actual_mount = mount_point if mount_point else str(Path.home() / "sftp_mount")
                mounter.create_fstab_entry(host, username, remote_path, 
                                          actual_mount, int(port))
        else:
            print("\n✗ Échec du montage")
    
    elif choice == "2":
        mount_point = input("\nPoint de montage à démonter: ")
        mounter.unmount_sftp(mount_point)
    
    elif choice == "3":
        print("Au revoir!")
        return
    
    else:
        print("Choix invalide")


if __name__ == "__main__":
    main()