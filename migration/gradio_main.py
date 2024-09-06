import gradio as gr
import json
# import de
import ckan
# import migration
from mlcroissant import Dataset
import logging
import io
import tempfile
import os
from gradio import dcat, croissant
import gradio.validate_dcat_json as validate_dcat_json

# Placeholder function to check metadata availability
def check_metadata_availability(de_link, username, password):
    # Get the DE API token
    token = de.get_de_api_key(username, password)
    print("token: ", token)

    if token is None:
        return "Error obtaining DE API key. Please check username and password."

    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Get the directory by cutting off the last part of the path
    path_parts = de_link.split('/')
    directory_path = '/'.join(path_parts[:-1])
    print("Directory Path:", directory_path)

    datasets = de.get_datasets(directory_path, headers)
    if datasets is None:
        return "Error obtaining datasets from the Discovery Environment."

    for dataset in datasets:
        if dataset['path'] == de_link:
            dataset_metadata = de.get_all_metadata_dataset(dataset)
            break

    de.pretty_print(dataset_metadata)

    return_dict = {}

    try:
        title = migration.get_title(dataset_metadata)
        return_dict["title"] = True
    except Exception as e:
        return_dict["title"] = False

    try:
        author = migration.get_author(dataset_metadata)
        return_dict["author"] = True
    except Exception as e:
        return_dict["author"] = False

    try:
        description = migration.get_description(dataset_metadata)
        return_dict["description"] = True
    except Exception as e:
        return_dict["description"] = False

    print(return_dict)

    return return_dict

def migrate_dataset_to_ckan(username, password, de_link, title, description, author):
    # Logic to migrate the dataset to CKAN
    token = de.get_de_api_key(username, password)

    if token is None:
        return "Error obtaining DE API key. Please check username and password."

    headers = {
        'Authorization': f'Bearer {token}'
    }

    path_parts = de_link.split('/')
    directory_path = '/'.join(path_parts[:-1])
    print("Directory Path:", directory_path)

    datasets = de.get_datasets(directory_path, headers)

    for dataset in datasets:
        if dataset['path'] == de_link:
            de.pretty_print(dataset)
            dataset_metadata = de.get_all_metadata_dataset(dataset)
            break

    de.pretty_print(dataset_metadata)

    curated = "curated" in de_link

    data = {
        'owner_org': "cyverse",
        'private': False,
        'extras': migration.get_extras(dataset_metadata, curated=curated)
    }

    if title:
        data['title'] = title
    else:
        title = migration.get_title(dataset_metadata)
        data['title'] = migration.get_title(dataset_metadata)

    # Set the 'name' key to the title of the dataset with unallowed characters replaced
    name = (title.lower().replace(' ', '-').replace('(', '').replace(')', '')
            .replace('.', '-').replace('"', '').replace('/', '-')
            .replace(',', '').replace(':', '').replace("*", "-")
            .replace("'", "-").replace('&', '-').replace("’", "-"))
    # If the length of the name is greater than 100, truncate it to 100 characters
    if len(name) > 100:
        name = name[:100]
    data['name'] = name

    if description:
        data['notes'] = description
    else:
        data['notes'] = migration.get_description(dataset_metadata)

    if author:
        data['author'] = author
    else:
        data['author'] = migration.get_author(dataset_metadata)

    if curated:
        # Try-Except block to check whether the key is 'rights' or 'Rights' in the dataset metadata
        try:
            # Set the keys for the license depending on the license specified in the dataset metadata
            if "ODC PDDL" in dataset_metadata['rights']:
                data['license_id'] = "odc-pddl"
                data['license_title'] = "Open Data Commons Public Domain Dedication and License (PDDL)"
                data['license_url'] = "http://www.opendefinition.org/licenses/odc-pddl"
            elif "CC0" in dataset_metadata['rights']:
                data['license_id'] = "cc-zero"
                data['license_title'] = "Creative Commons CCZero"
                data['license_url'] = "http://www.opendefinition.org/licenses/cc-zero"
            else:
                data['license_id'] = "notspecified"
                data['license_title'] = "License not specified"
        except KeyError:
            # Set the keys for the license depending on the license specified in the dataset metadata
            if "ODC PDDL" in dataset_metadata['Rights']:
                data['license_id'] = "odc-pddl"
                data['license_title'] = "Open Data Commons Public Domain Dedication and License (PDDL)"
                data['license_url'] = "http://www.opendefinition.org/licenses/odc-pddl"
            elif "CC0" in dataset_metadata['Rights']:
                data['license_id'] = "cc-zero"
                data['license_title'] = "Creative Commons CCZero"
                data['license_url'] = "http://www.opendefinition.org/licenses/cc-zero"
            else:
                data['license_id'] = "notspecified"
                data['license_title'] = "License not specified"


    # If there is a 'subject' key in the dataset metadata,
    # add it to the tags depending on whether it's a string or a list
    if 'subject' in dataset_metadata:
        if isinstance(dataset_metadata['subject'], str):
            subjects = dataset_metadata['subject'].replace("(", "").replace(")", "").replace("&", "-").split(',')
            data['tags'] = [{'name': subject} for subject in subjects]
        else:
            data['tags'] = [{'name': subject.replace("(", "").replace(")", "").replace("&", "-").replace("#", "-")}
                            for
                            subject in dataset_metadata['subject']]
            # Go through each tag in the tags list and check if any of them are separated by a comma.
            # If they are, split them into separate tags
            for tag in data['tags']:
                if ', ' in tag['name']:
                    data['tags'].remove(tag)
                    data['tags'] += [{'name': t.strip()} for t in tag['name'].split(',')]


    # If there is a 'version' or 'Version' key in the dataset metadata, add it to the data dictionary
    if 'version' in dataset_metadata:
        data['version'] = dataset_metadata['version']
    elif 'Version' in dataset_metadata:
        data['version'] = dataset_metadata['Version']

    print("Data for migrating to CKAN:")
    de.pretty_print(data)

    # Create the dataset
    dataset_response = ckan.create_dataset(data)
    print(f'Dataset creation response: {dataset_response["success"]}')
    if not dataset_response["success"]:
        print(dataset_response)

    # Get the dataset ID
    dataset_id = dataset_response['result']['id']
    print(f'Dataset ID: {dataset_id}')

    # --------------------------------- FILES --------------------------------

    print("\nMigrating Files...")

    # Get the list of files in the dataset
    files = de.get_files(dataset_metadata['de_path'])
    # Get the total number of files in the dataset
    num_files = files['total']
    print(f"Number of Files: {num_files}")

    # check if num_files is none and return if it is
    if num_files is None:
        return

    # Pass the number of files to the get_files function to get all the files
    files = de.get_files(dataset_metadata['de_path'], limit=num_files)

    # Iterate through each file in the dataset and create a resource for it in CKAN
    for file in files['files']:
        file_metadata = de.get_all_metadata_file(file)
        # pretty_print(file_metadata)

        data = {
            'package_id': dataset_id,
            'name': file_metadata['file_name'],
            'description': None,
            'url': file_metadata['web_dav_location'],
            'format': file_metadata['file_type'],
            'Date created in discovery environment': file_metadata['date_created'],
            'Date last modified in discovery environment': file_metadata['date_modified']
        }
        response = ckan.add_resource_link(data)
        # print(f'Resource creation response: {response}')
        # print("\n\n")

    # Iterate through each folder in the dataset and create a resource for it in CKAN
    for folder in files['folders']:
        folder_metadata = de.get_all_metadata_file(folder)
        # pretty_print(folder_metadata)

        data = {
            'package_id': dataset_id,
            'name': folder_metadata['file_name'],
            'description': None,
            'url': folder_metadata['web_dav_location'],
            'format': 'folder',
            'Date Created in Discovery Environment': folder_metadata['date_created'],
            'Date Last Modified in Discovery Environment': folder_metadata['date_modified']
        }
        response = ckan.add_resource_link(data)


    # This is a placeholder function
    return "Dataset migrated to CKAN successfully."

def generate_croissant_json(username, password, de_link, title, description, author):
    token = de.get_de_api_key(username, password)

    if token is None:
        return "Error obtaining DE API key. Please check username and password."

    headers = {
        'Authorization': f'Bearer {token}'
    }

    path_parts = de_link.split('/')
    directory_path = '/'.join(path_parts[:-1])
    print("Directory Path:", directory_path)

    datasets = de.get_datasets(directory_path, headers)

    for dataset in datasets:
        if dataset['path'] == de_link:
            de.pretty_print(dataset)
            dataset_metadata = de.get_all_metadata_dataset(dataset)
            break


    keywords = []

    # If there   is a 'subject' key in the dataset metadata,
    # add it to the tags depending on whether it's a string or a list
    if 'subject' in dataset_metadata:
        if isinstance(dataset_metadata['subject'], str):
            subjects = dataset_metadata['subject'].replace("(", "").replace(")", "").replace("&", "-").split(',')
            keywords = [subject for subject in subjects]
        else:
            keywords = [subject.replace("(", "").replace(")", "").replace("&", "-").replace("#", "-") for
                        subject in dataset_metadata['subject']]
            # Go through each tag in the tags list and check if any of them are separated by a comma.
            # If they are, split them into separate tags
            for tag in keywords:
                if ', ' in tag:
                    keywords.remove(tag)
                    keywords += [{'name': t.strip()} for t in tag['name'].split(',')]


    version = ""
    # If there is a 'version' or 'Version' key in the dataset metadata, add it to the data dictionary
    if 'version' in dataset_metadata:
        version = dataset_metadata['version']
    elif 'Version' in dataset_metadata:
        version = dataset_metadata['Version']

    # Get the list of files in the dataset
    files = de.get_files(dataset_metadata['de_path'])
    # Get the total number of files in the dataset
    num_files = files['total']
    print(f"Number of Files: {num_files}")

    distributions = []
    # make sure that num_files is none
    if num_files is not None:
        # Pass the number of files to the get_files function to get all the files
        files = de.get_files(dataset_metadata['de_path'], limit=num_files)

        # print("\n\n\nFiles: ")
        de.pretty_print(files)

        # Create a list of distributions for the dataset
        for file in files['files']:
            # Get the metadata for each file
            file_metadata = de.get_all_metadata_file(file)
            # Create a dictionary with the file metadata

            distribution = croissant.create_distribution(file_metadata['file_name'], file_metadata['file_type'],
                                                         file_metadata['web_dav_location'])
            # Append the distribution to the list of distributions
            distributions.append(distribution)

    croissant_json = croissant.create_croissant_jsonld(title, description, author, keywords=keywords, version=version,
                                                       distributions=distributions)

    # Save to file in a temporary directory
    temp_dir = tempfile.gettempdir()
    output_filename = os.path.join(temp_dir, "croissant.json")
    with open(output_filename, "w") as f:
        json.dump(croissant_json, f, indent=4)

    return output_filename

def generate_dcat_json(username, password, de_link, title, description, author):
    token = de.get_de_api_key(username, password)

    if token is None:
        return "Error obtaining DE API key. Please check username and password."

    headers = {
        'Authorization': f'Bearer {token}'
    }

    path_parts = de_link.split('/')
    directory_path = '/'.join(path_parts[:-1])
    print("Directory Path:", directory_path)

    datasets = de.get_datasets(directory_path, headers)

    for dataset in datasets:
        if dataset['path'] == de_link:
            de.pretty_print(dataset)
            dataset_metadata = de.get_all_metadata_dataset(dataset)
            break

    if title == "":
        title = migration.get_title(dataset_metadata)
    if description == "":
        description = migration.get_description(dataset_metadata)
    if author == "":
        author = migration.get_author(dataset_metadata)

    de.pretty_print(dataset_metadata)

    keywords = []

    # If there   is a 'subject' key in the dataset metadata,
    # add it to the tags depending on whether it's a string or a list
    if 'subject' in dataset_metadata:
        if isinstance(dataset_metadata['subject'], str):
            subjects = dataset_metadata['subject'].replace("(", "").replace(")", "").replace("&", "-").split(',')
            keywords = [subject for subject in subjects]
        else:
            keywords = [subject.replace("(", "").replace(")", "").replace("&", "-").replace("#", "-") for
                        subject in dataset_metadata['subject']]
            # Go through each tag in the tags list and check if any of them are separated by a comma.
            # If they are, split them into separate tags
            for tag in keywords:
                if ', ' in tag:
                    keywords.remove(tag)
                    keywords += [{'name': t.strip()} for t in tag['name'].split(',')]

    version = ""
    # If there is a 'version' or 'Version' key in the dataset metadata, add it to the data dictionary
    if 'version' in dataset_metadata:
        version = dataset_metadata['version']
    elif 'Version' in dataset_metadata:
        version = dataset_metadata['Version']

    # Get the list of files in the dataset
    files = de.get_files(dataset_metadata['de_path'])
    # Get the total number of files in the dataset
    num_files = files['total']
    print(f"Number of Files: {num_files}")

    distributions = []
    # make sure that num_files is none
    if num_files is not None:
        # Pass the number of files to the get_files function to get all the files
        files = de.get_files(dataset_metadata['de_path'], limit=num_files)

        # print("\n\n\nFiles: ")
        de.pretty_print(files)

        # Create a list of distributions for the dataset
        for file in files['files']:
            # Get the metadata for each file
            file_metadata = de.get_all_metadata_file(file)
            # Create a dictionary with the file metadata

            distribution = dcat.create_distribution(file_metadata['file_name'], file_metadata['file_type'],
                                                    file_metadata['web_dav_location'])
            # Append the distribution to the list of distributions
            distributions.append(distribution)

    dcat_json = dcat.create_dcat_jsonld(title, description, author, keywords=keywords, version=version,
                                        distributions=distributions)

    # Save to file in a temporary directory
    temp_dir = tempfile.gettempdir()
    output_filename = os.path.join(temp_dir, "dcat.json")
    with open(output_filename, "w") as f:
        json.dump(dcat_json, f, indent=4)

    return output_filename


def handle_submit_migrate(username, password, de_link, title, description, author):
    if not username or not password or not de_link:
        return "Username, password, and DE link are required.", {}

    metadata_status = check_metadata_availability(de_link, username, password)
    if metadata_status == "Error obtaining DE API key. Please check username and password.":
        return metadata_status, {}
    elif metadata_status == "Error obtaining datasets from the Discovery Environment.":
        return metadata_status, {}
    missing_fields = [key for key, value in metadata_status.items() if not value]

    visible_fields = {
        "title": title,
        "description": description,
        "author": author,
    }

    empty_fields = [key for key, value in visible_fields.items() if
                    key in metadata_status and metadata_status[key] == False and not value]

    if missing_fields and empty_fields:
        return f"Missing the following fields in the discovery environment: {', '.join(missing_fields)}", metadata_status

    if empty_fields:
        return f"Please fill in the following required fields: {', '.join(empty_fields)}", metadata_status

    return migrate_dataset_to_ckan(username, password, de_link, title, description, author), metadata_status

def handle_submit_croissant(username, password, de_link, title, description, author):
    if not username or not password or not de_link:
        return "Username, password, and DE link are required.", {}, None

    metadata_status = check_metadata_availability(de_link, username, password)
    if metadata_status == "Error obtaining DE API key. Please check username and password.":
        return metadata_status, {}, None
    elif metadata_status == "Error obtaining datasets from the Discovery Environment.":
        return metadata_status, {}, None
    missing_fields = [key for key, value in metadata_status.items() if not value]

    visible_fields = {
        "title": title,
        "description": description,
        "author": author,
    }

    empty_fields = [key for key, value in visible_fields.items() if
                    key in metadata_status and metadata_status[key] == False and not value]

    if missing_fields and empty_fields:
        return f"Missing the following fields in the discovery environment: {', '.join(missing_fields)}", metadata_status, None

    if empty_fields:
        return f"Please fill in the following required fields: {', '.join(empty_fields)}", metadata_status, None

    print("Title: ", title)
    print("Description: ", description)
    print("Author:", author)

    # Logic to migrate the dataset to CKAN
    token = de.get_de_api_key(username, password)

    if token is None:
        return "Error obtaining DE API key. Please check username and password."

    headers = {
        'Authorization': f'Bearer {token}'
    }

    path_parts = de_link.split('/')
    directory_path = '/'.join(path_parts[:-1])
    print("Directory Path:", directory_path)

    datasets = de.get_datasets(directory_path, headers)

    for dataset in datasets:
        if dataset['path'] == de_link:
            de.pretty_print(dataset)
            dataset_metadata = de.get_all_metadata_dataset(dataset)
            break

    de.pretty_print(dataset_metadata)


    if title == "":
        title = migration.get_title(dataset_metadata)
    if description == "":
        description = migration.get_description(dataset_metadata)
    if author == "":
        author = migration.get_author(dataset_metadata)



    output_filename = generate_croissant_json(username, password, de_link, title, description, author)
    return "Croissant JSON-LD file created successfully.", metadata_status, output_filename


def handle_submit_dcat(username, password, de_link, title, description, author):
    if not username or not password or not de_link:
        return "Username, password, and DE link are required.", {}, None

    metadata_status = check_metadata_availability(de_link, username, password)
    if metadata_status == "Error obtaining DE API key. Please check username and password.":
        return metadata_status, {}, None
    elif metadata_status == "Error obtaining datasets from the Discovery Environment.":
        return metadata_status, {}, None
    missing_fields = [key for key, value in metadata_status.items() if not value]

    visible_fields = {
        "title": title,
        "description": description,
        "author": author,
    }

    empty_fields = [key for key, value in visible_fields.items() if
                    key in metadata_status and metadata_status[key] == False and not value]
    if missing_fields and empty_fields:
        return f"Missing the following fields in the discovery environment: {', '.join(missing_fields)}", metadata_status, None

    if empty_fields:
        return f"Please fill in the following required fields: {', '.join(empty_fields)}", metadata_status, None



    output_filename = generate_dcat_json(username, password, de_link, title, description, author)
    return "DCAT JSON-LD file created successfully.", metadata_status, output_filename

# Set up logging to capture warning messages
class StringIOHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_capture_string = io.StringIO()

    def emit(self, record):
        message = self.format(record)
        self.log_capture_string.write(message + '\n')

    def get_log_contents(self):
        return self.log_capture_string.getvalue()

# Create a logging handler and attach it
log_handler = StringIOHandler()
logging.basicConfig(level=logging.WARNING, handlers=[log_handler])

def parse_validation_log(log):
    """
    Parse the validation log to separate errors from warnings.
    """
    errors = []
    warnings = []
    for line in log.split('\n'):
        if 'error' in line.lower():
            errors.append(line.strip())
        elif 'warning' in line.lower():
            warnings.append(line.strip())
    return errors, warnings

def handle_upload_croissant(username, password, croissant_file):
    if not username or not password or not croissant_file:
        return "Username, password, and croissant file are required."

    token = de.get_de_api_key(username, password)
    print("token: ", token)

    if token is None:
        return "Error authorizing user. Please check username and password."

    log_handler.log_capture_string.truncate(0)
    log_handler.log_capture_string.seek(0)

    with open(croissant_file.name, 'r') as f:
        croissant_json = json.load(f)

    try:
        dataset = Dataset(croissant_json)
        validation_log = log_handler.get_log_contents()
        errors, warnings = parse_validation_log(validation_log)

        if errors:
            return f"Error validating Croissant JSON: Found the following {len(errors)} error(s) during the validation:\n" + "\n".join(errors)
        elif warnings:
            return_message = f"Croissant JSON Uploaded to CKAN with warnings:\n" + "\n".join(warnings)
    except Exception as e:
        return f"Error validating Croissant JSON: {str(e)}"

    # Extract metadata
    title = croissant_json.get('title', 'Untitled')
    description = croissant_json.get('description', 'No description provided.')
    author = croissant_json.get('author', 'Unknown author')
    keywords = croissant_json.get('keyword', [])
    publisher = croissant_json.get('publisher', {}).get('name', 'Unknown publisher')
    date_published = croissant_json.get('datePublished', 'Unknown date')
    license_url = croissant_json.get('license', 'No license specified')

    # Prepare CKAN dataset data
    data = {
        'title': title,
        'name': title.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('.', '-').replace('"', '').replace('/', '-').replace(',', '').replace(':', '').replace("*", "-").replace("'", "-").replace('&', '-').replace("’", "-"),
        'notes': description,
        'author': author,
        'tags': [{'name': keyword} for keyword in keywords],
        'extras': [
            {'key': 'Publisher', 'value': publisher},
            {'key': 'Date Published', 'value': date_published},
            {'key': 'License URL', 'value': license_url}
        ],
        'owner_org': 'cyverse'
    }

    # Create dataset in CKAN
    try:
        ckan_response = ckan.create_dataset(data)
        if not ckan_response['success']:
            return f"Error creating CKAN dataset: {ckan_response['error']}"
        dataset_id = ckan_response['result']['id']
    except Exception as e:
        return f"Error creating CKAN dataset: {str(e)}"

    # Add resources (files) to the CKAN dataset
    for file_info in croissant_json.get('distribution', []):
        resource_data = {
            'package_id': dataset_id,
            'name': file_info.get('title', 'Untitled resource'),
            'description': file_info.get('description', 'No description provided.'),
            'url': file_info.get('downloadURL', 'No URL provided.'),
            'format': file_info.get('encodingFormat', 'Unknown format')
        }
        try:
            resource_response = ckan.add_resource_link(resource_data)
            if not resource_response['success']:
                return f"Error adding resource to CKAN dataset: {resource_response['error']}"
        except Exception as e:
            return f"Error adding resource to CKAN dataset: {str(e)}"

    try:
        return return_message
    except NameError:
        return "Croissant JSON uploaded to CKAN successfully"

def handle_upload_dcat(username, password, dcat_file):
    if not username or not password or not dcat_file:
        return "Username, password, and DCAT file are required."

    # token = de.get_de_api_key(username, password)
    # print("token: ", token)

    # if token is None:
    #     return "Error authorizing user. Please check username and password."

    log_handler.log_capture_string.truncate(0)
    log_handler.log_capture_string.seek(0)

    with open(dcat_file.name, 'r') as f:
        dcat_json = json.load(f)

    # Validate DCAT JSON
    validation_error = validate_dcat_json(dcat_json)
    if validation_error:
        return validation_error

    # Extract metadata
    dataset_info = dcat_json['dataset'][0]

    title = dataset_info.get('title', 'Untitled')
    description = dataset_info.get('description', 'No description provided.')
    author = dataset_info.get('author', 'Unknown author')
    keywords = dataset_info.get('keyword', [])
    publisher = dataset_info.get('publisher', {}).get('name', 'Unknown publisher')
    date_published = dataset_info.get('datePublished', 'Unknown date')
    license_url = dataset_info.get('license', 'No license specified')


    print("Title: ", title)
    print("Description: ", description)
    print("Author:", author)


    # Prepare CKAN dataset data
    data = {
        'title': title,
        'name': title.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('.', '-').replace('"', '').replace('/', '-').replace(',', '').replace(':', '').replace("*", "-").replace("'", "-").replace('&', '-').replace("’", "-"),
        'notes': description,
        'author': author,
        'tags': [{'name': keyword} for keyword in keywords],
        'extras': [
            {'key': 'Publisher', 'value': publisher},
            {'key': 'Date Published', 'value': date_published},
            {'key': 'License URL', 'value': license_url}
        ],
        'owner_org': 'cyverse'
    }

    # Create dataset in CKAN
    try:
        ckan_response = ckan.create_dataset(data)
        print("CKAN Response: ", ckan_response)
        if not ckan_response['success']:
            return f"Error creating CKAN dataset: {ckan_response['error']}"
        dataset_id = ckan_response['result']['id']
    except Exception as e:
        return f"Error creating CKAN dataset: {str(e)}"

    # Add resources (files) to the CKAN dataset
    for dataset in dcat_json.get('dataset', []):
        for distribution in dataset.get('distribution', []):
            resource_data = {
                'package_id': dataset_id,
                'name': distribution.get('title', 'Untitled resource'),
                'description': distribution.get('description', 'No description provided.'),
                'url': distribution.get('downloadURL', 'No URL provided.'),
                'format': distribution.get('encodingFormat', 'Unknown format')
            }
            try:
                resource_response = ckan.add_resource_link(resource_data)
                if not resource_response['success']:
                    return f"Error adding resource to CKAN dataset: {resource_response['error']}"
            except Exception as e:
                return f"Error adding resource to CKAN dataset: {str(e)}"

    return "DCAT JSON uploaded to CKAN successfully."



# Gradio interface layout
def migrate_interface():
    with gr.Blocks() as migrate_block:
        username_input = gr.Textbox(label="Username")
        password_input = gr.Textbox(label="Password", type="password")
        de_link_input = gr.Textbox(label="DE Link")

        title_input = gr.Textbox(label="Title", visible=False)
        description_input = gr.Textbox(label="Description", visible=False)
        author_input = gr.Textbox(label="Author", visible=False)

        submit_button = gr.Button("Submit")
        output = gr.Textbox(label="Output")

        def handle_migrate(*args):
            result, metadata_status = handle_submit_migrate(*args)
            updates = [
                gr.update(visible=not metadata_status.get("title", True)),
                gr.update(visible=not metadata_status.get("description", True)),
                gr.update(visible=not metadata_status.get("author", True))
            ]
            return result, *updates

        submit_button.click(
            fn=handle_migrate,
            inputs=[username_input, password_input, de_link_input, title_input, description_input, author_input],
            outputs=[output, title_input, description_input, author_input]
        )
    return migrate_block

def croissant_interface():
    with gr.Blocks() as croissant_block:
        username_input = gr.Textbox(label="Username")
        password_input = gr.Textbox(label="Password", type="password")
        de_link_input = gr.Textbox(label="DE Link")

        title_input = gr.Textbox(label="Title", visible=False)
        description_input = gr.Textbox(label="Description", visible=False)
        author_input = gr.Textbox(label="Author", visible=False)

        submit_button = gr.Button("Submit")
        output = gr.Textbox(label="Output")
        download_output = gr.File(label="Download File")

        def handle_croissant(*args):
            result, metadata_status, output_filename = handle_submit_croissant(*args)
            updates = [
                gr.update(visible=not metadata_status.get("title", True)),
                gr.update(visible=not metadata_status.get("description", True)),
                gr.update(visible=not metadata_status.get("author", True)),
            ]

            download_link = output_filename
            return result, *updates, download_link

        submit_button.click(
            fn=handle_croissant,
            inputs=[username_input, password_input, de_link_input, title_input, description_input, author_input],
            outputs=[output, title_input, description_input, author_input, download_output]
        )
    return croissant_block

def dcat_interface():
    with gr.Blocks() as dcat_block:
        username_input = gr.Textbox(label="Username")
        password_input = gr.Textbox(label="Password", type="password")
        de_link_input = gr.Textbox(label="DE Link")

        title_input = gr.Textbox(label="Title", visible=False)
        description_input = gr.Textbox(label="Description", visible=False)
        author_input = gr.Textbox(label="Author", visible=False)

        submit_button = gr.Button("Submit")
        output = gr.Textbox(label="Output")
        download_button = gr.File(label="Download DCAT JSON", visible=False)

        def handle_dcat(*args):
            result, metadata_status, output_filename = handle_submit_dcat(*args)
            updates = [
                gr.update(visible=not metadata_status.get("title", True)),
                gr.update(visible=not metadata_status.get("description", True)),
                gr.update(visible=not metadata_status.get("author", True)),
                gr.update(value=output_filename, visible=True)
            ]
            return result, *updates

        submit_button.click(
            fn=handle_dcat,
            inputs=[username_input, password_input, de_link_input, title_input, description_input, author_input],
            outputs=[output, title_input, description_input, author_input, download_button]
        )
    return dcat_block

def upload_croissant_interface():
    with gr.Blocks() as upload_croissant_block:
        with gr.Row():
            username_input = gr.Textbox(label="Username")
            password_input = gr.Textbox(label="Password", type="password")
        croissant_file_input = gr.File(label="Upload Croissant JSON File")
        output = gr.Textbox(label="Output")
        submit_button = gr.Button("Upload")

        submit_button.click(
            fn=handle_upload_croissant,
            inputs=[username_input, password_input, croissant_file_input],
            outputs=[output]
        )
    return upload_croissant_block

def upload_dcat_interface():
    with gr.Blocks(theme=gr.themes.Soft()) as upload_dcat_block:
        with gr.Row():
            username_input = gr.Textbox(label="Username")
            password_input = gr.Textbox(label="Password", type="password")
        dcat_file_input = gr.File(label="Upload DCAT JSON File")
        output = gr.Textbox(label="Output")
        submit_button = gr.Button("Upload")

        submit_button.click(
            fn=handle_upload_dcat,
            inputs=[username_input, password_input, dcat_file_input],
            outputs=[output]
        )
    return upload_dcat_block

iface = gr.TabbedInterface(
    [migrate_interface(), croissant_interface(), dcat_interface(), upload_croissant_interface(), upload_dcat_interface()],
    ["Migrate to CKAN", "Generate Croissant JSON", "Generate DCAT JSON", "Upload Croissant JSON to CKAN", "Upload DCAT JSON to CKAN"],
)

iface.launch()
