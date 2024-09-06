import json
import hashlib


def create_croissant_jsonld(title, description, author, distributions=[],
                            keywords=[], identifier="", publisher_name="",
                            citation="", date_published="", license_url="",
                            version=""):
    """
    Create a Croissant-compliant JSON-LD file.

    Args:
        title (str): Title of the dataset.
        description (str): Description of the dataset.
        identifier (str): Identifier of the dataset.
        keywords (list): List of keywords for the dataset.
        publisher_name (str): Name of the publisher.
        distributions (list): List of distribution metadata.
        citation (str): Citation for the dataset.
        date_published (str): Publication date of the dataset.
        license_url (str): License URL for the dataset.
        version (str): Version of the dataset.

    Returns:
        dict: The Croissant-compliant JSON-LD metadata.
    """
    croissant = {
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
        "author": author,
        "identifier": identifier,
        "keyword": keywords,
        "publisher": {
            "@type": "Organization",
            "name": publisher_name
        },
        "distribution": distributions,
        "citation": citation,
        "datePublished": date_published,
        "license": license_url,
        "version": version,
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
        "citeAs": citation,
        "examples": [],
        "includes": [],
        "regex": "",
        "fileSet": [],
        "recordSet": [],
        "references": [],
        "dct": [],
        "jsonPath": "",
        "dataType": "Dataset",
        "fileObject": distributions,
        "conformsTo": "https://schema.org",
        "separator": ",",
        "sc": [],
        "md5": "",
        "replace": ""
    }
    return croissant


def create_distribution(title, format, download_url, description=""):
    # Generate a unique identifier using the SHA-256 hash of the download URL
    identifier = hashlib.sha256(download_url.encode()).hexdigest()
    print(f"Generated identifier for {title}: {identifier}")

    return {
        "@type": "FileObject",
        "name": title.replace(" ", "_"),
        "identifier": identifier,
        "title": title,
        "description": description,
        "encodingFormat": format,
        "contentUrl": download_url,
        "sha256": identifier  # Example SHA-256 hash
    }


# Example usage
if __name__ == '__main__':
    # Example usage
    title = "Example Dataset"
    description = "This is an example dataset."
    identifier = "http://example.org/dataset/1"
    keywords = ["example", "dataset"]
    publisher_name = "Example Organization"
    citation = "Example Citation"
    date_published = "2022-01-01"
    license_url = "http://example.org/license"
    version = "1.0.0"
    distributions = [
        create_distribution("Example Dataset CSV",
                            "CSV file of the example dataset.",
                            "text/csv",
                            "http://example.org/dataset/1.csv"),
        create_distribution("Example Dataset Parquet",
                            "Parquet file of the example dataset.",
                            "application/x-parquet",
                            "http://example.org/dataset/1.parquet")
    ]

    croissant_jsonld = create_croissant_jsonld(title, description)

    # Save to file
    with open("croissant_title_and_description_only.json", "w") as f:
        json.dump(croissant_jsonld, f, indent=4)

    print("Croissant JSON-LD file created successfully.")
