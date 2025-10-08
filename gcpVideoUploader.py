from google.cloud import storage
import folder_paths
import os
import time
import shutil

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
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_service_json

        timestamp = int(time.time())
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        uploaded_urls = []

        # Ensure videos are iterable (can be multiple)
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

            # Save the video file (ComfyUI passes bytes-like or np array depending on node)
            if hasattr(video_data, "save"):
                video_data.save(local_path)
            elif isinstance(video_data, (bytes, bytearray)):
                with open(local_path, "wb") as f:
                    f.write(video_data)
            elif isinstance(video_data, str) and os.path.exists(video_data):
                shutil.copy(video_data, local_path)
            else:
                raise ValueError("[GCPVideoUploader] Unsupported video input format.")

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
    "GCPVideoUploader": GCPVideoUploader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GCPVideoUploader": "Upload Video to GCP Bucket",
}
