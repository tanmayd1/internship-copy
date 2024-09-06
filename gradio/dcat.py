import json
import hashlib
import datetime


def generate_sha256_hash(file_path):
    """
    Generate the SHA-256 hash for a given file.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: The SHA-256 hash of the file.
    """
    identifier = hashlib.sha256(file_path.encode()).hexdigest()
    return identifier


def create_dcat_jsonld(title, description, author, distributions=[],
                       keywords=[], identifier="", publisher_name="",
                       citation="", date_published="", license_url="",
                       version=""):
    """
    Create a DCAT-compliant JSON-LD file.

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
        dict: The DCAT-compliant JSON-LD metadata.
    """
    dcat = {
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
                "identifier": identifier,
                "keyword": keywords,
                "author": author,
                "publisher": {
                    "@type": "Organization",
                    "name": publisher_name
                },
                "distribution": distributions,
                "citation": citation,
                "license": license_url,
                "version": version
            }
        ]
    }
    return dcat


def create_distribution(title, format, file_path, description=""):
    """
    Create distribution metadata for a file.

    Args:
        title (str): Title of the distribution.
        description (str): Description of the distribution.
        format (str): Format of the file.
        download_url (str): URL to download the file.
        file_path (str): Path to the file to generate the SHA-256 hash.

    Returns:
        dict: The distribution metadata including the SHA-256 hash.
    """
    sha256_hash = generate_sha256_hash(file_path)
    return {
        "@type": "FileObject",
        "name": title.replace(" ", "_"),
        "description": description,
        "encodingFormat": format,
        "contentUrl": file_path,
        "sha256": sha256_hash
    }


if __name__ == '__main__':
    # Example usage
    title = "Example Dataset"
    description = "This is an example dataset."
    identifier = "http://example.org/dataset/1"
    keywords = ["example", "dataset"]
    publisher_name = "Example Organization"
    citation = "Example Organization (2024). Example Dataset. Retrieved from http://example.org/dataset/1"
    date_published = datetime.date.today().isoformat()  # Use today's date for example
    license_url = "http://example.org/license"
    version = "1.0.0"  # Ensure version follows MAJOR.MINOR.PATCH format

    # Paths to the example files
    csv_file_path = "path/to/example_dataset.csv"
    parquet_file_path = "path/to/example_dataset.parquet"

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

    dcat_jsonld = create_dcat_jsonld(title, description, identifier,
                                     keywords, publisher_name, distributions,
                                     citation, date_published, license_url, version)

    # Save to file
    with open("../migration/dcat.json", "w") as f:
        json.dump(dcat_jsonld, f, indent=4)

    print("DCAT JSON-LD file created successfully.")
