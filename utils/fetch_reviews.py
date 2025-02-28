import requests
from config import API_KEYS
from utils.sentiment_analysis import analyze_sentiment
import re

def extract_asin(link):
    match = re.search(r"/dp/([A-Z0-9]{10})|/gp/product/([A-Z0-9]{10})|/product/([A-Z0-9]{10})", link)
    return match.group(1) or match.group(2) or match.group(3) if match else None

def fetch_product_details(platform,link):
    asin = extract_asin(link)
    url = f"https://real-time-amazon-data.p.rapidapi.com/product-details?asin={asin}&country=IN"
    headers = {
        'x-rapidapi-key': API_KEYS["amazon"],
        'x-rapidapi-host': "real-time-amazon-data.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)
    return response.json().get("data", {}) if response.status_code == 200 else {}


def fetch_reviews(platform, link, model_choice, max_pages=5):
   
    all_reviews = []
    plain_comments = []

    if platform == "amazon":

        asin = extract_asin(link)
        if not asin:
            print("Invalid Amazon URL. ASIN not found.")
            return []
        product_details = fetch_product_details(platform, link)
        product_description = product_details.get("product_title", "")

        for page in range(1, max_pages + 1):
            url = f"https://real-time-amazon-data.p.rapidapi.com/product-reviews?asin={asin}&country=IN&page={page}"
            headers = {
                'x-rapidapi-key': API_KEYS["amazon"],
                'x-rapidapi-host': "real-time-amazon-data.p.rapidapi.com"
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                reviews = response.json().get("data", {}).get("reviews", [])
                if not reviews:
                    break
                
                for review in reviews:
                    review_comment = review.get("review_comment", "")
                    plain_comments.append(review_comment)

                    try:
                        sentiment, confidence = analyze_sentiment(product_description, review_comment, model_choice)
                        review["sentiment"] = sentiment
                        review["confidence"] = confidence
                    except Exception as e:
                        review["review_comment"]=""
                        review["sentiment"] = None  # Assign None if no comment
                        review["confidence"] = None
                        print(f"Error processing Amazon review: {e}")
                
                all_reviews.extend(reviews)
            else:
                print(f"Error fetching page {page}: {response.status_code}")
                break
        return all_reviews,plain_comments,product_details # Stop fetching if an error occurs
    
    elif platform == "instagram":
        post_id = link.split("/")[-1]  # Extract post ID from URL
        pagination_token = None

        for page in range(1, max_pages + 1):
            url = "https://instagram-scraper-api2.p.rapidapi.com/v1/comments"
            headers = {
                'x-rapidapi-key': API_KEYS["instagram"],
                'x-rapidapi-host': "instagram-scraper-api2.p.rapidapi.com"
            }
            params = {"code_or_id_or_url": post_id}
            if pagination_token:
                params["pagination_token"] = pagination_token  # Fetch next page

            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                comments = data.get("data", {}).get("items", [])
                if not comments:
                    break  # Stop if no more comments found

                

                # Add sentiment analysis and confidence score
                for comment in comments:
                    try:
                        sentiment, confidence = analyze_sentiment(comment.get("text", ""), model_choice)
                        comment["sentiment"] = sentiment
                        comment["confidence"] = confidence
                    except Exception as e:
                        review["sentiment"] = None  # Assign None if no comment
                        review["confidence"] = None
                        comment["text"]="  "
                        print(f"Error processing Instagram comment: {e}")
                 
                all_reviews.extend(comments)
                new_pagination_token = data.get("pagination_token")
                # print(new_pagination_token)
                if new_pagination_token:
                    pagination_token = new_pagination_token
                else:
                    break
            else:
                print(f"Error fetching Instagram comments, page {page}: {response.status_code}")
                break  # Stop fetching if an error occurs  
    return all_reviews, plain_comments  # Return collected reviews/comments with sentiment analysis
