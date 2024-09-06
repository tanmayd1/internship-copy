import json
import tempfile
import os
import croissant
import dcat
import de
import migration
import pandas as pd
import requests
from io import BytesIO
from tempfile import gettempdir


def extract_metadata(json_data):
    """
    Extracts metadata from a given JSON object.

    Args:
        json_data (dict): JSON data containing metadata information.

    Returns:
        dict: A dictionary containing extracted metadata.
    """
    metadata = {
        'title': json_data.get('title', 'Untitled'),
        'description': json_data.get('description', 'No description provided.'),
        'author': json_data.get('author', 'Unknown author'),
        'keywords': json_data.get('keyword', []),
        'publisher': json_data.get('publisher', {}).get('name', 'Unknown publisher'),
        'date_published': json_data.get('datePublished', 'Unknown date'),
        'license_url': json_data.get('license', 'No license specified')
    }
    return metadata


def generate_croissant_json(username, password, de_link, title, description, author):
    """
    Generates a Croissant JSON-LD file for a dataset.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.
        de_link (str): The Discovery Environment link to the dataset.
        title (str): The title of the dataset.
        description (str): The description of the dataset.
        author (str): The author of the dataset.

    Returns:
        str: The path to the generated Croissant JSON-LD file or an error message.
    """
    # Obtain DE API token
    token = de.get_de_api_key(username, password)
    if token is None:
        return "Error obtaining DE API key. Please check username and password."

    # Set up headers for authorization
    headers = {'Authorization': f'Bearer {token}'}
    path_parts = de_link.split('/')
    directory_path = '/'.join(path_parts[:-1])  # Get directory path

    # Get datasets from the directory
    datasets = de.get_datasets(directory_path, headers)
    for dataset in datasets:
        if dataset['path'] == de_link:
            dataset_metadata = de.get_all_metadata_dataset(dataset)
            break

    if not title:
        title = migration.get_title(dataset_metadata)

    if not description:
        description = migration.get_description(dataset_metadata)

    if not author:
        author = migration.get_author(dataset_metadata)

    # Extract keywords from dataset metadata
    keywords = []
    if 'subject' in dataset_metadata:
        subjects = dataset_metadata['subject']
        if isinstance(subjects, str):
            subjects = (subjects.replace("(", "")
                        .replace(")", "")
                        .replace("&", "-")
                        .split(','))
            keywords = [subject for subject in subjects]
        else:
            keywords = [subject
                        .replace("(", "")
                        .replace(")", "")
                        .replace("&", "-")
                        .replace("#", "-")
                        for subject in subjects]
            for tag in keywords:
                if ', ' in tag:
                    keywords.remove(tag)
                    keywords += [{'name': t.strip()} for t in tag.split(',')]

    # Get dataset version
    version = dataset_metadata.get('version', dataset_metadata.get('Version', ''))

    # Get list of files in the dataset
    files = de.get_files(dataset_metadata['de_path'])
    num_files = files['total']
    distributions = []
    if num_files is not None:
        files = de.get_files(dataset_metadata['de_path'], limit=num_files)
        for file in files['files']:
            file_metadata = de.get_all_metadata_file(file)
            distribution = croissant.create_distribution(file_metadata['file_name'],
                                                         file_metadata['file_type'],
                                                         file_metadata['web_dav_location'])
            distributions.append(distribution)

    # Create Croissant JSON-LD
    croissant_json = croissant.create_croissant_jsonld(title, description, author,
                                                       keywords=keywords, version=version,
                                                       distributions=distributions)
    temp_dir = tempfile.gettempdir()  # Get temporary directory
    output_filename = os.path.join(temp_dir, "croissant.json")
    with open(output_filename, "w") as f:
        json.dump(croissant_json, f, indent=4)

    return output_filename


def generate_dcat_json(username, password, de_link, title, description, author):
    """
    Generates a DCAT JSON-LD file for a dataset.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.
        de_link (str): The Discovery Environment link to the dataset.
        title (str): The title of the dataset.
        description (str): The description of the dataset.
        author (str): The author of the dataset.

    Returns:
        str: The path to the generated DCAT JSON-LD file or an error message.
    """
    # Obtain DE API token
    token = de.get_de_api_key(username, password)
    if token is None:
        return "Error obtaining DE API key. Please check username and password."

    # Set up headers for authorization
    headers = {'Authorization': f'Bearer {token}'}
    path_parts = de_link.split('/')
    directory_path = '/'.join(path_parts[:-1])  # Get directory path

    # Get datasets from the directory
    datasets = de.get_datasets(directory_path, headers)
    for dataset in datasets:
        if dataset['path'] == de_link:
            dataset_metadata = de.get_all_metadata_dataset(dataset)
            break

    if not title:
        title = migration.get_title(dataset_metadata)

    if not description:
        description = migration.get_description(dataset_metadata)

    if not author:
        author = migration.get_author(dataset_metadata)

    # Extract keywords from dataset metadata
    keywords = []
    if 'subject' in dataset_metadata:
        subjects = dataset_metadata['subject']
        if isinstance(subjects, str):
            subjects = (subjects.replace("(", "")
                        .replace(")", "")
                        .replace("&", "-")
                        .split(','))
            keywords = [subject for subject in subjects]
        else:
            keywords = [subject.replace("(", "")
                        .replace(")", "").replace("&", "-")
                        .replace("#", "-")
                        for subject in subjects]
            for tag in keywords:
                if ', ' in tag:
                    keywords.remove(tag)
                    keywords += [{'name': t.strip()} for t in tag.split(',')]

    # Get dataset version
    version = dataset_metadata.get('version', dataset_metadata.get('Version', ''))

    # Get list of files in the dataset
    files = de.get_files(dataset_metadata['de_path'])
    num_files = files['total']
    distributions = []
    if num_files is not None:
        files = de.get_files(dataset_metadata['de_path'], limit=num_files)
        for file in files['files']:
            file_metadata = de.get_all_metadata_file(file)
            distribution = dcat.create_distribution(file_metadata['file_name'],
                                                    file_metadata['file_type'],
                                                    file_metadata['web_dav_location'])
            distributions.append(distribution)

    # Create DCAT JSON-LD
    dcat_json = dcat.create_dcat_jsonld(title, description, author,
                                        keywords=keywords, version=version,
                                        distributions=distributions)
    temp_dir = tempfile.gettempdir()  # Get temporary directory
    output_filename = os.path.join(temp_dir, "dcat.json")
    with open(output_filename, "w") as f:
        json.dump(dcat_json, f, indent=4)

    return output_filename


# Function to convert CSV to Parquet
def convert_csv_to_parquet(files):
    """
    Convert CSV files to Parquet format.
    Args:
        files: The list of files to be converted.

    Returns:
        list: The list of files with CSV files converted to Parquet.
    """
    parquet_files = []

    for file in files['files']:
        if file['file_type'] == 'csv':
            csv_url = file['web_dav_location']
            response = requests.get(csv_url)
            csv_data = pd.read_csv(BytesIO(response.content))
            parquet_filename = file['file_name'].replace('.csv', '.parquet')
            parquet_filepath = os.path.join(gettempdir(), parquet_filename)
            csv_data.to_parquet(parquet_filepath)
            file['web_dav_location'] = parquet_filepath
            file['file_type'] = 'parquet'
            parquet_files.append(file)
    return parquet_files
