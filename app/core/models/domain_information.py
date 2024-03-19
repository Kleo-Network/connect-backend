from datetime import datetime
from flask import jsonify
from mongoengine import Document, StringField, DateTimeField, IntField

class DomainInformation(Document):
	user_address = StringField(required=True)
	domain = StringField()
	date = DateTimeField(required=True, default=datetime.now(datetime.UTC))
	counter = IntField(default=1)
	topic = StringField()
	category = StringField()
  
def create_domain_information_by_user_address(user_address, domain, date, visits):
    domain_information = DomainInformation(
		user_address=user_address,
  		domain=domain,
    	date=date,
		visits=visits
	)
    DomainInformation.save()
    return domain_information

def delete_domain_information_by_user_address(user_address):
    deleted_domain_information_count = DomainInformation.object(user_address=user_address).delete()
    if deleted_domain_information_count:
        return jsonify({'message': f'All domain information for user {user_address} deleted successfully'})
    return jsonify({'error': f'No domain information found for the user {user_address}'}), 404
    
