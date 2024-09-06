import requests
import json

# CKAN instance URL
ckan_url = 'https://ckan.cyverse.rocks/'

# API Key
api_key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJid0tfcVU5YUdlQkxScTNuWDRZbkdfRzctRk90bUdzeDh0ZzVwM19GUWJRIiwiaWF0IjoxNzE4MDg0NDcwfQ.f1Zp-LlzrhkqBvBh-bjm7hE0oOJiXKzRutFFjg6ykfo'


def get_organizations():
    url = 'https://ckan.cyverse.rocks/api/3/action/organization_list'
    headers = {'Authorization': api_key}

    response = requests.get(url, headers=headers)
    organizations = response.json()

    return organizations


def create_dataset(data):
    """
    Create a new dataset in CKAN.

    This function sends a POST request to the CKAN API to create a new dataset with the provided metadata.
    The dataset metadata should include information such as name, title, description, owner organization,
    and any additional metadata fields.

    Args:
        data (dict): The dataset metadata dictionary, including keys like 'name', 'title', 'description',
                     'owner_org', and any additional metadata.

    Returns:
        dict: The response from the CKAN API, typically containing the dataset metadata.
    """
    url = f'{ckan_url}/api/3/action/package_create'  # API endpoint for creating a dataset
    headers = {
        'Authorization': api_key,  # API key for authorization
        'Content-Type': 'application/json'  # Content type for the request
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))  # Send POST request to create dataset
    return response.json()  # Return the JSON response from the API


def upload_resource(dataset_id, file_path, name, date_created, date_updated, description=None):
    """
    Upload a resource (file) to a CKAN dataset.

    This function uploads a file to a specified CKAN dataset by sending a POST request to the CKAN API.
    The function attaches the file and metadata such as the resource name and description.

    Args:
        dataset_id (str): The ID of the dataset to add the resource to.
        file_path (str): The local path to the file to upload.
        name (str): The name of the resource.
        description (str, optional): A brief description of the resource.
        date_created (str): The date the resource was created.
        date_updated (str): The date the resource was last updated.

    Returns:
        dict: The response from the CKAN API, typically containing the resource metadata.
    """
    url = f'{ckan_url}/api/3/action/resource_create'  # API endpoint for creating a resource
    headers = {
        'Authorization': api_key  # API key for authorization
    }
    data = {
        'package_id': dataset_id,  # ID of the dataset to add the resource to
        'name': name,  # Name of the resource
        'description': description,  # Description of the resource
        'date_created_de': date_created,  # Date the resource was created
        'date_updated_de': date_updated  # Date the resource was last updated
    }
    files = {
        'upload': open(file_path, 'rb')  # File to upload
    }
    response = requests.post(url, headers=headers, data=data, files=files)  # Send POST request to upload resource
    return response.json()  # Return the JSON response from the API


def add_resource_link(data):
    """
    Add a link to a resource in a CKAN dataset.

    This function adds a URL link to a specified CKAN dataset by sending a POST request to the CKAN API.
    This is the primary way that resources are added to CKAN datasets from the discovery environment.
    The resource metadata should include the dataset ID, URL, name, description, format, and relevant dates.

    Args:
        data (dict): The resource metadata dictionary, including keys like 'package_id', 'name', 'url',
                     'description', 'format', and relevant dates.

    Returns:
        dict: The response from the CKAN API, typically containing the resource metadata.
    """
    resource_url = f'{ckan_url}/api/3/action/resource_create'  # API endpoint for creating a resource
    headers = {
        'Authorization': api_key  # API key for authorization
    }
    response = requests.post(resource_url, headers=headers, json=data)  # Send POST request to add resource link
    return response.json()  # Return the JSON response from the API


def update_dataset_metadata(dataset_id, new_metadata):
    """
    Update the metadata of a dataset in CKAN.

    This function sends a POST request to the CKAN API to update the metadata of a specified dataset.
    The new metadata should include information such as name, title, description, owner organization,
    and any additional metadata fields.

    Args:
        dataset_id (str): The ID of the dataset to update.
        new_metadata (dict): The new metadata dictionary, including keys like 'name', 'title', 'description',
                             'owner_org', and any additional metadata.

    Returns:
        dict: The response from the CKAN API, typically containing the updated dataset metadata.
    """
    url = f'{ckan_url}/api/3/action/package_update'  # API endpoint for updating a dataset
    headers = {
        'Authorization': api_key,  # API key for authorization
        'Content-Type': 'application/json'  # Content type for the request
    }
    data = new_metadata
    data['id'] = dataset_id  # Add the dataset ID to the data
    response = requests.post(url, headers=headers, data=json.dumps(data))  # Send POST request to update dataset
    return response.json()  # Return the JSON response from the API


def get_dataset_id(dataset_name):
    """
    Get the dataset ID for a given dataset name in CKAN.

    This function retrieves the ID of a dataset by its name. It sends a GET request to the CKAN API
    to fetch the dataset metadata and extract the dataset ID.

    Args:
        dataset_name (str): The name of the dataset.

    Returns:
        str: The dataset ID if found, or None if the dataset does not exist.
    """
    # Format dataset name to match CKAN conventions
    dataset_name = dataset_name.lower().replace(' ', '-').replace('.', '-')
    url = f'{ckan_url}/api/3/action/package_show'  # API endpoint for showing dataset details
    headers = {'Authorization': api_key}  # API key for authorization
    params = {'id': dataset_name}  # Parameters for the GET request
    response = requests.get(url, headers=headers, params=params)  # Send GET request to retrieve dataset details
    if response.status_code == 200:
        dataset_metadata = response.json()  # Parse the JSON response
        if dataset_metadata['success']:
            return dataset_metadata['result']['id']  # Return dataset ID if found
        else:
            print(f"Error: {dataset_metadata['error']['message']}")  # Print error message if not successful
            return None
    elif response.status_code == 404:
        print(f"Dataset '{dataset_name}' not found.")  # Print message if dataset not found
        return None
    else:
        print(f"An error occurred: {response.status_code} - {response.text}")  # Print error message for other errors
        return None


def get_dataset_info(dataset_id):
    """
    Get detailed information about a specific dataset in CKAN.

    This function retrieves detailed metadata for a specified dataset by sending a GET request to the CKAN API.
    It is used to fetch information such as the dataset title, description, tags, resources, and other metadata.

    Args:
        dataset_id (str): The ID of the dataset to retrieve information about.

    Returns:
        dict: The response from the CKAN API, containing the dataset metadata.
    """
    url = f'{ckan_url}/api/3/action/package_show'  # API endpoint for showing dataset details
    headers = {'Authorization': api_key}  # API key for authorization
    params = {'id': dataset_id}  # Parameters for the GET request
    response = requests.get(url, headers=headers, params=params)  # Send GET request to retrieve dataset details
    return response.json()  # Return the JSON response from the API


def list_datasets(organization=None, group=None):
    """
    List all datasets in the CKAN instance for a specific organization and/or group.

    This function retrieves a list of all datasets in the CKAN instance, filtered by organization
    or group if specified. It sends multiple GET requests to the CKAN API to handle pagination and
    returns the dataset metadata. This is used in the migration process to check whether a dataset
    from the discovery environment already exists in CKAN.

    Args:
        organization (str, optional): The name or ID of the organization.
        group (str, optional): The name or ID of the group.

    Returns:
        list: A list of dictionaries, each containing the metadata of a dataset.
    """
    headers = {'Authorization': api_key}  # API key for authorization
    output = []
    limit = 100  # Number of datasets to retrieve per request
    offset = 0  # Offset for pagination

    while True:
        params = {
            'rows': limit,
            'start': offset,
        }

        # Add filters for organization and group if provided
        if organization:
            params['q'] = f'organization:{organization}'
        if group:
            params['q'] = f'groups:{group}'

        response = requests.get(f'{ckan_url}/api/3/action/package_search', headers=headers, params=params)
        response_json = response.json()

        if 'result' not in response_json or 'results' not in response_json['result']:
            break

        datasets = response_json['result']['results']
        if not datasets:
            break

        for dataset in datasets:
            output.append(get_dataset_info(dataset['id'])['result'])

        offset += limit

    return output


def delete_dataset(dataset_id):
    """
    Delete a dataset in CKAN.

    This function deletes a specified dataset by sending a POST request to the CKAN API.
    This is used in the migration script when a dataset needs to be updated or replaced.

    Args:
        dataset_id (str): The ID of the dataset to delete.

    Returns:
        dict: The response from the CKAN API.
    """
    url = f'{ckan_url}/api/3/action/package_delete'  # API endpoint for deleting a dataset
    headers = {
        'Authorization': api_key,  # API key for authorization
        'Content-Type': 'application/json'  # Content type for the request
    }
    data = {
        'id': dataset_id  # ID of the dataset to delete
    }
    # Send POST request to delete dataset
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()  # Return the JSON response from the API


def delete_all_datasets_in_organization(organization):
    """
    Delete all datasets in a specific organization in CKAN.

    This function deletes all datasets belonging to a specified organization by first listing all datasets
    in the organization and then sending a delete request for each dataset.
    This can be used to clean up existing datasets before migrating new data.

    Args:
        organization (str): The name or ID of the organization.

    Returns:
        None
    """
    # List all datasets in the organization
    datasets = list_datasets(organization=organization)
    for dataset in datasets:
        dataset_id = dataset['id']  # Get the dataset ID
        delete_response = delete_dataset(dataset_id)  # Delete the dataset

        # Print confirmation message
        print(f'Deleted dataset with ID: {dataset_id}. Response: {delete_response}')


def pretty_print(json_data):
    """
    Format and print JSON data in a readable way.

    This function formats JSON data with indentation and sorted keys to make it more readable
    when printed to the console.

    Args:
        json_data (dict): JSON data to be pretty-printed.
    """
    print(json.dumps(json_data, indent=4, sort_keys=True))
