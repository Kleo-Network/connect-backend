import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

IMGUR_UPLOAD_IMG_ENDPOINT = "https://api.imgur.com/3/image"
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
IMGBB_UPLOAD_IMG_ENDPOINT = f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}"


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


def upload_image_to_image_bb(image_data):
    payload = {"image": image_data}
    response = requests.post(IMGBB_UPLOAD_IMG_ENDPOINT, data=payload)

    if response.status_code == 200:
        response_data = response.json()
        if response_data.get("success"):
            return response_data["data"]["url_viewer"]
        else:
            raise Exception("Image upload unsuccessful.")
