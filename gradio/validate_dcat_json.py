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