# question_gen.py (Versi Fix 100% Work Desember 2025)

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
dotenv_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path)

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
    Generate soal sesuai instruksi user, bisa pilihan ganda, essay, isian, matching, dll.
    HANYA generate tipe soal yang disebutkan di instruksi - tidak boleh ada tipe lain!
    """
    if model is None:
        return {"error": "GEMINI_API_KEY tidak ditemukan"}

    # Prompt dasar yang sangat ketat tentang tipe soal
    base_prompt = f"""
Kamu adalah pembuat soal ujian profesional yang mengikuti instruksi dengan SANGAT KETAT.

ATURAN UTAMA:
- Buat TEPAT {num_questions} soal berdasarkan teks materi di bawah.
- HANYA generate tipe soal yang EKSPLISIT disebutkan di instruksi user.
- JANGAN buat tipe soal lain yang tidak disebutkan.
- WAJIB mengikuti instruksi dengan sempurna.
- Output HARUS berupa JSON array yang valid, tanpa teks tambahan.

Instruksi dari user (IKUTI DENGAN TEPAT - HANYA TIPE SOAL INI):
{prompt_instructions if prompt_instructions else "Buat soal multiple choice dengan 4 opsi (A,B,C,D), 1 jawaban benar."}

FORMAT JSON berdasarkan tipe soal:
- multiple_choice: 
  {{"type": "multiple_choice", "question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "answer": "C"}}
- essay:
  {{"type": "essay", "question": "...", "answer_key": "Jawaban ideal / poin-poin yang diharapkan..."}}
- isian (singkat):
  {{"type": "isian", "question": "...", "answer": "jawaban singkat yang benar"}}
- matching (HARUS 4 keyword dengan 4 explanation):
  {{"type": "matching", "question": "Pasangkan istilah berikut dengan penjelasannya:", "pairs": [{{"keyword": "keyword1", "explanation": "penjelasan1"}}, {{"keyword": "keyword2", "explanation": "penjelasan2"}}, {{"keyword": "keyword3", "explanation": "penjelasan3"}}, {{"keyword": "keyword4", "explanation": "penjelasan4"}}], "answer_key": ["penjelasan1", "penjelasan2", "penjelasan3", "penjelasan4"]}}

PERINGATAN PENTING:
✗ JANGAN buat soal tipe lain selain yang disebutkan di instruksi
✗ JANGAN mix tipe jika instruksi hanya menyebutkan 1 tipe
✓ HANYA buat tipe yang JELAS disebutkan di instruksi user

Jangan tambahkan penjelasan atau teks apa pun di luar JSON!

Materi:
"""

    try:
        # Attach the actual material text so the model generates questions
        # based on the provided `text` (was missing previously).
        prompt_with_text = base_prompt + "\n" + text.strip()
        response = model.generate_content(prompt_with_text)
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

def generate_matching_questions(text: str, num_questions: int = 5):
    """
    Generate soal matching dengan 4 keyword dan 4 explanation.
    Shortcut untuk memudahkan generate soal matching.
    """
    matching_prompt = f"""
Kamu adalah pembuat soal ujian tipe MATCHING yang profesional.

Tugasmu:
- Buat **{num_questions} soal matching** dari teks materi di bawah
- SETIAP SOAL harus memiliki TEPAT 4 keyword dan 4 penjelasan yang akan dicocokkan

Format JSON yang WAJIB:
[
  {{
    "type": "matching",
    "question": "Pasangkan istilah di bawah dengan penjelasannya:",
    "pairs": [
      {{"keyword": "istilah 1", "explanation": "penjelasan untuk istilah 1"}},
      {{"keyword": "istilah 2", "explanation": "penjelasan untuk istilah 2"}},
      {{"keyword": "istilah 3", "explanation": "penjelasan untuk istilah 3"}},
      {{"keyword": "istilah 4", "explanation": "penjelasan untuk istilah 4"}}
    ],
    "answer_key": ["penjelasan untuk istilah 1", "penjelasan untuk istilah 2", "penjelasan untuk istilah 3", "penjelasan untuk istilah 4"]
  }},
  ... (repeat untuk soal berikutnya)
]

PENTING:
- answer_key HARUS sesuai urutan dengan pairs
- HARUS 4 keyword dan 4 explanation per soal
- Jangan tambahkan teks di luar JSON
"""
    
    return generate_questions_gemini(text, matching_prompt, num_questions)

def extract_question_types(instructions: str):
    """
    Extract tipe-tipe soal yang disebutkan di instruksi.
    Returns list of valid types: ['multiple_choice', 'essay', 'isian', 'matching']
    """
    valid_types = ['multiple_choice', 'essay', 'isian', 'matching']
    found_types = []
    
    instructions_lower = instructions.lower()
    
    # Mapping instruksi ke tipe soal
    type_keywords = {
        'multiple_choice': ['multiple choice', 'pilihan ganda', 'pilihan berganda'],
        'essay': ['essay', 'uraian'],
        'isian': ['isian', 'isian singkat', 'short answer', 'jawaban singkat'],
        'matching': ['matching', 'pencocokan', 'pasangkan', 'kesesuaian']
    }
    
    for qtype, keywords in type_keywords.items():
        for keyword in keywords:
            if keyword in instructions_lower:
                if qtype not in found_types:
                    found_types.append(qtype)
                break
    
    return found_types if found_types else ['multiple_choice']

def validate_question_types(questions_data: list, allowed_types: list):
    """
    Validate bahwa semua soal hanya menggunakan tipe yang diizinkan.
    Filter out soal yang tipe-nya tidak di-allow.
    Returns filtered list of questions.
    """
    if not isinstance(questions_data, list):
        return []
    
    valid_questions = []
    for q in questions_data:
        q_type = q.get('type', 'multiple_choice')
        if q_type in allowed_types:
            valid_questions.append(q)
    
    return valid_questions

# Test langsung
if __name__ == "__main__":
    teks = "Python adalah bahasa pemrograman yang diciptakan oleh Guido van Rossum pada tahun 1991."
    hasil = generate_questions_gemini(teks)
    print(json.dumps(hasil, indent=2, ensure_ascii=False))