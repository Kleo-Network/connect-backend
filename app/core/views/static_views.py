from flask import Blueprint, current_app, request, jsonify
from ..controllers.user import *
from werkzeug.local import LocalProxy
from ..controllers.user import * 
core = Blueprint('core', __name__)
from .auth_views import *
from ..controllers.checks import * 
from ..models.pending_cards import *
from ..models.published_cards import *
from ..models.static_cards import *
from datetime import datetime, timedelta
import requests
import os

logger = LocalProxy(lambda: current_app.logger)

#Calandly urls
CALENDLY_USER_URL = 'https://api.calendly.com/users/me'
#Github urls
GIHUB_AUTH_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'

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
        last_month = today - timedelta(days=90)
            
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
        token = data.get("token")
        max_photos = 3 
        
        if not all([slug, token]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "user is not found"}), 401
        address_from_token = kwargs.get('user_data')['payload']['publicAddress']
        if not check_user_authenticity(address, address_from_token):
            return jsonify({"error": "user is not authorised"}), 401
        
        response = requests.get(
            f"https://graph.instagram.com/me/media?fields=id,caption,media_url&access_token={token}"
        )

        if response.status_code == 200:
            media_data = response.json().get('data', [])
            
            if media_data:
                # Select a random photo from the user's media
                random.shuffle(media_data)
                random_photos = [media.get('media_url', '') for media in media_data[:max_photos]]
                staticCard = StaticCards(slug, 'InstaCard', int(datetime.now().timestamp()), metadata={
                    'urls' : random_photos
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
        
        print(response.json())
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
        
        print('test',user_response.json())
        if user_response.status_code == 200:
            user_data = user_response.json()
            print('data',user_data)
            bio = user_data.get('data', {}).get('description', '')
            pinned_tweet = user_data.get('includes', {}).get('tweets', [{}])[0].get('text', '')
            is_verified = user_data.get('data', {}).get('verified', False)
            followers_count = user_data.get('data', {}).get('public_metrics', {}).get('followers_count', 0)

            x_meta_data = {
                'bio': bio,
                'pinned_tweet': pinned_tweet,
                'is_verified': is_verified,
                'followers_count': followers_count
            }
            static_card = StaticCards(slug, 'XCard', int(datetime.now().timestamp()), metadata=x_meta_data)
            static_card.save()
            
            return jsonify({'message': f'X card created for user {slug}'}) , 200
        else:
            return jsonify({'error': 'Failed to fetch user data from Twitter API'}), 500
        
    except Exception as e:
        print(e)
        return jsonify({"error": "error while creating instagram card"}), 500