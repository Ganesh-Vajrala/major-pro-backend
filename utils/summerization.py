from transformers import pipeline
import google.generativeai as genai
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyB8VlGzvaPXRhA5Ctbr9Fbn9Nt-UnxgaPE"
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_summary(product_description, reviews):

    text = f'Product Description: {product_description}\n\nCustomer Reviews: {" ".join(reviews[:10])}'
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(f"Summarize this product information in 30 words and tell use ful to buy or not:\n{text}")
    summary_text = response.text
    return summary_text



