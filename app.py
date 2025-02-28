from flask import Flask, jsonify, request
from utils.fetch_reviews import fetch_reviews
from flask_cors import CORS
from utils.summerization import generate_summary

app = Flask(__name__)
CORS(app)

@app.route("/analyze", methods=["GET", "POST"])
def index():
    data = request.json
    platform = data.get("platform")
    link = data.get("link")
    model_choice = data.get("model")
    print(platform,link,model_choice)

    reviews,plain_comments,product_details = fetch_reviews(platform, link, model_choice) 
    product_description = product_details.get("product_title", "No description available.")

    product_summary = generate_summary(product_description, plain_comments)

    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for review in reviews:
        sentiment = review.get("sentiment")
        if sentiment:
            sentiment_counts[sentiment] += 1

    reviews.sort(key=lambda x: x.get("confidence") or -1, reverse=True)
    top_positive = [r for r in reviews if r.get("sentiment") == "Positive"][:5]
    top_negative = [r for r in reviews if r.get("sentiment") == "Negative"][:5]
    top_neutral = [r for r in reviews if r.get("sentiment") == "Neutral"][:5]

    return jsonify({
        "model_used":model_choice,
        "product_details": product_details,
        "reviews": reviews,
        "plain_comments": plain_comments,
        "product_summary":product_summary
    })

if __name__ == "__main__":
    app.run(debug=True)
