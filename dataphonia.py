import os
import requests
import getconf
import boto3
from typing import Dict

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
    


    # === MÉTHODE : UPLOAD EN COPIANT CE QUE FAIT REQUETES SITE ===
    def upload_file_2(self, file_path):
        """Upload un fichier en suivant le bon protocole Dataphonia (Projet 55)."""

        project_id = 55  # ID fixe du projet "super-mega-projet-de-test"

        if not os.path.exists(file_path):
            print("❌ Le fichier n'existe pas.")
            return False

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        print(f"🔄 Démarrage de l'upload pour '{file_name}' ({file_size} octets)...")

        # Vérifier si les cookies sont bien récupérés
        print(f"🔍 Cookies envoyés: {self._cookies}")
        print(f"🔍 Token CSRF envoyé: {self.csrf_token}")

        # 🔹 Headers avec CSRF Token et Referer
        headers = {
            "X-CSRFTOKEN": self.csrf_token,
            "Referer": "https://dataphonia.fr/upload/55",
            "Content-Type": "application/json"
        }

        # Étape 1 : Démarrer l'upload
        start_upload_url = f"{self._base_url}projects/{project_id}/start-uploads/"
        payload = {
            "name": file_name,
            "size": file_size,
            "mime_type": "audio/wav"
        }

        start_response = self.session.post(start_upload_url, json=payload, cookies=self._cookies, headers=headers)

        if start_response.status_code != 200:
            print(f"❌ Erreur lors du démarrage de l'upload (Code {start_response.status_code}): {start_response.text}")
            return False

        upload_file_id = start_response.json().get("id")
        print(f"✅ Upload initialisé avec ID {upload_file_id}")

        # Étape 2 : Récupérer l'URL S3 signée
        get_upload_url = f"{self._base_url}projects/{project_id}/upload-url/?upload_file={upload_file_id}"
        upload_url_response = self.session.get(get_upload_url, cookies=self._cookies, headers=headers)

        if upload_url_response.status_code != 200:
            print(f"❌ Erreur en récupérant l'URL S3: {upload_url_response.text}")
            return False

        upload_url = upload_url_response.json().get("upload_url")
        print(f"🔗 URL S3 obtenue : {upload_url}")

        # Étape 3 : Upload du fichier vers S3
        with open(file_path, "rb") as file:
            s3_response = requests.put(upload_url, data=file)

        if s3_response.status_code != 200:
            print(f"❌ Échec de l'upload S3: {s3_response.text}")
            return False

        print(f"✅ Fichier envoyé avec succès vers S3 !")

        # Étape 4 : Finalisation de l'upload
        finalize_url = f"{self._base_url}upload-files/{upload_file_id}/"
        finalize_payload = {"status": "completed"}

        finalize_response = self.session.patch(finalize_url, json=finalize_payload, cookies=self._cookies, headers=headers)

        if finalize_response.status_code == 200:
            print(f"✅ Upload finalisé avec succès !")
            return True
        else:
            print(f"❌ Erreur lors de la finalisation: {finalize_response.text}")
            return False
        
        
    
    # === OLD MÉTHODE : UPLOAD DIRECTEMENT VERS S3 ===
    def upload_file_1(self, file_path: str):
        """Upload un fichier dans le serveur S3 du projet 55 ('super-mega-projet-de-test')."""
        
        project_id = 55  # ID fixe du projet
        bucket_name = "biophonia-055-super-mega-projet-de-test"
        
        # Vérification de l'existence du fichier
        if not os.path.exists(file_path):
            print("Erreur: fichier non trouvé.")
            return False

        file_name = os.path.basename(file_path)  # Récupération du nom du fichier
        
        try:
            # Vérification de l'existence du fichier avant upload
            try:
                self._s3_client.head_object(Bucket=bucket_name, Key=file_name)
                print(f"Le fichier '{file_name}' existe déjà sur S3.")
                return False
            except self._s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] != '404':
                    print(f"Erreur lors de la vérification sur S3: {e}")
                    return False

            print(f"Envoi du fichier '{file_name}' vers le bucket S3 '{bucket_name}'...")

            # Upload du fichier vers S3
            self._s3_client.upload_file(file_path, bucket_name, file_name,ExtraArgs={'ContentType': 'audio/wav'})

            print(f"Fichier '{file_name}' uploadé avec succès dans 'super-mega-projet-de-test'.")
            return True

        except Exception as e:
            print(f"Erreur lors de l'upload: {e}")
            return False
    


    # === NOUVELLE MÉTHODE : UPLOAD DIRECTEMENT VERS S3 ===
    def upload_file_s3_1bis(self, file_path: str):
        """
        Upload un fichier directement vers S3 sans passer par Dataphonia.
        """

        if not os.path.exists(file_path):
            print("❌ Erreur: Fichier non trouvé.")
            return False

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        print(f"🔄 Envoi de '{file_name}' ({file_size} octets) vers S3...")

        try:
            bucket_name = "biophonia-055-super-mega-projet-de-test"

            # Vérifier si le fichier existe déjà sur S3
            try:
                self._s3_client.head_object(Bucket=bucket_name, Key=file_name)
                print(f"⚠️ Le fichier '{file_name}' existe déjà sur S3. Upload annulé.")
                return False
            except self._s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] != '404':
                    print(f"Erreur lors de la vérification sur S3: {e}")
                    return False  # Erreur inattendue

            # 📌 Ajout de ContentType pour corriger l'erreur InvalidArgument
            self._s3_client.upload_file(
                file_path, bucket_name, file_name,
                ExtraArgs={'ContentType': 'audio/wav'}  # 🔹 Ajout du ContentType correct
            )

            print(f"✅ Fichier '{file_name}' uploadé avec succès sur S3.")

            return True

        except Exception as e:
            print(f"❌ Erreur lors de l'upload: {e}")
            return False

    def download_file(self, project_id: int, file_name: str, save_path: str):
        """Télécharge un fichier depuis le serveur S3 (uniquement le projet 55)."""
        
        files = self.get_all_files(project_id)
        file_info = next((f for f in files if f['name'] == file_name), None)
        
        if not file_info:
            print("Fichier non trouvé dans le projet.")
            return False
        
        s3_key = file_info.get('s3Key')
        bucket_name = "biophonia-055-super-mega-projet-de-test"
        
        if not s3_key:
            print("Erreur: Clé S3 non trouvée pour ce fichier.")
            return False
        
        print(f"Téléchargement depuis S3 - Bucket: {bucket_name}, Key: {s3_key}")
        
        try:
            self._s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        except self._s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                print("Erreur: Fichier non trouvé sur S3.")
                return False
            else:
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


