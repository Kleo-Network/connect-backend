from flask import Blueprint, current_app, request, jsonify
from ..controllers.history import *
from werkzeug.local import LocalProxy
core = Blueprint('core', __name__)
from .auth_views import *
from ..models.pending_cards import *
from ..models.published_cards import *
from ..models.static_cards import *
from datetime import datetime, timedelta
import requests
import os
import boto3
import uuid

logger = LocalProxy(lambda: current_app.logger)

#Calandly urls
CALENDLY_USER_URL = 'https://api.calendly.com/users/me'
#Github urls
GIHUB_AUTH_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'
INSTAGRAM_AUTH_TOKEN_URL = 'https://api.instagram.com/oauth/access_token'

AWS_ACCESS_KEY = os.environ.get('API_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_REGION = os.environ.get('AWS_DEFAULT_REGION')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION
)

@core.route('/calendly/<string:slug>', methods=["POST"])
@token_required
def create_calendly_cards(slug,**kwargs):
    try:
        # Get JSON data from request body
        data = request.get_json()
        token = data.get("token")
        
        if not all([slug, token]):
            return jsonify({"error": "Missing required parameters"}), 400
        print(token)
        
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "user is not found"}), 401
        address_from_token = kwargs.get('user_data')['payload']['publicAddress']
        if not check_user_authenticity(address, address_from_token):
            return jsonify({"error": "user is not authorised"}), 401
        
        headers = {
			'Authorization': f'Bearer {token}'
		}
        response = requests.get(CALENDLY_USER_URL, headers=headers)
        print(response.json())
        user_data = response.json()
        if not user_data:
            return jsonify({"error": "Error while creating calendly card"}), 400
        user_slug = user_data['resource']['slug']
        
        # Create StaticCards instance and save to database
        static_card = StaticCards(slug, 'CalendarCard', int(datetime.now().timestamp()), metadata = {"slug":user_slug})
        static_card.save()
        
        return jsonify({"message": f"Created static calendly card for user {slug}"}), 200
    
    except Exception as e:
        print(e)
        return jsonify({"error": "error while creating calendly card"}), 500
    
    
@core.route('/github/<string:slug>', methods=["POST"])
@token_required
def create_github_cards(slug,**kwargs):
    try:
        # Get JSON data from request body
        data = request.get_json()
        code = data.get("code")
        
        if not all([slug, code]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "user is not found"}), 401
        address_from_token = kwargs.get('user_data')['payload']['publicAddress']
        if not check_user_authenticity(address, address_from_token):
            return jsonify({"error": "user is not authorised"}), 401
        
        git_auth_params = {
			"client_id": os.environ.get("GITHUB_CLIENT_ID"),
			"client_secret": os.environ.get("GITHUB_CLIENT_SECRET"),
			"code": code
		}
        token_response = requests.post(GIHUB_AUTH_TOKEN_URL, json=git_auth_params, headers={'Accept': 'application/json'})
        
        access_token = token_response.json().get('access_token')

        if not access_token:
            return jsonify({"error": "error while fetching access token of github"}), 500
            # Construct GraphQL query
            
        headers = {'Authorization': f'token {access_token}'}
        response = requests.get('https://api.github.com/user', headers=headers)
        gitUserData = response.json()
            
        today = datetime.now()
        last_month = get_last_third_month_start_date()
            
        query = """
			query {
				viewer {
					contributionsCollection(from: "%s", to: "%s") {
						contributionCalendar {
							weeks {
								contributionDays {
									date
									contributionCount
								}
							}
						}
					}
				}
			}
		""" % (last_month.isoformat(), today.isoformat())

        # Make request to GitHub GraphQL API
        graphql_response = requests.post(
			GITHUB_GRAPHQL_URL,
			json={'query': query},
			headers={'Authorization': f'Bearer {access_token}'}
		)
        commit_data = graphql_response.json().get('data', {}).get('viewer', {}).get('contributionsCollection', {}).get('contributionCalendar', {}).get('weeks', [])
        
        contribution = [
			{"count": item["contributionCount"], "date": item["date"]}
			for sublist in commit_data
			for item in sublist["contributionDays"]
		]
        
        if not contribution:
            return jsonify({"error": f"Error while fetching contribution from github for {slug}"}), 400
        
        # Create StaticCards instance and save to database
        static_card = StaticCards(slug, 'GitCard', int(datetime.now().timestamp()), metadata = {
            "contribution":contribution,
            "userName":gitUserData['login'],
            "url": gitUserData['html_url'],
            "followers": gitUserData['followers'],
            "following":gitUserData['following']})
        static_card.save()
        
        return jsonify({"message": f"Created static github card for user {slug}"}), 200
    
    except Exception as e:
        print(e)
        return jsonify({"error": "error while creating github card"}), 500
    
@core.route('/instagram/<string:slug>', methods=["POST"])
@token_required
def create_insta_cards(slug,**kwargs):
    try:
        # Get JSON data from request body
        data = request.get_json()
        code = data.get("code")
        
        max_photos = 3 
        
        if not all([slug, code]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "user is not found"}), 401
        address_from_token = kwargs.get('user_data')['payload']['publicAddress']
        if not check_user_authenticity(address, address_from_token):
            return jsonify({"error": "user is not authorised"}), 401
        
        
        insta_auth_params = {
			'client_id': os.environ.get("INSTAGRAM_CLIENT_ID"),
			'client_secret': os.environ.get("INSTAGRAM_CLIENT_SECRET"),
            'grant_type': "authorization_code",
            'redirect_uri': os.environ.get('REDIRECT_URI'),
			'code': code
		}
        token_response = requests.post(INSTAGRAM_AUTH_TOKEN_URL, data=insta_auth_params, headers={'Accept': 'application/json'})
        print(token_response.json())
        
        token = token_response.json().get('access_token')

        if not token:
            return jsonify({"error": "error while fetching access token of instagram"}), 500
            # Construct GraphQL query
        
        response = requests.get(
            f"https://graph.instagram.com/me/media?fields=id,caption,media_url,username&access_token={token}"
        )

        if response.status_code == 200:
            media_data = response.json().get('data', [])
            
            if media_data:
                # Select a random photo from the user's media
                random.shuffle(media_data)
                random_photos = []
                for media in media_data[:max_photos]:

                    try:
                        # Fetch the image data from the URL
                        image_response = requests.get(media['media_url'])
                        image_response.raise_for_status()
                        image_data = image_response.content
                        print(image_data)

                        # Generate a random key for the image
                        image_key = f"{uuid.uuid4()}.jpg"

                        # Upload the image to S3
                        s3.put_object(
                            Bucket=S3_BUCKET_NAME,
                            Key=image_key,
                            Body=image_data,
                            ContentType='image/jpeg'
                        )

                        # Generate the public URL
                        image_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{image_key}"

                        obj = {
                            'url': image_url,
                            'caption': media['caption']
                        }
                        random_photos.append(obj)
                    
                    except Exception as e:
                        print(e)
                        continue

                staticCard = StaticCards(slug, 'InstaCard', int(datetime.now().timestamp()), metadata={
                    'urls' : random_photos,
                    'username' : media_data[0]['username']
                })
                staticCard.save()
                return jsonify({'message': f'insta card generated for {slug}'}), 200
            else:
                return jsonify({'message': f'No media found for the {slug}'})
        else:
            return jsonify({'error': f'Failed to fetch media data from Instagram for user {slug}'})
    
    except Exception as e:
        print(e)
        return jsonify({"error": "error while creating instagram card"}), 500
    
@core.route('/x/<string:slug>', methods=["POST"])
@token_required
def create_x_cards(slug,**kwargs):
    try:
        # Get JSON data from request body
        data = request.get_json()
        code = data.get("code")
        
        if not all([slug, code]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "user is not found"}), 401
        address_from_token = kwargs.get('user_data')['payload']['publicAddress']
        if not check_user_authenticity(address, address_from_token):
            return jsonify({"error": "user is not authorised"}), 401
        
        payload = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': os.environ.get('X_CLIENT_ID'),
            'redirect_uri': os.environ.get('REDIRECT_URI'),
            'code_verifier': 'challenge'
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            # No need to set Access-Control-Allow-Origin here, as it is a response header controlled by the server
        }

        response = requests.post('https://api.twitter.com/2/oauth2/token', data=payload, headers=headers)
        
        token = response.json().get('access_token')
        print('token',token)    
        
        user_response = requests.get(
            'https://api.twitter.com/2/users/me',
            headers={
                'Authorization': f'Bearer {token}'
            },
            params={
                'user.fields': 'description,pinned_tweet_id,verified,public_metrics',
                'tweet.fields': 'text',
                'expansions': 'pinned_tweet_id'
            }
        )
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print('data',user_data)
            username = user_data.get('data', {}).get('username', '')
            bio = user_data.get('data', {}).get('description', '')
            pinned_tweet = user_data.get('includes', {}).get('tweets', [{}])[0].get('text', '')
            is_verified = user_data.get('data', {}).get('verified', False)
            followers_count = user_data.get('data', {}).get('public_metrics', {}).get('followers_count', 0)
            following_count = user_data.get('data', {}).get('public_metrics', {}).get('following_count', 0)            

            x_meta_data = {
                'username': username,
                'bio': bio,
                'pinned_tweet': pinned_tweet,
                'is_verified': is_verified,
                'followers_count': followers_count,
                'following_count': following_count
            }
            static_card = StaticCards(slug, 'XCard', int(datetime.now().timestamp()), metadata=x_meta_data)
            static_card.save()
            
            return jsonify({'message': f'X card created for user {slug}'}) , 200
        else:
            return jsonify({'error': 'Failed to fetch user data from Twitter API'}), 500
        
    except Exception as e:
        print(e)
        return jsonify({"error": "error while creating instagram card"}), 500
    