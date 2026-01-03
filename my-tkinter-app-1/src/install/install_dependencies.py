import subprocess
import sys
import os

def install_requirements():
    """Install dependencies from requirements.txt."""
    requirements_path = os.path.join(os.path.dirname(__file__), '..', '..', 'requirements.txt')
    if os.path.exists(requirements_path):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
    else:
        print(f"[ERROR] requirements.txt not found at {requirements_path}")

if __name__ == "__main__":
    install_requirements()
    print("[INFO] All dependencies are installed.")