import os
import requests
import getconf
import boto3
from typing import Dict

class Dataphonia:
    """
    Classe pour interagir avec l'API Dataphonia
    """
    _cookies: any
    _base_url: str
    _s3_client: any

    def __init__(self):
        config = getconf.ConfigGetter("dataphonia", ["dataphonia.env"])
        self._base_url = config.getstr("api.BASE_URL")
        
        # Configuration des accès S3
        '''
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
        '''
        
        
        self._login(
            config.getstr("authentication.username"),
            config.getstr("authentication.password"),
        )

    def _login(self, email: str, password: str):
        r = self.post("auth/login", {"email": email, "password": password})
        self._cookies = r.cookies

    def post(self, route: str, data: Dict):
        r = requests.post(self._base_url + route, json=data)
        return r

    def get(self, route: str):
        r = requests.get(self._base_url + route, cookies=self._cookies)
        return r

    def get_all_files(self, project_id: int):
        r = self.get(f"projects/{project_id}/files/")
        return r.json()

    def get_all_projects(self):
        r = self.get("projects/")
        return r.json()
    
    def upload_file(self, project_id: int, file_path: str):
        """Upload un fichier vers la plateforme"""
        url = f"{self._base_url}projects/{project_id}/upload"
        
        if not os.path.exists(file_path):
            print("Erreur: fichier non trouvé.")
            return None
        
        try:
            with open(file_path, "rb") as file:
                files = {"file": file}
                data = {"project": project_id}
                response = requests.post(url, cookies=self._cookies, files=files, data=data)
            
            if response.status_code != 200:
                print(f"Erreur lors de l'upload {response.status_code}: {response.text}")
                return None
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'upload : {e}")
            return None
    
    def download_file(self, project_id: int, file_name: str, save_path: str):
        """Télécharge un fichier depuis le serveur S3."""
        files = self.get_all_files(project_id)
        file_info = next((f for f in files if f['name'] == file_name), None)
        
        if not file_info:
            print("Fichier non trouvé dans le projet.")
            return False

        s3_key = file_info.get('s3Key')
        bucket_name = file_info.get('bucket', f"dataphonia-project-{project_id}")
        
        if not s3_key:
            print("Erreur: Clé S3 non trouvée pour ce fichier.")
            return False
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        try:
            with open(save_path, 'wb') as file:
                self._s3_client.download_fileobj(bucket_name, s3_key, file)
            print(f"Fichier téléchargé avec succès: {save_path}")
            return True
        except Exception as e:
            print(f"Erreur lors du téléchargement: {e}")
            return False
