# Data Commons
This is a replacement for the CyVerse Data Commons based on CKAN.

Large scale data repositories that are hosted in commercial cloud are common for NIH, NASA funded projects, analysis performed with these data sets with private local data is a regular occurrence.

Eventually the final results have to be made public, sharing these multiple data sources and analysis in a unified form are a fairly challenge for most projects. We will create a novel protocol that will allow labs to create their own data commons that can be customized for their projects and meet federal data sharing requirements.

## Python Scripts

### migration/de.py

This is a helper script used to interact with the Data Commons API. 
It is used to get datasets, files, and metadata from the Discovery Environment.

### migration/ckan.py 

This is a helper script  used to interact with the CKAN API. 
It is used to create datasets, resources, and organizations in CKAN.

### migration/migration.py

This is the primary script that is used to migrate datasets from the Discovery Environment to CKAN.
It iterates through each dataset in the curated directory in the discovery environment and creates a dataset in CKAN with the same metadata if it does not already exist.
If it does exist, it also checks if the files in the dataset have been updated and updates the dataset in CKAN accordingly.
This script doesn't take in any arguments and is run as is.
This script is also being run as a cron job every 24 hours to keep the datasets in CKAN up to date.

### migration/migrate_single_dataset.py

This script is used to migrate a single dataset from the Discovery Environment to CKAN using the functions defined in migration.py.
It takes in 4 command line arguments:
- data_store_path: The path to the dataset in the Discovery Environment
- ckan_org: The organization in CKAN where the dataset should be created
- username: The username of the user who is wanting to migrate the dataset
- password: The password of the user who is wanting to migrate the dataset

The username and password is used to generate the API key for the discovery environment API so that the script can interact with the API.
It is also a form of authentication to ensure that only authorized users can migrate datasets.

*Example usage:*
```
python migrate_single_dataset.py /iplant/home/shared/test cyverse test_user test_password
```

### gradio/gradio_main.py

This is currently a testing script to test creating an interface using gradio.

