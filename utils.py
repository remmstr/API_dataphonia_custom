import re

#ATTENTION GESTION DES CARACTERE SPECIAUX ENCORE INCOMPLETE

def normalize_bucket_name(project_id, project_name):
    """
    Génère un nom de bucket valide pour S3 à partir d'un ID et d'un nom de projet.
    
    - Remplace les caractères spéciaux par un tiret '-'.
    - Remplace les espaces et underscores '_' par '-'.
    - S'assure que tout est en minuscules.
    - Ajoute le préfixe "biophonia-[ID]-" pour respecter la nomenclature.
    
    Ex: "Super Mega (projet de test) 55" -> "biophonia-55-super-mega-projet-de-test"
    """
    # Supprime les caractères non valides
    project_name = re.sub(r"[^a-zA-Z0-9 _-]", "", project_name)
    # Remplace les espaces et les underscores par des tirets
    project_name = re.sub(r"[\s_]+", "-", project_name)
    # Passe en minuscules
    project_name = project_name.lower()
    
    return f"biophonia-0{project_id}-{project_name}"


def choisir_projet(client):
    """Permet à l'utilisateur de choisir un projet et retourne son ID et le bucket S3 corrigé."""
    projects = client.get_all_projects()
    if not projects:
        print("❌ Aucun projet trouvé.")
        return None, None

    print("\n📂 Liste des projets disponibles:")
    for i, project in enumerate(projects):
        print(f"{i + 1}. {project['name']} (ID: {project['id']})")

    try:
        project_index = int(input("\nSélectionnez un projet (numéro) : ")) - 1
        if 0 <= project_index < len(projects):
            project_id = projects[project_index]['id']
            project_name = projects[project_index]['name']
            
            # Utilise la fonction de normalisation pour générer un nom de bucket valide
            bucket_name = normalize_bucket_name(project_id, project_name)
            
            return project_id, bucket_name
        else:
            print("❌ Sélection invalide.")
            return None, None
    except ValueError:
        print("❌ Entrée invalide. Veuillez entrer un numéro valide.")
        return None, None



def choisir_fichier_dans_projet(client, project_id):
    """Permet à l'utilisateur de choisir un fichier d'un projet donné."""
    files = client.get_all_files(project_id)
    if not files:
        print("❌ Aucun fichier trouvé pour ce projet.")
        return None

    print("\n📄 Liste des fichiers disponibles:")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file['name']} (ID: {file['id']})")

    try:
        file_index = int(input("Sélectionnez un fichier (numéro) : ")) - 1
        if 0 <= file_index < len(files):
            return files[file_index]['name']
        else:
            print("❌ Sélection invalide.")
            return None
    except ValueError:
        print("❌ Entrée invalide. Veuillez entrer un numéro valide.")
        return None