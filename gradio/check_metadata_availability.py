import de
import migration


def check_metadata_availability(de_link, username, password):
    """
    Check the availability of metadata fields in a dataset, specifically title, author, and description.
    Used to ensure that the most important pieces of metadata are available
    for migration or for generating a Croissant/DCAT JSON-LD file.
    Args:
        de_link: The link to the dataset in the Discovery Environment.
        username: The CyVerse username.
        password: The CyVerse password.

    Returns:
        dict: A dictionary indicating the availability of metadata fields.
    """
    token = de.get_de_api_key(username, password)
    if token is None:
        return "Error obtaining DE API key. Please check username and password."

    headers = {'Authorization': f'Bearer {token}'}
    path_parts = de_link.split('/')
    directory_path = '/'.join(path_parts[:-1])

    datasets = de.get_datasets(directory_path, headers)
    if datasets is None:
        return "Error obtaining datasets from the Discovery Environment."

    for dataset in datasets:
        if dataset['path'] == de_link:
            dataset_metadata = de.get_all_metadata_dataset(dataset)
            break

    return_dict = {}

    # Check the availability of title, author, and description
    try:
        migration.get_title(dataset_metadata)
        return_dict["title"] = True
    except Exception:
        return_dict["title"] = False

    try:
        migration.get_author(dataset_metadata)
        return_dict["author"] = True
    except Exception:
        return_dict["author"] = False

    try:
        migration.get_description(dataset_metadata)
        return_dict["description"] = True
    except Exception:
        return_dict["description"] = False

    return return_dict
