import importlib
import os
import json

config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "gcp_storage_config")

def install_gcp_storage():
    print(f"Checking for google-cloud-storage installation..")
    try:
        importlib.import_module("google-cloud-storage")
    except ImportError:
        print("Error: google-cloud-storage not found. Installing..")
        import pip
        pip.main(["install", "google-cloud-storage"])

install_gcp_storage()
if not os.path.isfile(config_file_path):
    print('Creating missing config file..')
    config = {
        "gcp_service_json_path": "xxx"
    }

    with open(config_file_path, "w") as f:
        json.dump(config, f, indent=2)

from .gcp_storage import NODE_CLASS_MAPPINGS
from .gcp_storage import NODE_DISPLAY_NAME_MAPPINGS
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']