import google.generativeai as genai
from django.conf import settings
import json
import re

genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")


def gemini_score(reference, essay):

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
