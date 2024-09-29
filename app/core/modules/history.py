import logging
import math

logging.basicConfig(level=logging.ERROR)

from datetime import timedelta
from app.core.models.visits import fetch_visits_for_last_15_days, fetch_visits_for_week
from ..models.history import *

import requests
import json
import openai
import os
from pydantic_core import from_json

from pydantic import BaseModel
import time


class CardObject(BaseModel):
    activity: str
    description: str
    tags: list
    titles: list


categories_to_exclude = [
    "Abortion",
    "Alcohol",
    "Marijuana",
    "Nudity and Risque",
    "Other Adult Materials",
    "Pornography",
    "Tobacco",
    "Weapons (Sales)",
    "Child Sexual Abuse",
    "Discrimination",
    "Drug Abuse",
    "Explicit Violence",
    "Extremist Groups",
    "Illegal or Unethical",
    "Plagiarism",
    "Potentially Unwanted Program",
    "Terrorism",
    "Malicious Websites",
    "Phishing",
    "Spam URLs",
    "Web-based Email",
    "Web Chat",
    "Online Meeting",
    "Instant Messaging",
    "File Sharing and Storage",
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
        "Travel",
    ],
    "Entertainment": [
        "Internet Radio and TV",
        "Streaming Media and Download",
        "Arts and Culture",
        "Entertainment",
        "Folklore",
        "Games",
        "Global Religion",
    ],
    "Education & Beliefs": [
        "Advocacy Organizations",
        "Alternative Beliefs",
        "Sex Education",
        "Child Education",
        "Education",
        "Reference",
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
        "Dynamic DNS",
    ],
    "Business & Finance": [
        "Business",
        "Charitable Organizations",
        "Cryptocurrency",
        "Finance and Banking",
        "Auction",
        "Brokerage and Trading",
        "Job Search",
        "Real Estate",
    ],
    "Government": [
        "Armed Forces",
        "General Organizations",
        "Government and Legal Organizations",
        "Political Organizations",
    ],
    "Media & Communication": [
        "Advertising",
        "Content Servers",
        "Digital Postcards",
        "Domain Parking",
        "News and Media",
        "Newsgroups and Message Boards",
        "Personal Websites and Blogs",
        "Social Networking",
    ],
    "Personal": ["Personal Privacy", "Personal Vehicles", "Meaningless Content"],
    "Health & Medicine": ["Medicine"],
    "Miscellaneous": ["Newly Observed Domain", "Newly Registered Domain", "Not Rated"],
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
    return (
        cleaned_item if cleaned_item["category"] not in categories_to_exclude else None
    )


# def get_category(raw_resp):
#     try:
#         soup = bs(raw_resp.text, 'html.parser')
#         result = soup.find("div", {"id": "webfilter-result"})
#         if result is None:
#             raise ValueError("Could not find the 'webfilter-result' div in the response.")
#         paragraph = result.select_one("div > p")
#         if paragraph is None:
#             raise ValueError("Could not find the paragraph element within the 'webfilter-result' div.")
#         main_result = result.find("h4", {"class": "info_title"})
#         if main_result is None:
#             raise ValueError("Could not find the 'info_title' element within the 'webfilter-result' div.")
#         category_description = paragraph.getText().split("Group:")[0].strip()
#         category_group = paragraph.getText().split("Group:")[1].strip()
#         category = main_result.getText().split("Category:")[1].strip()
#         return category_group, category_description, category
#     except (AttributeError, IndexError) as e:
#         print(f"Error occurred while parsing the response: {str(e)}")
#         return "Other", "Unknown", "Other"
#     except ValueError as e:
#         print(str(e))
#         return "Other", "Unknown", "Other"
#     except Exception as e:
#         print(f"An unexpected error occurred: {str(e)}")
#         return "Other", "Unknown", "Other"


# def single_url_request(domain):
#     try:
#         url = "https://www.fortiguard.com/webfilter"
#         payload = {'url': domain}
#         response = requests.request("POST", url, headers={}, data=payload, files=[])
#         print(response.text)
#         return get_category(response)
#     except requests.exceptions.RequestException as e:
#         print(f"Error occurred while making request to {url}: {str(e)}")
#         return None
#     except Exception as e:
#         print(f"An unexpected error occurred: {str(e)}")
#         return None


def single_url_request(domain):
    try:
        url = f"https://website-categorization-api-now-with-ai.p.rapidapi.com/website-categorization/{domain}"
        headers = {
            "X-RapidAPI-Key": "Os4X7YlgE2mshuPlMvD8ROAkCNApp1Uhbqpjsnno2qXlvgJ0gW",
            "X-RapidAPI-Host": "website-categorization-api-now-with-ai.p.rapidapi.com",
        }
        response = requests.get(url, headers=headers)
        response_json = response.json()

        if "categories" in response_json:
            categories = response_json["categories"]
            if len(categories) > 0:
                highest_confidence_category = max(
                    categories, key=lambda x: x["confidence"]
                )
                return (
                    highest_confidence_category["name"],
                    "",
                    highest_confidence_category["name"],
                )
            else:
                return "Other", "Unknown", "Other"
        else:
            return "Other", "Unknown", "Other"
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while making request to {url}: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None


def create_pending_cards(slug):
    if datetime.today().weekday() == 0:  # Check if today is Monday
        last_week_start, last_week_end = get_date_range(1)
        last_to_last_week_start, last_to_last_week_end = get_date_range(2)

        last_week_visits = fetch_visits_for_week(slug, last_week_start, last_week_end)
        last_to_last_week_visits = fetch_visits_for_week(
            slug, last_to_last_week_start, last_to_last_week_end
        )

        deviations = calculate_deviation(last_week_visits, last_to_last_week_visits)
        top_domains = sorted(
            deviations.items(), key=lambda item: item[1], reverse=True
        )[:3]

        for domain, deviation in top_domains:
            last_week_count = last_week_visits[domain]
            last_to_last_week_count = last_to_last_week_visits.get(domain, 0)
            create_visit_count_card(
                slug,
                domain,
                deviation,
                last_week_count,
                last_to_last_week_count,
                format_date_range(
                    int(last_week_start.timestamp()), int(last_week_end.timestamp())
                ),
            )

    today = datetime.today()
    if today.day == 1 or today.day == 15:
        start_date = (today - timedelta(days=15)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        top_domains = fetch_visits_for_last_15_days(slug)
        if top_domains:
            create_visit_chart_card(slug, top_domains, start_date, end_date)

    history_from_db = get_history_item(slug)
    print("Step 1")
    if not history_from_db:
        return
    cluster_history_list = cluster_and_save(history_from_db)
    print("Step 2")
    if not cluster_history_list:
        return
    response_from_llm = create_card_from_llm(slug, cluster_history_list)
    print(response_from_llm)
    return response_from_llm


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


def message_from_LLM_API(
    initial_prompt,
    model_name,
    prompt,
    temperature,
    base_url,
    api_key,
    service,
    max_tokens=200,
):
    max_retries = 3
    retry_delay = 600  # seconds

    for attempt in range(max_retries):
        try:
            if service == "azure":
                headers = {"Content-Type": "application/json", "api-key": f"{api_key}"}
                data = {
                    "messages": [
                        {"role": "system", "content": initial_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.8,
                }
                response = requests.post(base_url, headers=headers, json=data)
                response_json = response.json()

                if (
                    "error" in response_json
                    and response_json["error"].get("code") == "429"
                ):
                    if attempt < max_retries - 1:  # don't sleep on the last attempt
                        logging.warning(
                            f"Rate limit exceeded. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(retry_delay)
                        continue
                else:
                    logging.info(f"Azure API response: {response_json}")
                    return response_json

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
                logging.info(f"Ansycale API response: {chat_completion}")
                return chat_completion.choices[0].message.content

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logging.error(
                    f"Request failed. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})"
                )
                logging.error(f"Error details: {str(e)}")
                time.sleep(retry_delay)
            else:
                logging.error(f"All retry attempts failed. Last error: {str(e)}")
                raise

    # If we've exhausted all retries, return the last error response
    logging.error(f"All retry attempts failed. Last response: {response_json}")
    return response_json


def get_category_cards(data, num_cards):
    frequency_data = data["frequency"]
    total_frequency = sum(frequency_data.values())
    category_ratios = {
        category: (freq / total_frequency) * num_cards
        for category, freq in frequency_data.items()
    }
    category_cards = {}
    for category, ratio in category_ratios.items():
        if category in ["Social Networking", "Streaming Media and Download"]:
            category_cards[category] = max(
                0, math.floor(ratio)
            )  # Ensure a minimum count of 0
        else:
            category_cards[category] = math.ceil(ratio)

    while sum(category_cards.values()) != num_cards:
        if sum(category_cards.values()) < num_cards:
            max_diff_category = max(
                category_ratios, key=lambda x: category_ratios[x] - category_cards[x]
            )
            category_cards[max_diff_category] += 1
        else:
            min_diff_category = min(
                category_ratios,
                key=lambda x: (
                    category_cards[x] - category_ratios[x]
                    if category_cards[x] > 0
                    else float("inf")
                ),
            )
            category_cards[min_diff_category] -= 1

    return category_cards


def get_titles_and_items_by_category(data, category):
    titles = []
    items = []
    for item in data["items"]:
        if item["category"] == category:
            titles.append(item["title"])
            items.append(item)

    return titles, items


def generate_results(slug, items, initial_prompt, input_service, max_tokens=100):
    cards_main = []
    prompt = ""
    for item in items:
        prompt += json.dumps({"title": item["title"], "domain": item["domain"]}) + "\n"

    num_tokens = len(prompt) // 4
    if num_tokens > 4000:
        return

    bot_response = message_from_LLM_API(
        initial_prompt=initial_prompt,
        model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
        prompt=prompt,
        temperature=0.8,
        base_url=os.environ.get("OPEN_AI_BASE_URL"),
        api_key=os.environ.get("OPEN_AI_API_KEY"),
        service=input_service,
        max_tokens=max_tokens,
    )
    print(bot_response)
    if (
        "choices" in bot_response
        and len(bot_response["choices"]) > 0
        and "message" in bot_response["choices"][0]
        and "content" in bot_response["choices"][0]["message"]
    ):
        response_text_json = from_json(
            bot_response["choices"][0]["message"]["content"], allow_partial=True
        )
        if isinstance(response_text_json, dict):
            response_text_json = [response_text_json]
    else:
        response_text_json = []

    print(response_text_json)
    if response_text_json is not None and len(response_text_json) > 0:
        for card_data in response_text_json:
            try:
                validated_card_data = CardObject.model_validate(card_data)
            except ValidationError as e:
                logging.error(
                    f"Validation error for card data in slug: {slug}. Error: {str(e)}"
                )
                logging.error(f"Problematic card data: {card_data}")
                continue  # Skip this card and continue with the next one

            items_list = []
            for item in items:
                if "titles" in validated_card_data.dict() and item["title"].lower() in [
                    title.lower() for title in validated_card_data.titles
                ]:
                    items_list.append(
                        {"title": item["title"], "url": item["url"], "id": item["id"]}
                    )

            card = {
                "cardType": "DataCard",
                "content": validated_card_data.description,
                "metadata": validated_card_data.dict(),
                "tags": validated_card_data.tags,
                "urls": items_list,
            }

            try:
                pendingCard = PendingCard(
                    slug,
                    "DataCard",
                    validated_card_data.description,
                    validated_card_data.tags,
                    items_list,
                    validated_card_data.dict(),
                    get_tags_from_category(tags, items[0]["category"]),
                )
                pendingCard.save()
                for item in items_list:
                    cards_main.append(card)
            except Exception as e:
                logging.error(
                    f"Error while saving or processing PendingCard for slug: {slug}. Error: {str(e)}"
                )

    return cards_main


def create_card_from_llm(slug, data):

    initial_prompt_single_card = """
        Pick one specific context from the history having at maximum 4 titles, ignore other items.
        The JSON strictly conforms to this schema.
        {{
            "activity" : verb,
            "tags": [2-3 categories]
            "description": describe one-two-line motive, reason or interest for @{slug}
            "titles": [related titles to this context]
        }}
        Use past tense for verbs
    """.format(
        slug=slug
    )

    initial_prompt_multiple_card = """
        The JSON object strictly conforms to this schema.
        {{
            "activity" : verb,
            "tags": [2-3 categories]
            "description": describe one-two-line motive, reason or interest for @{slug}
            "titles": [related titles in this cluster context]
        }}
        Use past tense for verbs
    """.format(
        slug=slug
    )

    number_of_cards_category = get_category_cards(data, 15)
    final_results = []
    for category, num_cards in number_of_cards_category.items():
        if num_cards > 0:
            if num_cards == 1:
                titles, items = get_titles_and_items_by_category(
                    data, category=category
                )
                res = generate_results(
                    slug, items, initial_prompt_single_card, "azure", 200
                )
                final_results.append(res)
            if num_cards >= 2:
                initial_prompt_multiple_card += "Create {} clusters based on specific context from given titles, for EACH cluster create a JSON object".format(
                    str(num_cards)
                )
                titles, items = get_titles_and_items_by_category(
                    data, category=category
                )
                res = generate_results(
                    slug, items, initial_prompt_multiple_card, "azure", 200 * num_cards
                )
                final_results.append(res)
    if len(final_results) > 0:
        delete_all_history(slug)
    return final_results


def get_date_range(weeks_ago=0):
    today = datetime.today()
    start_date = (today - timedelta(days=today.weekday() + 7 * weeks_ago)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_date = (start_date + timedelta(days=6)).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )
    return start_date, end_date


def format_date_range(start_epoch, end_epoch):
    # Convert epoch to datetime objects
    start_date = datetime.fromtimestamp(start_epoch)
    end_date = datetime.fromtimestamp(end_epoch)

    # Format the dates
    start_date_str = start_date.strftime("%d %b")
    end_date_str = end_date.strftime("%d %b")

    # Return the formatted date range
    return f"{start_date_str} - {end_date_str}"


def calculate_deviation(last_week, last_to_last_week):
    deviation = {}
    for domain in last_week:
        last_week_count = last_week[domain]
        last_to_last_week_count = last_to_last_week.get(domain, 0)
        deviation[domain] = abs(last_week_count - last_to_last_week_count)
    return deviation


def create_visit_count_card(
    slug, domain, deviation, last_week_count, last_to_last_week_count, date_range
):
    description = f"{'increased' if last_week_count > last_to_last_week_count else 'decreased'} in visiting {domain}"
    activity_percentage = round(
        (deviation / (last_to_last_week_count if last_to_last_week_count else 1)) * 100,
        0,
    )
    activity = [
        "increased" if last_week_count > last_to_last_week_count else "decreased"
    ]
    if activity_percentage > 0:
        pendingCard = PendingCard(
            slug,
            "DomainVisitCard",
            description,
            [str(activity_percentage) + "%", activity, date_range],
            [{"title": "", "url": domain}],
            {"activity": [activity_percentage, activity], "description": domain},
            "Miscellaneous",
        )
        pendingCard.save()


def create_visit_chart_card(slug, domains_data, start_date, end_date):
    activity = [
        {"category": domain["_id"], "count": domain["count"]} for domain in domains_data
    ]
    pendingCard = PendingCard(
        slug,
        "VisitChartCard",
        "",
        [],
        [],
        {
            "activity": activity,
            "dateFrom": int(start_date.timestamp()),
            "dateTo": int(end_date.timestamp()),
        },
        "Miscellaneous",
    )
    pendingCard.save()
