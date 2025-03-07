import os
import requests
import getconf
import boto3
from typing import Dict
import s3transfer
import tqdm
import boto3.s3.transfer as s3transfer
import botocore



# 🛠 Ajout des variables d'environnement pour contourner le problème d'argument invalid de PutObject
os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "when_required"
os.environ["AWS_RESPONSE_CHECKSUM_VALIDATION"] = "when_required"


class Dataphonia:
    """
    Classe pour interagir avec l'API Dataphonia et le stockage S3.
    """
    _cookies: any
    _base_url: str
    _s3_client: any
    session: requests.Session

    def __init__(self):
        config = getconf.ConfigGetter("dataphonia", ["dataphonia.env"])
        self._base_url = config.getstr("api.BASE_URL")

        # 🔹 Initialisation des cookies (Évite l'AttributeError)
        self._cookies = None
        self.session = requests.Session()

        # 🔹 Configuration des accès S3
        storage_access = config.getstr("storage.access")
        storage_secret = config.getstr("storage.secret")
        storage_host = config.getstr("storage.host")
        storage_region = config.getstr("storage.region_name")

        self._s3_client = boto3.client(
            "s3",
            aws_access_key_id=storage_access,
            aws_secret_access_key=storage_secret,
            endpoint_url=storage_host,
            region_name=storage_region
        )

        # 🔹 Connexion et récupération des cookies
        self._login(
            config.getstr("authentication.username"),
            config.getstr("authentication.password"),
        )

        # 🔹 Récupération du CSRF token après connexion
        self.csrf_token = self.session.cookies.get("csrftoken")
        if not self.csrf_token:
            print("❌ Erreur: Impossible de récupérer le token CSRF après connexion.")

    def _login(self, email: str, password: str):
        """Effectue la connexion et stocke les cookies"""
        r = self.session.post(self._base_url + "auth/login", json={"email": email, "password": password})
        if r.status_code == 200:
            self._cookies = self.session.cookies  # Stocke les cookies après connexion
        else:
            print(f"❌ Erreur lors de la connexion: {r.text}")

    def post(self, route: str, data: Dict):
        """Envoie une requête POST avec les cookies"""
        return self.session.post(self._base_url + route, json=data, cookies=self._cookies)

    def get(self, route: str):
        """Envoie une requête GET avec les cookies"""
        return self.session.get(self._base_url + route, cookies=self._cookies)

    def get_all_files(self, project_id: int):
        r = self.get(f"projects/{project_id}/files/")
        return r.json()

    def get_all_projects(self):
        r = self.get("projects/")
        return r.json()

    def upload_file(self, file_path: str, bucket_name: str, key_name: str):
        """Upload un fichier vers le stockage S3."""
        if not os.path.exists(file_path):
            print(f"❌ Erreur : Le fichier {file_path} n'existe pas.")
            return False

        try:
            # Configuration de l'upload multipart pour les fichiers volumineux
            transfer_config = s3transfer.TransferConfig(multipart_threshold=5 * 1024 * 1024)
            
            with open(file_path, "rb") as data:
                self._s3_client.upload_fileobj(
                    data,
                    bucket_name,
                    key_name,
                    ExtraArgs={"ContentType": "audio/wav"},
                    Config=transfer_config
                )
            print(f"✅ Fichier {file_path} uploadé avec succès vers {bucket_name}/{key_name}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'upload : {e}")
            return False

    def list_files_in_bucket(self, bucket_name):
        """Liste tous les fichiers présents dans le bucket."""
        response = self._s3_client.list_objects_v2(Bucket=bucket_name)
        
        if "Contents" in response:
            print("\n📂 Fichiers présents dans le bucket:")
            for obj in response["Contents"]:
                print(f"- {obj['Key']}")
        else:
            print("❌ Aucun fichier trouvé dans le bucket.")

    def download_file(self, project_id: int, bucket_name: str, file_name: str, save_path: str):
        """Télécharge un fichier depuis le serveur S3 (uniquement le projet 55)."""
        
        files = self.get_all_files(project_id)
        file_info = next((f for f in files if f['name'] == file_name), None)
        
        if not file_info:
            print("Fichier non trouvé dans le projet.")
            return False
        
        s3_key = file_info.get('s3Key')
        
        if not s3_key:
            print("Erreur: Clé S3 non trouvée pour ce fichier.")
            return False
        
        print(f"Téléchargement depuis S3 - Bucket: {bucket_name}, Key: {s3_key}")
        
        try:
            self._s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        except self._s3_client.exceptions.ClientError as e:
            print(f"Erreur lors de la vérification du fichier sur S3: {e}")
            return False

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        try:
            with open(save_path, 'wb') as file:
                self._s3_client.download_fileobj(bucket_name, s3_key, file)
            return True
        except Exception as e:
            print(f"Erreur lors du téléchargement: {e}")
            return False
