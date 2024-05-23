from google.cloud import storage
import folder_paths
from PIL import Image
import json
import os
import numpy as np

config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'gcp_config.json')
     
class upload_to_gcp_storage:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.compress_level = 4
        
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "file_name": ("STRING", {"default": 'file', "multiline": False}),
                "bucket_name": ("STRING", {"default": "bucket", "multiline": False}),
                "bucket_folder_prefix": ("STRING", {"multiline": False}),
            },
            "optional": {},
        }
    
    RETURN_TYPES = ()
    FUNCTION = "upload_to_gcp_storage"
    OUTPUT_NODE = True
    CATEGORY = "image"

    def upload_to_gcp_storage(self,images,file_name,bucket_name,bucket_folder_prefix):
        get_api_key()

        file = f"{file_name}.png"
        subfolder = os.path.dirname(os.path.normpath(file))
        full_output_folder = os.path.join(self.output_dir, subfolder)
        full_file_path = os.path.join(full_output_folder, file)

        print(f"Saving file '{file_name}' to {full_file_path}..")
        save_images(self, images,file_name)

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{bucket_folder_prefix}/{file}")
        print(f"Uploading blob to {bucket_name}/{bucket_folder_prefix}/{file}..")
        blob.upload_from_filename(full_file_path)

        return {"ui": {"images": []}}

def get_api_key():
    print(f"Checking for Service account json..")
    try:
        print(f"Config File Location: {config_file_path}")
        with open(config_file_path, "r") as f:
            config = json.load(f)
        json_path = config["gcp_service_json_path"]
        print(f"Setting [GOOGLE_APPLICATION_CREDENTIALS] to {json_path}..")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= json_path
    except:
        print("Error: Service account json not found")

def save_images(self, images, filename_prefix="ComfyUI"):
    full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
    for (batch_number, image) in enumerate(images):
        i = 255. * image.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        metadata = None
        file = f"{filename}.png"
        img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=self.compress_level)

NODE_CLASS_MAPPINGS = {
    "GCPStorageNode": upload_to_gcp_storage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GCPStorageNode": "GCP Storage Upload",
}