import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API endpoint for uploading images
IMGUR_UPLOAD_IMG_ENDPOINT = "https://api.imgur.com/3/image"

# Get Imgur Client ID from environment variables
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")


def upload_image_to_imgur(image_data):
    """
    Uploads base64 encoded image data to Imgur and returns the image URL.
    :param image_data: Base64 encoded image data (without data URL prefix).
    :return: URL of the uploaded image or None if upload fails.
    """
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    payload = {"image": image_data, "type": "base64"}

    try:
        response = requests.post(
            IMGUR_UPLOAD_IMG_ENDPOINT, headers=headers, data=payload
        )

        if response.status_code == 200:
            imgur_response = response.json()
            return imgur_response["data"]["link"]
        else:
            print(f"Error uploading image: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred while uploading image: {e}")
        return None
