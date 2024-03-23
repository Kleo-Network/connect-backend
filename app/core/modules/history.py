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
    print(domain)
    payload = {'url': domain}
    response = requests.request("POST", url, headers={}, data=payload, files=[])
    return get_category(response)

def create_pending_cards(slug):
    history_from_db = get_history_item(slug)
    cluster_history_list = cluster_and_save(history_from_db)
    response_from_llm = create_card_from_llm(slug, cluster_history_list)
    
def cluster_and_save(data):
    # Prepare the result structure
    result_embeddings = {}

    for item in data:
        domain = item["domain"]
        if domain not in result_embeddings:
            result_embeddings[domain] = []
        result_embeddings[domain].append(item)
    
    return result_embeddings

def convert_to_json(text):
    try: 
        text = text.strip()
        result = []
        list = re.findall(r'\{(.*?)\}', text, re.DOTALL)
        for item in list:
            activity_pattern = r'"activity":\s*"([^"]*)"'
            act_match = re.search(activity_pattern, item)
            card_json = {"activity": "", "description": "", "entities":[]}
            if act_match:
                card_json["activity"] =  act_match.group(1)
        
            description_pattern = r'"description":\s*"([^"]*)"'
            desc_match = re.search(description_pattern, item)
            if desc_match:
                card_json["description"] = desc_match.group(1)
            
            entities_pattern = r'"entities":\s*(\[.*?\])'
            ent_match = re.search(entities_pattern, item)
        
            if ent_match:
                card_json["entities"] = json.loads(ent_match.group(1))
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
            "prompt": prompt + "  " + initial_prompt,
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
    
def create_card_from_llm(slug,data):
    initial_prompt = """
    Conversion of the above browsing history items into a specific JSON. 
    The JSON strictly conforms to this schema. 
    {
        "activity" : multiple possible verbs in past tense, 
        "entities": array of one word extracted entities,
        "description" : one or two sentences briefly describing possible motive and reason for activities
    }
    Create just one json object for the same. 
    """
    input_models = ["azure", "anyscale"]
    print(len(list(data.keys())))
    selected_domains = random.sample(list(data.keys()), len(list(data.keys())))
    cards_main=[]
    for domain in selected_domains:
        print('domain', domain)
        items = data[domain]
        prompt = ""
        items_list= []
        last_item = {}
        for item in items:
            prompt += json.dumps({"title": item["title"], "domain": item["domain"]}) + "\n"
            items_list.append({"title": item["title"], "url": item["url"]})
            last_item = item
            

            num_tokens = len(prompt) // 4

            if num_tokens > 4000:
                print(f"Skipping domain '{domain}' due to context size exceeding 2048 tokens.")
                continue

            bot_response = message_from_LLM_API(
                initial_prompt=initial_prompt,
                model_name="gpt-35-turbo-instruct",
                prompt=prompt, temperature=0.8, 
                base_url=os.environ.get('OPEN_AI_BASE_URL'),
                api_key=os.environ.get('OPEN_AI_API_KEY'), 
                service="azure")
            
            response_text_json = convert_to_json(bot_response["choices"][0]["text"])
            print(response_text_json)
            pendingCard = PendingCard(slug, "DataCard", response_text_json[0]["description"],
                                      response_text_json[0]["entities"], {"title": item["title"], "url": item["url"]},
                                      response_text_json[0])
            pendingCard.save()
            if delete_history(slug, item["id"]):
                cards_main.append({"cardType": "DataCard", 
                                "category": last_item["category"], 
                                "content": response_text_json[0]["description"], 
                                "date": last_item["visitTime"], 
                                "metadata": response_text_json[0], 
                                "tags": response_text_json[0]["entities"],
                                "items": items_list})
            else:
                print(f"error while deleting {item['id']} of {slug}")
            
    return cards_main