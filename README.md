# GCPImageUploader
## 🙏 Credits & Origin

This node is based on the original [ComfyUI-GCP-Storage](https://github.com/Fantaxico/ComfyUI-GCP-Storage.git) by Fantaxico.

> I created this version after fixing several bugs I ran into while using the original. Since the PR I opened wasn’t merged, I decided to release a clean standalone version to make it easier to use, update, and publish via ComfyUI Manager.

All credit to the original creator — this repo just contains fixes, improvements, and quality-of-life additions.

## Description:

A custom node for ComfyUI to save a image to your Google Cloud Platform Storage Bucket.

## Installation:

Use `git clone https://github.com/noobprograms/comfyui-gcp-uploader.git` in your ComfyUI custom nodes directory

## Usage

Requires a `config.json` file that has `{ "gcp_service_json_path": "xxx" }` set to your Service Account json file path (for reference see https://cloud.google.com/iam/docs/keys-create-delete).

Add the node to your workflow and enter a file name and your bucket name.

The node saves your image locally in `comfyUi/outputs` and then uploads it to GCP.
