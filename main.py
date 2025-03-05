import os
from dataphonia import Dataphonia

def afficher_metadonnees(client):
    projects = client.get_all_projects()
    if not projects:
        print("Aucun projet trouvé.")
        return
    
    print("Liste des projets disponibles:")
    for i, project in enumerate(projects):
        print(f"{i + 1}. {project['name']} (ID: {project['id']})")
    
    try:
        project_index = int(input("Sélectionnez un projet (numéro) : ")) - 1
        if project_index < 0 or project_index >= len(projects):
            print("Sélection invalide.")
            return
    except ValueError:
        print("Entrée invalide. Veuillez entrer un numéro valide.")
        return
    
    project_id = projects[project_index]['id']
    files = client.get_all_files(project_id)
    if not files:
        print("Aucun fichier trouvé pour ce projet.")
        return
    
    print("Liste des fichiers disponibles:")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file['name']} (ID: {file['id']})")
    
    try:
        file_index = int(input("Sélectionnez un fichier (numéro) : ")) - 1
        if file_index < 0 or file_index >= len(files):
            print("Sélection invalide.")
            return
    except ValueError:
        print("Entrée invalide. Veuillez entrer un numéro valide.")
        return
    
    file_selected = files[file_index]
    metadata = file_selected.get("metadata")
    if not metadata:
        print(f"Aucune métadonnée disponible pour {file_selected['name']}.")
        return
    
    print(f"Méta-données du fichier {file_selected['name']}:")
    for key, value in metadata.items():
        print(f"{key}: {value}")

def uploader_fichier(client):
    projects = client.get_all_projects()
    if not projects:
        print("Aucun projet trouvé.")
        return
    
    print("Liste des projets disponibles:")
    for i, project in enumerate(projects):
        print(f"{i + 1}. {project['name']} (ID: {project['id']})")
    
    try:
        project_index = int(input("Sélectionnez un projet (numéro) : ")) - 1
        if project_index < 0 or project_index >= len(projects):
            print("Sélection invalide.")
            return
    except ValueError:
        print("Entrée invalide. Veuillez entrer un numéro valide.")
        return
    
    project_id = projects[project_index]['id']
    file_path = input("Entrez le chemin du fichier à uploader : ")
    if not os.path.exists(file_path):
        print("Le fichier spécifié n'existe pas.")
        return
    
    try:
        response = client.upload_file(project_id, file_path)
        if response:
            print("Fichier uploadé avec succès.")
        else:
            print("Échec de l'upload.")
    except PermissionError:
        print("Erreur de permission. Vérifiez vos droits d'accès au fichier.")

def telecharger_fichier(client):
    projects = client.get_all_projects()
    if not projects:
        print("Aucun projet trouvé.")
        return
    
    print("Liste des projets disponibles:")
    for i, project in enumerate(projects):
        print(f"{i + 1}. {project['name']} (ID: {project['id']})")
    
    try:
        project_index = int(input("Sélectionnez un projet (numéro) : ")) - 1
        if project_index < 0 or project_index >= len(projects):
            print("Sélection invalide.")
            return
    except ValueError:
        print("Entrée invalide. Veuillez entrer un numéro valide.")
        return
    
    project_id = projects[project_index]['id']
    all_files = client.get_all_files(project_id)
    if not all_files:
        print("Aucun fichier disponible pour le téléchargement.")
        return
    
    print("Liste des fichiers disponibles pour téléchargement:")
    for i, file in enumerate(all_files):
        print(f"{i + 1}. {file['name']}")
    
    try:
        file_index = int(input("Sélectionnez un fichier à télécharger (numéro) : ")) - 1
        if file_index < 0 or file_index >= len(all_files):
            print("Sélection invalide.")
            return
    except ValueError:
        print("Entrée invalide. Veuillez entrer un numéro valide.")
        return
    
    file_name = all_files[file_index]['name']
    os.makedirs("downloads", exist_ok=True)
    save_path = os.path.join("downloads", file_name)
    
    try:
        if client.download_file(project_id, file_name, save_path):
            print(f"Fichier téléchargé avec succès: {save_path}")
        else:
            print("Le téléchargement a échoué.")
    except FileNotFoundError:
        print("Erreur: Chemin de sauvegarde invalide.")

def main():

    client = Dataphonia()
    
    while True:
        print("\n---------------------- Menu --------------------------")
        print("1. Afficher les métadonnées d'un fichier")
        print("2. Uploader un fichier")
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
            print("Au revoir!")
            break
        else:
            print("Option invalide, veuillez réessayer.")

if __name__ == "__main__":
    main()
