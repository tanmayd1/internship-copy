import gradio as gr
import requests
import hashlib
import json
from io import BytesIO
import de
import ckan
import migration
from mlcroissant import Dataset
import logging
import io
import tempfile
import os

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
        data['title'] = migration.get_title(dataset_metadata)

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


    # Create the dataset
    dataset_response = ckan.create_dataset(data)
    print(f'Dataset creation response: {dataset_response["success"]}')
    if not dataset_response["success"]:
        print(dataset_response)

    # Get the dataset ID
    dataset_id = dataset_response['result']['id']
    print(f'Dataset ID: {dataset_id}')

    # This is a placeholder function
    return "Dataset migrated to CKAN successfully."

def generate_croissant_json(username, password, de_link, title, description, author):
    # Logic to generate Croissant JSON file
    croissant_json = {
        "@context": {
            "@vocab": "https://schema.org/",
            "croissant": "https://mlcommons.org/croissant#",
            "Dataset": "https://schema.org/Dataset",
            "FileObject": "https://schema.org/FileObject"
        },
        "@type": "Dataset",
        "name": title.replace(" ", "_"),
        "title": title,
        "description": description,
        "identifier": hashlib.sha256(de_link.encode()).hexdigest(),
        "author": author,
        "isLiveDataset": True,
        "subField": [],
        "parentField": [],
        "format": "json-ld",
        "transform": [],
        "path": "",
        "cr": [],
        "key": [],
        "source": [],
        "field": [],
        "fileProperty": [],
        "extract": [],
        "repeated": False,
        "@language": "en",
        "data": [],
        "rai": [],
        "column": [],
        "citeAs": "",
        "examples": [],
        "includes": [],
        "regex": "",
        "fileSet": [],
        "recordSet": [],
        "references": [],
        "dct": [],
        "jsonPath": "",
        "dataType": "Dataset",
        "fileObject": [],
        "conformsTo": "https://schema.org",
        "separator": ",",
        "sc": [],
        "md5": "",
        "replace": ""
    }
    # Save to file in a temporary directory
    temp_dir = tempfile.gettempdir()
    output_filename = os.path.join(temp_dir, "croissant.json")
    with open(output_filename, "w") as f:
        json.dump(croissant_json, f, indent=4)

    return output_filename

def generate_dcat_json(username, password, de_link, title, description, author):
    # Logic to generate DCAT JSON file
    dcat_json = {
        "@context": {
            "@vocab": "https://schema.org/",
            "dcat": "http://www.w3.org/ns/dcat#",
            "Dataset": "https://schema.org/Dataset",
            "FileObject": "https://schema.org/FileObject"
        },
        "@type": "Catalog",
        "title": "Dataset Catalog",
        "description": "A catalog of datasets.",
        "dataset": [
            {
                "@type": "Dataset",
                "name": title.replace(" ", "_"),
                "title": title,
                "description": description,
                "identifier": hashlib.sha256(de_link.encode()).hexdigest(),
                "author": author,
                "distribution": []
            }
        ]
    }
    # Save to file
    with open("dcat.json", "w") as f:
        json.dump(dcat_json, f, indent=4)

    return "DCAT JSON-LD file created successfully."

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
        return "Username, password, and DE link are required.", {}

    metadata_status = check_metadata_availability(de_link, username, password)
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

    return "Croissant JSON-LD file created successfully.", generate_croissant_json(username, password, de_link, title, description, author), metadata_status

def handle_submit_dcat(username, password, de_link, title, description, author):
    if not username or not password or not de_link:
        return "Username, password, and DE link are required.", {}

    metadata_status = check_metadata_availability(de_link, username, password)
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

    return generate_dcat_json(username, password, de_link, title, description, author), metadata_status

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

def handle_upload_croissant(username, password, croissant_file):
    log_handler.log_capture_string.truncate(0)
    log_handler.log_capture_string.seek(0)

    # Load and validate the Croissant JSON file
    with open(croissant_file.name, 'r') as f:
        croissant_json = json.load(f)

    try:
        dataset = Dataset(croissant_json)
        warning_messages = log_handler.get_log_contents()
        if warning_messages:
            return f"Croissant JSON uploaded to CKAN successfully with warnings:\n{warning_messages}"
    except Exception as e:
        return f"Error validating Croissant JSON: {str(e)}"

    title = croissant_json['title']
    description = croissant_json['description']
    author = croissant_json['author']

    print("Title: ", title)
    print("Description: ", description)
    print("Author:", author)

    return "Uploaded to CKAN successfully completed"

def handle_upload_dcat(username, password, dcat_file):
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
            result, download_output, metadata_status = handle_submit_croissant(*args)
            updates = [
                gr.update(visible=not metadata_status.get("title", True)),
                gr.update(visible=not metadata_status.get("description", True)),
                gr.update(visible=not metadata_status.get("author", True))
            ]
            return result, *updates, download_output

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

        def handle_dcat(*args):
            result, metadata_status = handle_submit_dcat(*args)
            updates = [
                gr.update(visible=not metadata_status.get("title", True)),
                gr.update(visible=not metadata_status.get("description", True)),
                gr.update(visible=not metadata_status.get("author", True))
            ]
            return result, *updates

        submit_button.click(
            fn=handle_dcat,
            inputs=[username_input, password_input, de_link_input, title_input, description_input, author_input],
            outputs=[output, title_input, description_input, author_input]
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
    with gr.Blocks() as upload_dcat_block:
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
    ["Migrate to CKAN", "Generate Croissant JSON", "Generate DCAT JSON", "Upload Croissant JSON to CKAN", "Upload DCAT JSON to CKAN"]
)

iface.launch()

