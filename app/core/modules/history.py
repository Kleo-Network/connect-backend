import math
from bs4 import BeautifulSoup as bs
from flask import jsonify
from urllib.parse import urlparse
from ..models.history import *
from ..models.pending_cards import *

import requests
import json
import re
import openai
import random
import os

categories_to_exclude = [
    "Abortion", "Alcohol", "Marijuana", "Nudity and Risque", "Other Adult Materials",
    "Pornography", "Tobacco", "Weapons (Sales)", "Child Sexual Abuse", "Discrimination",
    "Drug Abuse", "Explicit Violence", "Extremist Groups", "Illegal or Unethical",
    "Plagiarism", "Potentially Unwanted Program", "Terrorism", "Malicious Websites",
    "Phishing", "Spam URLs", "Web-based Email", "Web Chat", "Online Meeting","Instant Messaging","File Sharing and Storage"
]

tags = {
 "Lifestyle": [
   "Dating",
   "Gambling",
   "Lingerie and Swimsuit",
   "Sports Hunting and War Games",
   "Health and Wellness",
   "Restaurant and Dining",
   "Shopping",
   "Society and Lifestyles",
   "Travel"
 ],
 "Entertainment": [
   "Internet Radio and TV",
   "Streaming Media and Download",
   "Arts and Culture",
   "Entertainment",
   "Folklore",
   "Games",
   "Global Religion"
 ],
 "Education & Beliefs": [
   "Advocacy Organizations",
   "Alternative Beliefs",
   "Sex Education",
   "Child Education",
   "Education",
   "Reference"
 ],
 "Technology": [
   "File Sharing and Storage",
   "Freeware and Software Downloads",
   "Internet Telephony",
   "Peer-to-peer File Sharing",
   "Artificial Intelligence Technology",
   "Information Technology",
   "Information and Computer Security",
   "Remote Access",
   "Search Engines and Portals",
   "Secure Websites",
   "URL Shortening",
   "Web Analytics",
   "Web Hosting",
   "Web-based Applications",
   "Dynamic Content",
   "Crypto Mining",
   "Hacking",
   "Proxy Avoidance",
   "Dynamic DNS"
 ],
 "Business & Finance": [
   "Business",
   "Charitable Organizations",
   "Cryptocurrency",
   "Finance and Banking",
   "Auction",
   "Brokerage and Trading",
   "Job Search",
   "Real Estate"
 ],
 "Government": [
   "Armed Forces",
   "General Organizations",
   "Government and Legal Organizations",
   "Political Organizations"
 ],
 "Media & Communication": [
   "Advertising",
   "Content Servers",
   "Digital Postcards",
   "Domain Parking",
   "News and Media",
   "Newsgroups and Message Boards",
   "Personal Websites and Blogs",
   "Social Networking"
 ],
 "Personal": [
   "Personal Privacy",
   "Personal Vehicles",
   "Meaningless Content"
 ],
 "Health & Medicine": [
   "Medicine"
 ],
 "Miscellaneous": [
   "Newly Observed Domain",
   "Newly Registered Domain",
   "Not Rated"
 ]
}

def get_tags_from_category(tag_map, category):
    for tag, cats in tag_map.items():
        if category in cats:
            return tag
    return "Miscellaneous"

keys_to_keep = ["visitTime", "category", "title", "url", "domain", "id"]

# Function to clean individual item
def clean_item(item):
    cleaned_item = {key: item[key] for key in keys_to_keep if key in item}
    return cleaned_item if cleaned_item["category"] not in categories_to_exclude else None

def get_category(raw_resp):
    try:
        soup = bs(raw_resp.text)
        result = soup.find("div", {"id": "webfilter-result"})
        paragraph = result.select_one("div > p").getText()
        main_result = result.find("h4", {"class": "info_title"})
        category_description = paragraph.split("Group:")[0].strip()
        category_group = paragraph.split("Group:")[1].strip()
        category = main_result.getText().split("Category:")[1].strip()
        return category_group, category_description, category
    except:
        return "Other", "Unknown", "Other"


def single_url_request(domain):
    url = "https://www.fortiguard.com/webfilter"
    
    payload = {'url': domain}
    response = requests.request("POST", url, headers={}, data=payload, files=[])
    return get_category(response)

def create_pending_cards(slug):
    history_from_db = get_history_item(slug)
    if not history_from_db:
        return
    cluster_history_list = cluster_and_save(history_from_db)
    if not cluster_history_list:
        return
    response_from_llm = create_card_from_llm(slug, cluster_history_list)
    
def cluster_and_save(data):
    # Prepare the result structure
    # Clean the data and remove duplicates based on title
    titles_seen = set()
    cleaned_data = []
    final_data = {}
    categories_json = {}

    for item in data:
        cleaned_item = clean_item(item)
        if cleaned_item and cleaned_item["title"] not in titles_seen:
            titles_seen.add(cleaned_item["title"])
            cleaned_data.append(cleaned_item)
            
            if cleaned_item and cleaned_item["category"] in categories_json:
                categories_json[cleaned_item["category"]] += 1
            elif cleaned_item:
                categories_json[cleaned_item["category"]] = 1
    
    # Determine the new file name
    final_data["items"] = cleaned_data
    final_data["frequency"] = categories_json
    
    return final_data

def convert_to_json(text):
    try:
        text = text.strip()
        result = []
        patterns = [
            r'"activity"\s*:\s*"((?:[^"\\]|\\.)*)"',
            r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"',
            r'"entities"\s*:\s*(\[(?:[^]\\]|\\.)*\])'
        ]
        matches = re.findall(r'{(.*?)}', text, re.DOTALL)
        for match in matches:
            card_json = {"activity": "", "description": "", "entities": []}
            for i, pattern in enumerate(patterns):
                value = re.search(pattern, match, re.DOTALL)
                if value:
                    if i == 0 and value.group(1).strip():
                        card_json["activity"] = value.group(1).replace('\\n', '\n')
                    elif i == 1 and value.group(1).strip():
                        card_json["description"] = value.group(1).replace('\\n', '\n')
                    elif i == 2:
                        entities_str = value.group(1).replace('\\n', '\n')
                        entities = json.loads(entities_str)
                        if entities:
                            card_json["entities"] = entities
            if card_json["activity"] or card_json["description"] or card_json["entities"]:
                result.append(card_json)
        return result
    except:
        return [{"activity": "Error", "description": "Error", "entities": ["Error"]}]
    
def message_from_LLM_API(
    initial_prompt, model_name, prompt, temperature, base_url, api_key, service
):
    if service == "azure":
        headers = { "Content-Type": "application/json", "api-key": f"{api_key}" }
        data = {
            "messages":[
                {"role": "system", "content": initial_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": temperature,
            "top_p": 0.8
        }
        response = requests.post(base_url, headers=headers, json=data)
        print(response.json())
        return response.json()
    elif service == "ansycale":
        client = openai.OpenAI(base_url=base_url, api_key=api_key)
        chat_completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": initial_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
        return chat_completion.choices[0].message.content
    
def get_category_cards(data, num_cards):

    frequency_data = data["frequency"]

    total_frequency = sum(frequency_data.values())

    category_ratios = {category: (freq / total_frequency) * num_cards for category, freq in frequency_data.items()}

    category_cards = {}

    for category, ratio in category_ratios.items():
        if category in ["Social Networking", "Streaming Media and Download"]:
            category_cards[category] = max(0, math.floor(ratio))  # Ensure a minimum count of 0
        else:
            category_cards[category] = math.ceil(ratio)

    while sum(category_cards.values()) != num_cards:
        if sum(category_cards.values()) < num_cards:
            max_diff_category = max(category_ratios, key=lambda x: category_ratios[x] - category_cards[x])
            category_cards[max_diff_category] += 1
        else:
            min_diff_category = min(category_ratios, key=lambda x: category_cards[x] - category_ratios[x] if category_cards[x] > 0 else float('inf'))
            category_cards[min_diff_category] -= 1

    return category_cards

def get_titles_and_items_by_category(data, category):
    titles = []
    items = []
    for item in data['items']:
        if item['category'] == category:
            titles.append(item['title'])
            items.append(item)

    return titles, items

def generate_results(slug, items, initial_prompt, input_service):
    cards_main = []
    items_list = []
    prompt = ''
    for item in items:
        prompt += json.dumps({"title": item["title"], "domain": item["domain"]}) + "\n"
        items_list.append({"title": item["title"], "url": item["url"], "id": item["id"]})

    num_tokens = len(prompt) // 4
    if num_tokens > 4000:
        Exception 

    bot_response = message_from_LLM_API(
            initial_prompt=initial_prompt,
            model_name="gpt-4",
            prompt=prompt,
            temperature=0.8,
            base_url=os.environ.get('OPEN_AI_BASE_URL'),
            api_key=os.environ.get('OPEN_AI_API_KEY'),
            service=input_service
        )
    if "choices" in bot_response and len(bot_response["choices"]) > 0 and "message" in bot_response["choices"][0] and "content" in bot_response["choices"][0]["message"]:
        response_text_json = convert_to_json(bot_response["choices"][0]["message"]["content"])
    else: 
        response_text_json = []
    
    if len(response_text_json) > 0:
        for card_data in response_text_json:
            card = {
                "cardType": "DataCard",
                "content": card_data["description"],
                "metadata": card_data,
                "tags": card_data["entities"],
                "urls": items_list
            }
            pendingCard = PendingCard(slug, "DataCard", card_data["description"],
                                      card_data["entities"], items_list,
                                      card_data, get_tags_from_category(tags, items[0]["category"]))
            pendingCard.save()
            for item in items_list:
                if delete_history(slug, item["id"]): #We protect user privacy by deleting history once we create pending cards
                    cards_main.append(card)
                else:
                    print(f"error while deleting {item['id']} of {slug}")
                    
    return cards_main

    
def create_card_from_llm(slug,data):
    initial_prompt = """
    Conversion of the above browsing history items into specific JSON. 
    The JSON strictly conforms to this schema. 
    {
        "activity" : multiple possible verbs in past tense, 
        "entities": array of one word extracted entities,
        "description" : one or two sentences briefly describing possible motive and reason for activities, all verbs should be in past tense
    }
    """
    number_of_cards_category = get_category_cards(data, 15)
    print(number_of_cards_category)
    final_results = []
    for category, num_cards in number_of_cards_category.items():
        if num_cards > 0:
            if num_cards == 1:
                titles, items = get_titles_and_items_by_category(data, category=category)
                res = generate_results(slug, items, initial_prompt, 'azure')
                final_results.append(res)
            if num_cards >= 2:
                titles, items = get_titles_and_items_by_category(data, category=category)
                initial_prompt += "Create {} clusters based on context, for each cluster create a card in this format,".format(num_cards)
                res = generate_results(slug, items, initial_prompt, 'azure')
                final_results.append(res)
    return final_results