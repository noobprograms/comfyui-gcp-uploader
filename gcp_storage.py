from google.cloud import storage
import json
import os

config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'config.json')

def get_api_key():
    print(f"Checking for Service account json..")
    try:
        print(f"Config File Location: {config_file_path}")
        with open(config_file_path, "r") as f:
            config = json.load(f)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= config["gcp_service_json_path"]
    except:
        print("Error: Service account json not found")
     
class GCPStorage:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE", ),
                "blob_name": ("STRING", {"default": 'blob', "multiline": False}),
                "bucket_name": ("STRING", {"default": "bucket", "multiline": False}),
            },
            "optional": {},
        }
    
    RETURN_TYPES = ()
    FUNCTION = "upload_to_storage"
    OUTPUT_NODE = False
    CATEGORY = "GCP"
    EXECUTE='upload_to_storage'

    @staticmethod
    def upload_to_storage(image,blob_name,bucket_name):
        print(f"Uploading file {image} to {bucket_name} as {blob_name}..")

        get_api_key()

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(image)

NODE_CLASS_MAPPINGS = {
    "GCPStorage": GCPStorage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GCPStorage": "GCP Storage Node",
}