import migration
import ckan
import de
import file_utils as fu


def prepare_ckan_data(metadata, owner_org, curated=False, title=None, description=None, author=None):
    """
    Prepare the dataset metadata for CKAN.
    Args:
        metadata: The metadata of the dataset from the discovery environment.
        owner_org: The organization to which the dataset belongs in CKAN.
        curated: Whether the dataset is curated.
        title: The title of the dataset.
        description: The description of the dataset.
        author: The author of the dataset.

    Returns:
        dict: The dataset metadata formatted for CKAN.
    """
    print(metadata)
    data = {
        'tags': migration.get_tags(metadata),
        'extras': migration.get_extras(metadata, curated),
        'owner_org': owner_org
    }

    if title:
        data['title'] = title
    else:
        data['title'] = migration.get_title(metadata)

    data['name'] = migration.get_name_from_title(data['title'])

    if description:
        data['notes'] = description
    else:
        data['notes'] = migration.get_description(metadata)

    if author:
        data['author'] = author
    else:
        data['author'] = migration.get_author(metadata)

    return data


def migrate_dataset_to_ckan(username, password, de_link, title, description, author, convert_csv=False):
    """
    Migrate a dataset from the Discovery Environment to CKAN with the provided metadata.
    Args:
        username: The Discovery Environment username.
        password: The Discovery Environment password.
        de_link: The link to the dataset in the Discovery Environment.
        title: The title of the dataset.
        description: The description of the dataset.
        author: The author of the dataset.
        convert_csv: Whether to convert CSV files to Parquet format.

    Returns:
        str: A message indicating the success or failure of the migration.
    """
    token = de.get_de_api_key(username, password)

    if token is None:
        return "Error obtaining DE API key. Please check username and password."

    headers = {'Authorization': f'Bearer {token}'}
    path_parts = de_link.split('/')
    directory_path = '/'.join(path_parts[:-1])

    datasets = de.get_datasets(directory_path, headers)
    for dataset in datasets:
        if dataset['path'] == de_link:
            dataset_metadata = de.get_all_metadata_dataset(dataset)
            break

    curated = "curated" in de_link
    data = prepare_ckan_data(dataset_metadata, "cyverse", curated, title, description, author)
    if curated:
        data = migration.get_license_info(data, dataset_metadata)

    dataset_response = ckan.create_dataset(data)
    if not dataset_response["success"]:
        return f"Error creating CKAN dataset: {dataset_response['error']}"
    dataset_id = dataset_response['result']['id']

    files = de.get_files(dataset_metadata['de_path'])
    num_files = files['total']
    if num_files is None:
        return

    files = de.get_files(dataset_metadata['de_path'], limit=num_files)

    # Add conversion of CSV to Parquet if requested
    if convert_csv:
        files = fu.convert_csv_to_parquet(files)

    for file in files['files']:
        file_metadata = de.get_all_metadata_file(file)
        resource_data = {
            'package_id': dataset_id,
            'name': file_metadata['file_name'],
            'description': None,
            'url': file_metadata['web_dav_location'],
            'format': file_metadata['file_type'],
            'Date created in discovery environment': file_metadata['date_created'],
            'Date last modified in discovery environment': file_metadata['date_modified']
        }
        ckan.add_resource_link(resource_data)

    for folder in files['folders']:
        folder_metadata = de.get_all_metadata_file(folder)
        resource_data = {
            'package_id': dataset_id,
            'name': folder_metadata['file_name'],
            'description': None,
            'url': folder_metadata['web_dav_location'],
            'format': 'folder',
            'Date Created in Discovery Environment': folder_metadata['date_created'],
            'Date Last Modified in Discovery Environment': folder_metadata['date_modified']
        }
        ckan.add_resource_link(resource_data)

    return "Dataset migrated to CKAN successfully."
