import google.generativeai as genai
import os

# 1. Setup your API Key directly or load from environment
# Replace 'YOUR_ACTUAL_API_KEY' with your real key if not using env vars
os.environ["GOOGLE_API_KEY"] = "AIzaSyAVnCobTJcu_KNVI-L6rwgRXrhCXPGotmg"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("--- AVAILABLE MODELS ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
except Exception as e:
    print(f"Error: {e}")