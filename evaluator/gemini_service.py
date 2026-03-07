import google.generativeai as genai
from django.conf import settings
import json
import re
from google.generativeai.types import generation_types


def gemini_score(reference, essay):
    """
    Score essay using Gemini API with fallback to second API key, then to None if both fail.
    """
    api_keys = [settings.GEMINI_API_KEY_2, settings.GEMINI_API_KEY]
    
    for api_key in api_keys:
        if not api_key:
            continue
            
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")
            
            prompt = f"""
            Anda adalah dosen yang menilai jawaban mahasiswa.

            Referensi:
            {reference}

            Jawaban mahasiswa:
            {essay}

            Berikan nilai 0-100 dalam format JSON:
            {{
                "score": number
            }}
            """

            response = model.generate_content(prompt)
            text = response.text

            json_text = re.search(r'\{.*\}', text, re.DOTALL).group()
            result = json.loads(json_text)

            return result["score"] / 100
            
        except Exception as e:
            # Check if it's a rate limit or quota exceeded error
            if "quota" in str(e).lower() or "limit" in str(e).lower() or "resource" in str(e).lower():
                continue  # Try next API key
            else:
                # For other errors, re-raise
                raise e
    
    # If both API keys failed due to limits, return None
    return None
