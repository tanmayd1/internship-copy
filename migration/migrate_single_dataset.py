import migration
import de
import ckan
import argparse
import requests
from requests.auth import HTTPBasicAuth
import json


# Function to get DE API token
def get_de_api_key(username, password):
    """
    Obtain an API key from the Discovery Environment (DE) using the username and password.

    This function sends a GET request to the DE token endpoint with HTTP basic authentication
    to retrieve an access token. The token can then be used to authorize calls to other DE API endpoints.

    Args:
        username (str): The CyVerse username.
        password (str): The CyVerse password.

    Returns:
        str: The access token for DE API.
    """
    url = 'https://de.cyverse.org/terrain/token/keycloak'
    response = requests.get(url, auth=HTTPBasicAuth(username, password))

    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token']
    else:
        print(f"Error obtaining API key: {response.status_code} - {response.text}")
        return None


# parser = argparse.ArgumentParser(description='Add a single dataset from the Data Store to a CKAN organization.')
# parser.add_argument('data_store_path', help='The absolute path to the Data Store folder containing the dataset')
# parser.add_argument('ckan_org', help='The name of the CKAN organization that owns the dataset')
# parser.add_argument('username', help='The CyVerse account username')
# parser.add_argument('password', help='The CyVerse account password')
# args = parser.parse_args()
#
# print("Absolute Path:", args.data_store_path)
# print("Name of organization:", args.ckan_org)
# print("CyVerse Username:", args.username)
# print("CyVerse Password:", args.password)
# print("\n")


def migrate_dataset(data_store_path, ckan_org, username, password):
    # Get the DE API token
    token = get_de_api_key(username, password)

    if token is None:
        raise Exception("Error obtaining DE API key")

    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Get the directory by cutting off the last part of the path
    path_parts = data_store_path.split('/')
    directory_path = '/'.join(path_parts[:-1])
    print("Directory Path:", directory_path)

    datasets = de.get_datasets(directory_path, headers)

    for dataset in datasets:
        if dataset['path'] == data_store_path:
            dataset_metadata = de.get_all_metadata_dataset(dataset)
            break

    # Migrate files to CKAN
    migration.migrate_dataset_and_files(dataset_metadata, organization=ckan_org, curated=False)

if __name__ == '__main__':
    migrate_dataset("/iplant/home/shared/aegis", "cyverse", "tanmaytest", "password123")


