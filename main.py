import os

from API_dataphonia_custom.dataphonia import Dataphonia
from API_dataphonia_custom.utils import choisir_projet, choisir_fichier_dans_projet, normalize_bucket_name



def afficher_metadonnees(client):
    """Affiche les métadonnées d'un fichier dans un projet sélectionné."""
    project_id, project_name = choisir_projet(client)
    if not project_id:
        return

    file_name = choisir_fichier_dans_projet(client, project_id)
    if not file_name:
        return

    files = client.get_all_files(project_id)
    file_selected = next((f for f in files if f["name"] == file_name), None)

    metadata = file_selected.get("metadata", {})
    print(f"\n📝 Métadonnées du fichier {file_selected['name']} dans {project_name}:")
    if not metadata:
        print("❌ Aucune métadonnée disponible.")
    else:
        for key, value in metadata.items():
            print(f"{key}: {value}")


def parcourir_et_uploader(client, directory, bucket_name):
    """Parcourt un répertoire et upload tous les fichiers trouvés vers S3."""
    if not os.path.exists(directory):
        print(f"❌ Le dossier {directory} n'existe pas.")
        return

    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("."):  # Ignore les fichiers système comme .DS_Store sur macOS
                continue

            file_path = os.path.join(root, file)
            key_name = os.path.relpath(file_path, start=directory)

            print(f"📤 Upload du fichier : {file_path} → S3: {bucket_name}/{key_name}")
            client.upload_file(file_path, bucket_name, key_name)


def uploader_fichier(client):
    """Upload d'un fichier ou dossier après choix du projet"""
    project_id, bucket_name = choisir_projet(client)
    if not project_id or not bucket_name:
        return

    choix = input("\nVoulez-vous uploader (1) un fichier ou (2) un dossier ? ")

    if choix == "1":
        file_path = input("Entrez le chemin du fichier à uploader : ")
        if not os.path.isfile(file_path):
            print("❌ Le fichier spécifié n'existe pas.")
            return

        key_name = os.path.basename(file_path)  # Nom du fichier comme clé S3

        if client.upload_file(file_path, bucket_name, key_name):
            print(f"✅ Fichier {file_path} uploadé avec succès dans {bucket_name}/{key_name}.")
        else:
            print("❌ Échec de l'upload.")

    elif choix == "2":
        dir_path = input("Entrez le chemin du dossier contenant les fichiers à uploader : ")
        parcourir_et_uploader(client, dir_path, bucket_name)

    else:
        print("❌ Option invalide.")



def telecharger_fichier(client):
    """Télécharge un fichier depuis un projet sélectionné."""
    project_id, bucket_name = choisir_projet(client)
    if not project_id:
        return

    file_name = choisir_fichier_dans_projet(client, project_id)
    if not file_name:
        return

    save_dir = "downloads"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, file_name)

    try:
        if client.download_file(project_id,bucket_name, file_name, save_path):
            print(f"✅ Fichier téléchargé avec succès: {save_path}")
        else:
            print("❌ Le téléchargement a échoué.")
    except FileNotFoundError:
        print("❌ Erreur: Chemin de sauvegarde invalide.")


def main():
    """Menu principal"""
    client = Dataphonia()  # Connexion gérée dans `dataphonia.py`

    while True:
        print("\n---------------------- Menu --------------------------")
        print("1. Afficher les métadonnées d'un fichier")
        print("2. Uploader un fichier ou un dossier")
        print("3. Télécharger un fichier")
        print("4. Quitter")

        choix = input("Choisissez une option : ")
        if choix == "1":
            afficher_metadonnees(client)
        elif choix == "2":
            uploader_fichier(client)
        elif choix == "3":
            telecharger_fichier(client)
        elif choix == "4":
            print("👋 Au revoir!")
            break
        else:
            print("❌ Option invalide, veuillez réessayer.")


if __name__ == "__main__":
    main()
