from mongoengine import Document, StringField, DateTimeField
from datetime import datetime

class History(Document):
	user_address = StringField(required=True)
	create_timestamp = DateTimeField(default=datetime.now(datetime.UTC))
	title = StringField()
	summary = StringField()
	category = StringField()
	subcategory = StringField()
	url = StringField()
	domain = StringField()
  
def create_history_by_user_address(user_address, create_timestamp, title, category, subcategory, url, domain):
	history = History(
		user_address=user_address,
		create_timestamp=create_timestamp,
		title=title,
		category=category,
		subcategory=subcategory,
		url=url,
		domain=domain
	)
	History.save()
	return history

def get_history_by_user_address(user_address):
    return History.object(user_address=user_address)
