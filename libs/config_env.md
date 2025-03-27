```bash
env="env_gps"

# Installer pip si ce n'est pas déjà fait
apt update
apt install -y python3-pip python3-venv

# Créer l'environnement virtuel s'il n'existe pas
python3 -m venv "$env"

# Activer l'environnement virtuel
source "$env/bin/activate"

# Désinstaller le paquet 'serial' s'il est installé
pip uninstall -y serial

# Installer les dépendances
pip install -r requirements.txt
```





