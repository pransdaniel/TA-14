# question_gen.py (Versi Fix 100% Work Desember 2025)

import os
import json
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Prepare model only if API key present; otherwise model stays None and
# generate_questions_gemini will return an error dict when called.
model = None
if api_key:
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

def generate_questions_gemini(text: str, prompt_instructions: str = "", num_questions: int = 5):
    """
    Generate soal sesuai instruksi user, bisa pilihan ganda, essay, isian, dll.
    """
    if model is None:
        return {"error": "GEMINI_API_KEY tidak ditemukan"}

    # Prompt dasar yang sangat fleksibel
    base_prompt = f"""
Kamu adalah pembuat soal ujian profesional yang mengikuti instruksi dengan sangat ketat.

Tugasmu:
- Buat **{num_questions} soal** berdasarkan teks materi di bawah.
- Ikuti **SELAIN** instruksi yang diberikan user dengan tepat.
- Output **HARUS** berupa JSON array yang valid, tanpa teks tambahan di luar JSON.

Instruksi khusus dari user (WAJIB DIKIKUTI):
{prompt_instructions if prompt_instructions else "Buat soal pilihan ganda dengan 4 opsi (A,B,C,D), 1 jawaban benar."}

Format JSON yang diharapkan (sesuaikan dengan instruksi user):
- Jika pilihan ganda: 
  {{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "answer": "C"}}
- Jika essay:
  {{"question": "...", "answer_key": "Jawaban ideal / poin-poin yang diharapkan..."}}
- Jika isian singkat:
  {{"question": "...", "answer": "jawaban singkat yang benar"}}
- Bisa juga tambahkan "rubrik" atau "poin" jika diminta

Jangan tambahkan penjelasan di luar JSON!

Materi:
"""

    try:
        response = model.generate_content(base_prompt)
        raw = response.text.strip()

        # Pembersihan output yang umum di 2025
        if raw.startswith("```json"):
            raw = raw[7:].strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()

        data = json.loads(raw)

        # Normalisasi: pastikan selalu list
        if isinstance(data, dict):
            data = [data]

        return data

    except json.JSONDecodeError as e:
        return {
            "error": "JSON parse error",
            "raw": raw,
            "detail": str(e)
        }
    except Exception as e:
        return {"error": "API error", "detail": str(e)}

# Test langsung
if __name__ == "__main__":
    teks = "Python adalah bahasa pemrograman yang diciptakan oleh Guido van Rossum pada tahun 1991."
    hasil = generate_questions_gemini(teks)
    print(json.dumps(hasil, indent=2, ensure_ascii=False))