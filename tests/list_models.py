#!/usr/bin/env python3
"""List available Gemini models"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure API
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

print("Available Gemini Models:")
print("=" * 60)
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        print()
