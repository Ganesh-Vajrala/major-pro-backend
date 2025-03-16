from transformers import pipeline
import google.generativeai as genai
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyCMD7OGeJv64eYwRNiqREAF3UxT5woS3jI"
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_summary(product_description, reviews):

    text = f'Product Description: {product_description}\n\nCustomer Reviews: {" ".join(reviews[:10])}'
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(f"Summarize this product information and tell use ful to buy or not in para format in 30 words without any heading:\n{text}")
    summary_text = response.text
    return summary_text



