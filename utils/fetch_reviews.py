import requests
from config import API_KEYS
import json
import subprocess
from utils.sentiment_analysis import analyze_sentiment
from apify_client import ApifyClient
import re

def extract_asin(link):
    match = re.search(r"/dp/([A-Z0-9]{10})|/gp/product/([A-Z0-9]{10})|/product/([A-Z0-9]{10})", link)
    return match.group(1) or match.group(2) or match.group(3) if match else None

def extract_pid(link):
    match = re.search(r'pid=([A-Z0-9]+)', link)
    pid = match.group(1)
    return pid if match else None

def fetch_product_details(platform,link):
    if platform == "amazon":
        asin = extract_asin(link)
        url = f"https://real-time-amazon-data.p.rapidapi.com/product-details?asin={asin}&country=IN"
        headers = {
            'x-rapidapi-key': API_KEYS["amazon"],
            'x-rapidapi-host': "real-time-amazon-data.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers)
        return response.json().get("data", {}) if response.status_code == 200 else {}
    if platform == "flipkart":
        pid = extract_pid(link)
        url = "https://flipkart-apis.p.rapidapi.com/backend/rapidapi/product-details"

        querystring = {"pid":pid}

        headers = {
            "x-rapidapi-key": API_KEYS["flipkart"],
            "x-rapidapi-host": "flipkart-apis.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        return response.json().get("data", {}) if response.status_code == 200 else {}



def fetch_reviews(platform, link, model_choice, max_pages=5):
   
    all_reviews = []
    plain_comments = []

    if platform == "amazon":

        asin = extract_asin(link)
        print(asin)
        if not asin:
            print("Invalid Amazon URL. ASIN not found.")
            return []
        product_details = fetch_product_details(platform, link)
        product_description = product_details.get("product_title", "")

        for page in range(1, max_pages + 1):
            url = "https://api.scrapingdog.com/amazon/reviews"
            params = {
                'api_key': API_KEYS["amazon_review"],
                "asin":asin,
                "domain":"in",
                "page": str(page),
            }

            response = requests.get(url, params=params)
            if response.status_code == 200:
                reviews = response.json().get("customer_reviews", [])
                if not reviews:
                    break
                
                for review in reviews:
                    review_comment = review.get("review", "")
                    plain_comments.append(review_comment)

                    try:
                        sentiment, confidence = analyze_sentiment(product_description, review_comment, model_choice)
                        review["sentiment"] = sentiment
                        review["confidence"] = confidence
                    except Exception as e:
                        review["review"]=""
                        review["sentiment"] = None  # Assign None if no comment
                        review["confidence"] = None
                        print(f"Error processing Amazon review: {e}")
                
                all_reviews.extend(reviews)
            else:
                print(f"Error fetching page {page}: {response.status_code}")
                break
        return all_reviews,plain_comments,product_details # Stop fetching if an error occurs
    
    elif platform == "instagram":
        postid = re.search(r"instagram\.com/p/([^/?]+)", link)
        if postid:
            postid = postid.group(1)
            print("post ID:", postid)
        else:
            return
        client = ApifyClient("<Your API KEY>")

        run_input = {
            "directUrls": [link],
            "resultsType": "posts",
            "resultsLimit": 10,
            "searchType": "hashtag",
            "searchLimit": 1,
            "addParentData": False,
        }
        post_details = []
        run = client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            post_details.append(item)
        post_description = post_details[0].get("alt")
        run_input = {
            "directUrls": [link],
            "resultsType": "comments",
            "resultsLimit": 50,
            "searchType": "hashtag",
            "searchLimit": 1,
            "addParentData": False,
        }
        run = client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)
        for review in client.dataset(run["defaultDatasetId"]).iterate_items():
            post_comment = review.get("text")
            plain_comments.append(post_comment)
            try:
                sentiment, confidence = analyze_sentiment(post_description, post_comment, model_choice)
                review["sentiment"] = sentiment
                review["confidence"] = confidence
            except Exception as e:
                review["review"]=""
                review["sentiment"] = None
                review["confidence"] = None
                print(f"Error processing Amazon review: {e}")
    
            all_reviews.append(review)
        return all_reviews,plain_comments,post_details
          
    elif platform == "flipkart":
        pid = extract_pid(link)
        print(pid)
        if not pid:
            print("Invalid Flipkart URL. PID not found.")
            return []
        product_details = fetch_product_details(platform, link)
        print(product_details)
        product_description = product_details["page_content"].get("title", "")
        apiUrl = "http://127.0.0.1:5001/v1.0/reviews"
        for page in range(1, max_pages +1):
            params = {
                "page":page,
                "url":link
            }
            response = requests.get(apiUrl,params=params)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                if data != []:
                    reviews = data[1:]
                    for review in reviews:
                        review_comment = review.get("review_content","")
                        plain_comments.append(review_comment)
                        try:
                            sentiment, confidence = analyze_sentiment(product_description, review_comment, model_choice)
                            review["sentiment"] = sentiment
                            review["confidence"] = confidence
                        except Exception as e:
                            review["review"]=""
                            review["sentiment"] = None  # Assign None if no comment
                            review["confidence"] = None
                            print(f"Error processing Amazon review: {e}")
                
                    all_reviews.extend(reviews)
            else:         
                print(f"Error fetching page {page}: {response.status_code}")
                break
        print("all reviews plain_reviews: ---->",plain_comments,"product_title ---->", product_description)
        return all_reviews,plain_comments,product_details
    return all_reviews, plain_comments


