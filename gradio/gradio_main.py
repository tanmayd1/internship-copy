import gradio as gr
from mlcroissant import Dataset
import json

import sys
import ckan
import de
import migration

import file_utils as fu
import log_utils as lu
from check_metadata_availability import check_metadata_availability
from validate_dcat_json import validate_dcat_json
import migrate_utils


def handle_submit_migrate(username, password, de_link, convert_csv, title, description, author):
    """
    Handles the submission for migrating a dataset from the Discovery Environment (DE) to CKAN.

    Args:
        username (str): Username for DE authentication.
        password (str): Password for DE authentication.
        de_link (str): Link to the dataset in DE.
        convert_csv (bool): Flag to convert CSV files to Parquet.
        title (str): Title of the dataset.
        description (str): Description of the dataset.
        author (str): Author of the dataset.

    Returns:
        str: Result message.
        dict: Metadata status.
    """
    if not username or not password or not de_link:
        return "Username, password, and DE link are required.", {}

    # Check the availability of metadata
    metadata_status = check_metadata_availability(de_link, username, password)
    if metadata_status == "Error obtaining DE API key. Please check username and password.":
        return metadata_status, {}
    elif metadata_status == "Error obtaining datasets from the Discovery Environment.":
        return metadata_status, {}

    # Determine missing and empty fields
    missing_fields = [key for key, value in metadata_status.items() if not value]
    visible_fields = {"title": title, "description": description, "author": author}
    empty_fields = [key for key, value in visible_fields.items() if
                    key in metadata_status and metadata_status[key] is False and not value]

    # Return messages for missing and empty fields
    if missing_fields and empty_fields:
        return (f"Missing the following fields in the discovery environment: "
                f"{', '.join(missing_fields)}"), metadata_status
    if empty_fields:
        return (f"Please fill in the following required fields: "
                f"{', '.join(empty_fields)}"), metadata_status

    # Migrate dataset to CKAN
    return migrate_utils.migrate_dataset_to_ckan(username, password, de_link,
                                                 title, description, author, convert_csv), metadata_status


def handle_submit_croissant(username, password, de_link, title, description, author):
    """
    Handles the submission for generating a Croissant JSON-LD file.

    Args:
        username (str): Username for DE authentication.
        password (str): Password for DE authentication.
        de_link (str): Link to the dataset in DE.
        title (str): Title of the dataset.
        description (str): Description of the dataset.
        author (str): Author of the dataset.

    Returns:
        str: Result message.
        dict: Metadata status.
        str: Output filename.
    """

    if not username or not password or not de_link:
        return "Username, password, and DE link are required.", {}

    # Check the availability of metadata
    metadata_status = check_metadata_availability(de_link, username, password)
    if metadata_status == "Error obtaining DE API key. Please check username and password.":
        return metadata_status, {}, None
    elif metadata_status == "Error obtaining datasets from the Discovery Environment.":
        return metadata_status, {}, None

    # Determine missing and empty fields
    missing_fields = [key for key, value in metadata_status.items() if not value]
    visible_fields = {"title": title, "description": description, "author": author}
    empty_fields = [key for key, value in visible_fields.items() if
                    key in metadata_status and metadata_status[key] is False and not value]

    # Return messages for missing and empty fields
    if missing_fields and empty_fields:
        return f"Missing the following fields in the discovery environment: {', '.join(missing_fields)}", metadata_status, None
    if empty_fields:
        return f"Please fill in the following required fields: {', '.join(empty_fields)}", metadata_status, None

    # Generate Croissant JSON-LD file
    output_filename = fu.generate_croissant_json(username, password, de_link, title, description, author)
    return "Croissant JSON-LD file created successfully.", metadata_status, output_filename


def handle_submit_dcat(username, password, de_link, title, description, author):
    """
    Handles the submission for generating a DCAT JSON-LD file.

    Args:
        username (str): Username for DE authentication.
        password (str): Password for DE authentication.
        de_link (str): Link to the dataset in DE.
        title (str): Title of the dataset.
        description (str): Description of the dataset.
        author (str): Author of the dataset.

    Returns:
        str: Result message.
        dict: Metadata status.
        str: Output filename.
    """
    if not username or not password or not de_link:
        return "Username, password, and DE link are required.", {}

    # Check the availability of metadata
    metadata_status = check_metadata_availability(de_link, username, password)
    if metadata_status == "Error obtaining DE API key. Please check username and password.":
        return metadata_status, {}, None
    elif metadata_status == "Error obtaining datasets from the Discovery Environment.":
        return metadata_status, {}, None

    # Determine missing and empty fields
    missing_fields = [key for key, value in metadata_status.items() if not value]
    visible_fields = {"title": title, "description": description, "author": author}
    empty_fields = [key for key, value in visible_fields.items() if
                    key in metadata_status and metadata_status[key] is False and not value]

    # Return messages for missing and empty fields
    if missing_fields and empty_fields:
        return f"Missing the following fields in the discovery environment: {', '.join(missing_fields)}", metadata_status, None
    if empty_fields:
        return f"Please fill in the following required fields: {', '.join(empty_fields)}", metadata_status, None

    # Generate DCAT JSON-LD file
    output_filename = fu.generate_dcat_json(username, password, de_link, title, description, author)
    return "DCAT JSON-LD file created successfully.", metadata_status, output_filename


def handle_upload_croissant(username, password, croissant_file):
    """
    Handles the uploading of a Croissant JSON file to CKAN.

    Args:
        username (str): Username for DE authentication.
        password (str): Password for DE authentication.
        croissant_file (UploadedFile): The Croissant JSON file.

    Returns:
        str: Result message.
    """
    if not username or not password or not croissant_file:
        return "Username, password, and croissant file are required."

    # Get DE API token
    token = de.get_de_api_key(username, password)
    if token is None:
        return "Error authorizing user. Please check username and password."

    # Clear the log handler
    lu.log_handler.log_capture_string.truncate(0)
    lu.log_handler.log_capture_string.seek(0)

    # Load Croissant JSON file
    with open(croissant_file.name, 'r') as f:
        croissant_json = json.load(f)

    try:
        # Validate the Croissant JSON
        dataset = Dataset(croissant_json)
        validation_log = lu.log_handler.get_log_contents()
        errors, warnings = lu.parse_validation_log(validation_log)

        # Handle validation errors and warnings
        if errors:
            return (f"Error validating Croissant JSON: Found the following {len(errors)} "
                    f"error(s) during the validation:\n") + "\n".join(errors)
        elif warnings:
            return_message = "Croissant JSON Uploaded to CKAN with warnings:\n" + "\n".join(warnings)
    except Exception as e:
        return f"Error validating Croissant JSON: {str(e)}"

    # Extract metadata and prepare CKAN dataset data
    metadata = fu.extract_metadata(croissant_json)
    print(metadata)
    data = {}
    data['name'] = migration.get_name_from_title(metadata.get('title', 'Untitled dataset'))
    data['title'] = metadata.get('title', 'Untitled dataset')
    data['notes'] = metadata.get('description', 'No description provided.')
    data['author'] = metadata.get('author', 'No author provided.')
    data['owner_org'] = 'cyverse'
    data['tags'] = metadata.get('keywords', [])

    try:
        # Create dataset in CKAN
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
    """
    Handles the uploading of a DCAT JSON file to CKAN.

    Args:
        username (str): Username for DE authentication.
        password (str): Password for DE authentication.
        dcat_file (UploadedFile): The DCAT JSON file.

    Returns:
        str: Result message.
    """
    if not username or not password or not dcat_file:
        return "Username, password, and DCAT file are required."

    # Clear the log handler
    lu.log_handler.log_capture_string.truncate(0)
    lu.log_handler.log_capture_string.seek(0)

    # Load DCAT JSON file
    with open(dcat_file.name, 'r') as f:
        dcat_json = json.load(f)

    # Validate DCAT JSON
    validation_error = validate_dcat_json(dcat_json)
    if validation_error:
        return validation_error

    # Extract metadata and prepare CKAN dataset data
    dataset_info = dcat_json['dataset'][0]
    metadata = fu.extract_metadata(dataset_info)
    data = {}
    data['name'] = migration.get_name_from_title(metadata.get('title', 'Untitled dataset'))
    data['title'] = metadata.get('title', 'Untitled dataset')
    data['notes'] = metadata.get('description', 'No description provided.')
    data['author'] = metadata.get('author', 'No author provided.')
    data['owner_org'] = 'cyverse'
    data['tags'] = metadata.get('keywords', [])

    de.pretty_print(data)

    try:
        # Create dataset in CKAN
        ckan_response = ckan.create_dataset(data)
        if not ckan_response['success']:
            return f"Error creating CKAN dataset: {ckan_response['error']}"
        dataset_id = ckan_response['result']['id']
    except Exception as e:
        return f"Error creating CKAN dataset: {str(e)}"

    # Add resources (files) to the CKAN dataset
    for distribution in dataset_info.get('distribution', []):
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
    """
    Creates the interface for migrating a dataset from DE to CKAN.
    """
    with gr.Blocks() as migrate_block:
        username_input = gr.Textbox(label="Username")
        password_input = gr.Textbox(label="Password", type="password")
        de_link_input = gr.Textbox(label="DE Link")
        convert_csv_input = gr.Checkbox(label="Convert CSV to Parquet", value=False)

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
            inputs=[username_input, password_input, de_link_input, convert_csv_input, title_input, description_input,
                    author_input],
            outputs=[output, title_input, description_input, author_input]
        )
    return migrate_block


def croissant_interface():
    """
    Creates the interface for generating a Croissant JSON-LD file from a path in the Discovery Environment.
    """
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
    """
    Creates the interface for generating a DCAT JSON-LD file.
    """
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
    """
    Creates the interface for uploading a Croissant JSON file to CKAN.
    """
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
    """
    Creates the interface for uploading a DCAT JSON file to CKAN.
    """
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


# Create the Gradio interface with all tabs
iface = gr.TabbedInterface(
    [migrate_interface(), croissant_interface(), dcat_interface(), upload_croissant_interface(),
     upload_dcat_interface()],
    ["Migrate to CKAN", "Generate Croissant JSON", "Generate DCAT JSON", "Upload Croissant JSON to CKAN",
     "Upload DCAT JSON to CKAN"],
    theme=gr.themes.Monochrome()
)

# Launch the Gradio interface
iface.launch(server_name="0.0.0.0", server_port=7860)
