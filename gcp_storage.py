from google.cloud import storage
import folder_paths
from PIL import Image
import os
import numpy as np
import time
import shutil

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

class GCPVideoUploader:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "videos": ("VIDEO",),
                "file_name": ("STRING", {"default": "video_file", "multiline": False}),
                "bucket_name": ("STRING", {"default": "bucket", "multiline": False}),
                "bucket_folder_prefix": ("STRING", {"default": "", "multiline": False}),
                "gcp_service_json": ("STRING", {"default": "path/to/credentials.json", "multiline": False}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "upload_to_gcp"
    OUTPUT_NODE = True
    CATEGORY = "🪣 Cloud Uploads/GCP"

    def upload_to_gcp(self, videos, file_name, bucket_name, bucket_folder_prefix, gcp_service_json):
        print(f"[GCPVideoUploader] Using credentials from: {gcp_service_json}")
        print(f"[GCPVideoUploader] DEBUG - videos type: {type(videos)}")
        print(f"[GCPVideoUploader] DEBUG - videos content: {videos}")
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_service_json

        timestamp = int(time.time())
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        uploaded_urls = []

        # ComfyUI VIDEO type is typically a tuple: (frames_tensor, fps, etc) or dict with 'filenames'
        # First, check if videos is a dictionary with 'filenames' key (common format)
        if isinstance(videos, dict) and 'filenames' in videos:
            # Extract filenames from the video dictionary
            video_files = videos['filenames']
            if not isinstance(video_files, list):
                video_files = [video_files]
            
            for i, video_file_info in enumerate(video_files):
                # video_file_info might be a dict or a path string
                if isinstance(video_file_info, dict):
                    video_path = video_file_info.get('filename') or video_file_info.get('path')
                    subfolder = video_file_info.get('subfolder', '')
                    video_type = video_file_info.get('type', 'output')
                else:
                    video_path = str(video_file_info)
                    subfolder = ''
                    video_type = 'output'
                
                # Construct full local path
                if subfolder:
                    local_path = os.path.join(self.output_dir, subfolder, video_path)
                else:
                    local_path = os.path.join(self.output_dir, video_path)
                
                if not os.path.exists(local_path):
                    raise FileNotFoundError(f"[GCPVideoUploader] Video file not found: {local_path}")
                
                # Create new filename with timestamp
                ext = os.path.splitext(video_path)[1] or ".mp4"
                filename = f"{file_name}_{timestamp}_{i}{ext}"
                
                remote_path = f"{bucket_folder_prefix}/{filename}".lstrip("/")

                print(f"[GCPVideoUploader] Uploading {local_path} → gs://{bucket_name}/{remote_path}")
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_path)

                file_size_bytes = os.path.getsize(local_path)
                size_mb = round(file_size_bytes / (1024 * 1024), 2)
                public_url = f"https://storage.googleapis.com/{bucket_name}/{remote_path}"

                uploaded_urls.append({
                    "url": public_url,
                    "filename": filename,
                    "size_mb": size_mb,
                    "subfolder": subfolder,
                    "type": self.type,
                })
        else:
            # Fallback: try to handle as list or single item
            if not isinstance(videos, list):
                videos = [videos]

            for i, video_data in enumerate(videos):
                # Determine save path
                ext = ".mp4"  # Default extension
                filename = f"{file_name}_{timestamp}_{i}{ext}"

                full_output_folder, _, _, subfolder, _ = folder_paths.get_save_image_path(
                    file_name, self.output_dir, 0, 0
                )
                local_path = os.path.join(full_output_folder, filename)

                # Save the video file
                # Check for ComfyUI VideoFromComponents or similar video objects
                if hasattr(video_data, '__dict__'):
                    print(f"[GCPVideoUploader] DEBUG - video_data attributes: {dir(video_data)}")
                    print(f"[GCPVideoUploader] DEBUG - video_data dict: {vars(video_data)}")
                
                if hasattr(video_data, 'path'):
                    # VideoFromComponents or similar object with path attribute
                    source_path = video_data.path
                    if os.path.exists(source_path):
                        shutil.copy(source_path, local_path)
                    else:
                        raise FileNotFoundError(f"[GCPVideoUploader] Video path not found: {source_path}")
                elif hasattr(video_data, 'filename'):
                    # Object with filename attribute
                    source_path = video_data.filename
                    if os.path.exists(source_path):
                        shutil.copy(source_path, local_path)
                    else:
                        raise FileNotFoundError(f"[GCPVideoUploader] Video file not found: {source_path}")
                elif hasattr(video_data, "save"):
                    video_data.save(local_path)
                elif isinstance(video_data, (bytes, bytearray)):
                    with open(local_path, "wb") as f:
                        f.write(video_data)
                elif isinstance(video_data, str) and os.path.exists(video_data):
                    shutil.copy(video_data, local_path)
                else:
                    raise ValueError(f"[GCPVideoUploader] Unsupported video input format. Type: {type(video_data)}, Value: {video_data}")

                remote_path = f"{bucket_folder_prefix}/{filename}".lstrip("/")

                print(f"[GCPVideoUploader] Uploading {local_path} → gs://{bucket_name}/{remote_path}")
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_path)

                file_size_bytes = os.path.getsize(local_path)
                size_mb = round(file_size_bytes / (1024 * 1024), 2)
                public_url = f"https://storage.googleapis.com/{bucket_name}/{remote_path}"

                uploaded_urls.append({
                    "url": public_url,
                    "filename": filename,
                    "size_mb": size_mb,
                    "subfolder": subfolder,
                    "type": self.type,
                })

        print(f"[GCPVideoUploader] Uploaded {len(uploaded_urls)} video(s) successfully.")
        return {
            "ui": {"uploaded_videos": uploaded_urls}
        }

NODE_CLASS_MAPPINGS = {
    "GCPImageUploader": GCPImageUploader,
    "GCPVideoUploader": GCPVideoUploader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GCPImageUploader": "🪣 Upload to GCP Bucket",
    "GCPVideoUploader": "Upload Video to GCP Bucket",
}
