import joblib
import re
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.linear_model import LinearRegression
from transformers import pipeline
from sklearn.feature_extraction.text import HashingVectorizer

# Load pre-trained models and vectorizers
vectorizer = joblib.load("models/hashing_vectorizer.pkl")
svm_model = joblib.load("models/svm_model.pkl")

# Initialize VADER analyzer
analyzer = SentimentIntensityAnalyzer()

# Load BERT sentiment analysis pipeline
bert_sentiment = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# Clean text function
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text

# Analyze sentiment based on the selected model
def analyze_sentiment(product_description, review_comment, model_choice):
    # Combine product description and review comment for analysis
    combined_text = f"{product_description} {review_comment}"
    cleaned_text = clean_text(combined_text)

    if model_choice == "VADER":
        # VADER sentiment analysis
        print("im here , vader is called ! " )
        vs = analyzer.polarity_scores(review_comment)
        sentiment = "Positive" if vs["compound"] >= 0.05 else "Negative" if vs["compound"] <= -0.05 else "Neutral"
        confidence = abs(vs["compound"]) * 100
        return sentiment, confidence

    elif model_choice == "SVM":
        # SVM sentiment analysis
        X = vectorizer.transform([cleaned_text])
        pred = svm_model.predict(X)[0]
        confidence = np.max(svm_model.decision_function(X)) * 100  # Confidence score
        return "Positive" if pred == 1 else "Negative", confidence

    elif model_choice == "BERT":
        # BERT sentiment analysis
        result = bert_sentiment(cleaned_text, truncation=True)[0]   
        label = result['label']  # e.g., "5 stars"
        confidence = result['score'] * 100
        
        # Map star ratings to expected sentiment categories
        if label in ["4 stars", "5 stars"]:
            sentiment = "Positive"
        elif label in ["1 star", "2 stars"]:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
        return sentiment, confidence

    elif model_choice == "Linear Regression":
        # Linear Regression sentiment analysis (using VADER compound scores as features)
        vs = analyzer.polarity_scores(review_comment)
        compound_score = vs["compound"]
        X = np.array([[compound_score]])  # Feature matrix
        lr_model = LinearRegression()
        
        # Dummy training data (replace with actual data if available)
        X_train = np.array([[-0.8], [-0.5], [0.0], [0.5], [0.8]])
        y_train = np.array([0, 0, 1, 1, 1])  # 0: Negative, 1: Positive
        
        lr_model.fit(X_train, y_train)
        pred = lr_model.predict(X)[0]
        sentiment = "Positive" if pred >= 0.5 else "Negative"
        confidence = abs(pred - 0.5) * 100  # Confidence score
        return sentiment, confidence

    else:
        raise ValueError("Invalid model choice. Choose from 'VADER', 'SVM', 'BERT', or 'LinearRegression'.")
    return sentiment, confidence
