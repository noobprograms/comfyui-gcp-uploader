from google.cloud import storage
import folder_paths
from PIL import Image
import os
import numpy as np
import time

class GCPImageUploader:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "file_name": ("STRING", {"default": 'file', "multiline": False}),
                "bucket_name": ("STRING", {"default": "bucket", "multiline": False}),
                "bucket_folder_prefix": ("STRING", {"default": "", "multiline": False}),
                "gcp_service_json": ("STRING", {"default": 'path/to/credentials.json', "multiline": False}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "upload_to_gcp"
    OUTPUT_NODE = True
    CATEGORY = "🪣 Cloud Uploads/GCP"

    def upload_to_gcp(self, images, file_name, bucket_name, bucket_folder_prefix, gcp_service_json):
        print(f"[GCPImageUploader] Using credentials from: {gcp_service_json}")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_service_json

        timestamp = int(time.time())
        filename_prefix = f"{file_name}_{timestamp}"
        results = self.save_images(images, filename_prefix)

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        uploaded_urls = []
        for image_meta in results:
            local_path = os.path.join(self.output_dir, image_meta["subfolder"], image_meta["filename"])
            remote_path = f"{bucket_folder_prefix}/{image_meta['filename']}"
            print(f"[GCPImageUploader] Uploading {local_path} → gs://{bucket_name}/{remote_path}")
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_path)
            file_size_bytes = os.path.getsize(local_path)
            size_kb = round(file_size_bytes / 1024, 2)
            public_url = f"https://storage.googleapis.com/{bucket_name}/{remote_path}"
            uploaded_urls.append({
            "url": public_url,
            "filename": image_meta["filename"],
            "width": image_meta["width"],
            "height": image_meta["height"],
            "size_kb": size_kb
        })

        return {
            "ui": {"images": results, "uploaded_urls": uploaded_urls}
        }

    def save_images(self, images, filename_prefix):
        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])

        results = []

        for i, image in enumerate(images):
            i_data = 255. * image.cpu().numpy()
            np_image = np.clip(i_data, 0, 255).astype(np.uint8)

            if np_image.shape[2] == 4:
                img_format = "PNG"
                ext = ".png"
                img = Image.fromarray(np_image, mode="RGBA")
            else:
                img_format = "JPEG"
                ext = ".jpg"
                img = Image.fromarray(np_image, mode="RGB")

            image_filename = f"{filename}_{i:03}{ext}"
            full_path = os.path.join(full_output_folder, image_filename)

            if img_format == "JPEG":
                img.save(full_path, format="JPEG", quality=90)
            else:
                img.save(full_path, format="PNG", compress_level=self.compress_level)

            results.append({
                "filename": image_filename,
                "subfolder": subfolder,
                "type": self.type,
                "width": img.width,
                "height": img.height,
            })

        return results

NODE_CLASS_MAPPINGS = {
    "GCPImageUploader": GCPImageUploader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GCPImageUploader": "🪣 Upload to GCP Bucket",
}
