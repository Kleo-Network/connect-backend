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
import requests

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
            
        query = """
			query {
				viewer {
					contributionsCollection {
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
		"""

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
        static_card = StaticCards(slug, 'GitCard', int(datetime.now().timestamp()), metadata = {"contribution":contribution})
        static_card.save()
        
        return jsonify({"message": f"Created static github card for user {slug}"}), 200
    
    except Exception as e:
        print(e)
        return jsonify({"error": "error while creating github card"}), 500