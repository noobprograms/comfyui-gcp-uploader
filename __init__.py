import os
import json

config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")

if not os.path.isfile(config_file_path):
    print('Creating missing config file..')
    config = {
        "gcp_service_json_path": "xxx"
    }

    with open(config_file_path, "w") as f:
        json.dump(config, f, indent=2)