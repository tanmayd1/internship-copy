import json
from datetime import datetime
from mlcroissant._src.datasets import Dataset
from mlcroissant._src.structure_graph.nodes.metadata import Metadata
from mlcroissant._src.core.context import Context

def convert_dcat_to_croissant(dcat_file_path, croissant_output_path):
    """
    Convert a DCAT JSON-LD file to Croissant JSON-LD format.

    Args:
        dcat_file_path (str): Path to the input DCAT JSON-LD file.
        croissant_output_path (str): Path to the output Croissant JSON-LD file.
    """
    # Load the DCAT JSON-LD file
    with open(dcat_file_path, 'r') as f:
        dcat_json = json.load(f)

    # Transform the DCAT JSON-LD to Croissant JSON-LD
    try:
        ctx = Context()
        metadata = Metadata.from_json(ctx=ctx, json_=dcat_json)
        croissant_json = metadata.to_json()
    except Exception as e:
        print(f"Error converting to Croissant JSON-LD: {e}")
        return

    # Custom JSON serializer for datetime objects
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {obj.__class__.__name__} not serializable")

    # Save the Croissant JSON-LD to the specified output path
    with open(croissant_output_path, 'w') as f:
        json.dump(croissant_json, f, indent=4, default=json_serializer)
    print(f"Croissant JSON-LD file created successfully at {croissant_output_path}")

# Example usage
dcat_file_path = "dcat.json"
croissant_output_path = "croissant.json"
convert_dcat_to_croissant(dcat_file_path, croissant_output_path)
