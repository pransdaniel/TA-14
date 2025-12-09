# question_gen.py (Versi Fix 100% Work Desember 2025)

import os
import json
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY tidak ditemukan!")

genai.configure(api_key=api_key)

# GUNAKAN MODEL INI! (paling stabil + kuota besar)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite-preview-09-2025",  # atau "gemini-1.5-flash-001"
    generation_config={
        "temperature": 0.3,
        "response_mime_type": "application/json",  # ini SUPPORT di model ini
    },
    # Tambahkan ini biar tidak kena blokir safety
    safety_settings=[
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE"
        },
    ]
)

def generate_questions_gemini(text: str):
    prompt = f"""
    Buat 5 soal pilihan ganda dari teks berikut. 
    Setiap soal harus punya 4 opsi (A, B, C, D) dan satu jawaban benar.

    Kembalikan dalam format JSON array of objects seperti ini:
    [
      {{
        "question": "Pertanyaan di sini?",
        "options": ["A. Pilihan 1", "B. Pilihan 2", "C. Pilihan 3", "D. Pilihan 4"],
        "answer": "B"
      }}
    ]

    Teks materi:
    {text}
    """

    try:
        response = model.generate_content(prompt)
        raw_json = response.text.strip()
        
        # Kadang ada markdown ```json ... ``` → bersihkan dulu
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:]
        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]
            
        data = json.loads(raw_json)
        return data

    except json.JSONDecodeError as e:
        return {"error": "JSON parse gagal", "raw": response.text, "details": str(e)}
    except Exception as e:
        return {"error": "API Error", "details": str(e)}

# Test langsung
if __name__ == "__main__":
    teks = "Python adalah bahasa pemrograman yang diciptakan oleh Guido van Rossum pada tahun 1991."
    hasil = generate_questions_gemini(teks)
    print(json.dumps(hasil, indent=2, ensure_ascii=False))