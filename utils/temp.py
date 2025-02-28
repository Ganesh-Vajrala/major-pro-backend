import os
import re
import joblib
import pandas as pd
from sklearn.svm import SVC
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import nltk
from nltk.corpus import stopwords

# Ensure necessary NLTK data is downloaded
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Load Dataset (Download from https://jmcauley.ucsd.edu/data/amazon/index_2014.html)
DATASET_PATH = 'reviews.csv'  # Ensure this file is in the same directory
if not os.path.exists(DATASET_PATH):
    raise FileNotFoundError("Dataset 'reviews.csv' not found. Please download and place it in the script directory.")

data = pd.read_csv(DATASET_PATH, nrows=100000)  # Adjust size as needed

# Data Preprocessing
def clean_text(text):
    text = text.lower()  # Lowercase
    text = re.sub(r'[^a-z\s]', '', text)  # Remove non-alphabetic characters
    text = ' '.join(word for word in text.split() if word not in stop_words)  # Remove stopwords
    return text

data['cleaned_text'] = data['reviewText'].astype(str).apply(clean_text)

data = data[data['overall'] != 3]  # Remove neutral reviews
data['label'] = data['overall'].apply(lambda x: 1 if x > 3 else 0)  # 1: Positive, 0: Negative

# Feature Extraction
vectorizer = HashingVectorizer(n_features=10000)
X = vectorizer.transform(data['cleaned_text'])
y = data['label']

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Model
svm_model = SVC(kernel='linear', probability=True)
svm_model.fit(X_train, y_train)

# Evaluate Model
y_pred = svm_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy * 100:.2f}%")

# Save Model and Vectorizer
os.makedirs('models', exist_ok=True)
joblib.dump(vectorizer, 'models/hashing_vectorizer.pkl')
joblib.dump(svm_model, 'models/svm_model.pkl')
print("Model and vectorizer saved in 'models' directory.")