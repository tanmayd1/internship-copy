import json
import jsonschema
from jsonschema import validate

# Define a simple DCAT schema
dcat_schema = {
    "type": "object",
    "properties": {
        "@context": {"type": "object"},
        "@type": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "dataset": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "@type": {"type": "string"},
                    "name": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "identifier": {"type": "string"},
                    "author": {"type": "string"},
                    "distribution": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                },
                "required": ["@type", "name", "title", "description", "identifier", "author"]
            }
        }
    },
    "required": ["@context", "@type", "title", "description", "dataset"]
}

def validate_dcat_json(dcat_json):
    try:
        validate(instance=dcat_json, schema=dcat_schema)
    except jsonschema.exceptions.ValidationError as err:
        return f"Error validating DCAT JSON: {err.message}"
    return None

# Example DCAT JSON
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
            "name": "example_dataset",
            "title": "Example Dataset",
            "description": "An example dataset.",
            "identifier": "12345",
            "author": "John Doe",
            "publisher": {
                "@type": "Organization",
                "name": "Example Publisher"
            },
            "distribution": [
                {
                    "@type": "FileObject",
                    "name": "example_file",
                    "description": "An example file.",
                    "encodingFormat": "text/csv",
                    "contentUrl": "https://example.com/example.csv",
                    "sha256": "abc123"
                }
            ]
        }
    ]
}

# Validate the DCAT JSON