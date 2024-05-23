from google.cloud import storage
import folder_paths
from PIL import Image
import json
import os
import numpy as np


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

def save_images(self, images, filename_prefix="ComfyUI"):
    full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
    results = list()
    for (image) in enumerate(images):
        i = 255. * image.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        metadata = None

        file = f"{filename}.png"
        print(f"Saving file to {full_output_folder}/{filename}..")
        img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=self.compress_level)
        results.append({
            "filename": file,
            "subfolder": subfolder,
            "type": self.type
        })
        counter += 1

    return { "ui": { "images": results } }
     
class upload_to_gcp_storage:
    def __init__(self):
        self.type = "output"
        self.output_dir = folder_paths.get_output_directory()
        
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "file_name": ("STRING", {"default": 'file', "multiline": False}),
                "blob_name": ("STRING", {"default": 'blob', "multiline": False}),
                "bucket_name": ("STRING", {"default": "bucket", "multiline": False}),
            },
            "optional": {},
        }
    
    RETURN_TYPES = ()
    FUNCTION = "upload_to_gcp_storage"
    OUTPUT_NODE = True
    CATEGORY = "GCP"


    def upload_to_gcp_storage(self,images,file_name,blob_name,bucket_name):
        subfolder = os.path.dirname(os.path.normpath(file_name))
        full_output_folder = os.path.join(self.output_dir, subfolder)
        full_file_path = os.path.join(full_output_folder, file_name)
        save_images(self, images,file_name)
        get_api_key()
        print(f"Uploading file {file_name} to {bucket_name} as {blob_name}..")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{blob_name}.png")
        blob.upload_from_filename(full_file_path)

NODE_CLASS_MAPPINGS = {
    "GCPStorage": upload_to_gcp_storage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GCPStorage": "GCP Storage Node",
}