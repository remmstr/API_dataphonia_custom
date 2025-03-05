# Utilisation de Dataphonia via API

L'API utilisée pour l'application Dataphonia est une [API Rest](https://fr.wikipedia.org/wiki/Representational_state_transfer). Elle peut aussi bien être appelée depuis l'application Dataphonia que depuis un script Python.

## Rémi -- Configuration & Lancement du code


Sur macOS et Linux :
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

Sur Windows :
```bash
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```


## Utilisation de l'API

### Principes généraux

L'idée générale est d'utiliser la bibliothèque Python `requests`. L'authentification est basée sur des 🍪 cookies.

```py
import requests

# On fait une requête pour se connecter à l'api
r = requests.post("https://dataphonia.fr/api/auth/login", { email: "mon@email.fr", password: "password"})

# On récupére les cookies de connexion
cookies = r.cookies

# On ajoute les cookies pour authentifier toute future requête
requests.get("...", cookies=cookies)
```

### Script d'exemple

Un script Python `dataphonia.py` est fourni en exemple.

Pour fonctionner, ce script a besoin d'un fichier de configuration (`.env`), vous aurez besoin d'installer `getconf` pour /Users/remimustiere/Library/Mobile Documents/com~apple~CloudDocs/LE FICHIER/03_Professionel/Biophonia/Projet_Exploration/API/biophonia/scripts/dataphonia.envl'utiliser.

```
[api]
BASE_URL = https://preprod.dataphonia.fr/api/

[authentication]
PASSWORD = yourpassword
USERNAME = youremail@biophonia.fr
```

### Les différentes routes de l'API

Vous pouvez un peu dans l'API depuis votre navigateur, par ex. https://preprod.dataphonia.fr/api/

Les routes principales sont :

- Obtenir la liste des projets `/projects/`
- Obtenir la liste des fichiers pour un projet donné `/projects/<project_id>/files/`

Ces routes sont définies dans les fichiers `back/biophonia/urls.py` et `back/biophonia/views/project_views.py`.

## Télécharger les fichiers

Les fichiers sont stockés sur le serveur s3.

Pour les télécharger vous avez besoin :

- des informations de connexion au serveur s3 ;
- du nom du bucket associé au projet (il y a un bucket par projet) : actuellement seulement visible dans l'interface Django ;
- de la clé s3 associée au projet (disponible via appel API à `/projects/<project_id>/files`)

Côté TelesCoop, on utilise `boto3` comme client s3. Un exemple d'utilisation dans le code `back/biophonia/storage.py`.
