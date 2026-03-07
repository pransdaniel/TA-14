import json
from dotenv import load_dotenv
import google.generativeai as genai
from django.conf import settings

api_key = getattr(settings, "GEMINI_API_KEY", None)

model = None
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite-preview",
        generation_config={
            "temperature": 0.3,
            "response_mime_type": "application/json",
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH",        "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",  "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT",         "threshold": "BLOCK_NONE"},
        ]
    )

# ─────────────────────────────────────────────────────────────
#  PROMPT TEMPLATES  (semua berbasis kode / snippet)
# ─────────────────────────────────────────────────────────────

# Default fallback: fill-in-the-blank pada potongan kode
DEFAULT_PROMPT = """
Kamu adalah pembuat soal pemrograman profesional.

ATURAN SOAL:
- Fokus pada PRAKTIK KODE, bukan teori.
- Setiap soal WAJIB menyertakan potongan kode (code snippet) yang relevan.
- Gunakan format markdown code block di dalam string JSON:
  "question": "Perhatikan kode berikut:\\n```python\\n<kode di sini>\\n```\\nIsilah bagian `___` agar output yang dihasilkan adalah `<output>`."
- Tipe soal: short_answer (isian singkat — isi bagian yang kosong / `___` pada kode).
- Jawaban harus berupa 1–2 baris kode atau ekspresi yang benar.

Contoh format JSON:
{"type": "short_answer",
 "question": "Perhatikan kode berikut:\\n```python\\nangka = [1, 2, 3, 4, 5]\\nhasil = ___\\nprint(hasil)  # Output: 15\\n```\\nIsilah `___` agar output-nya 15.",
 "answer": "sum(angka)"}
"""

# Multiple choice — opsi berisi potongan kode / ekspresi kode
MC_PROMPT = """
Kamu adalah pembuat soal pemrograman profesional.

ATURAN SOAL multiple_choice:
- Setiap soal WAJIB menyertakan potongan kode (code snippet) di bagian "question".
- Pertanyaan bisa berupa:
    a) "Apa output dari kode berikut?"
    b) "Manakah opsi yang melengkapi `___` dengan benar?"
    c) "Kode mana yang menghasilkan output `<output>`?"
- Opsi A–D boleh berisi potongan kode pendek atau ekspresi.
- JANGAN buat soal yang murni hafalan teori.

Format JSON:
{"type": "multiple_choice",
 "question": "Apa output dari kode berikut?\\n```python\\nx = [i**2 for i in range(4)]\\nprint(x)\\n```",
 "options": ["A. [0, 1, 4, 9]", "B. [1, 4, 9, 16]", "C. [0, 1, 2, 3]", "D. Error"],
 "answer": "A"}
"""

# True/False — pernyataan tentang perilaku kode
TF_PROMPT = """
Kamu adalah pembuat soal pemrograman profesional.

ATURAN SOAL true_false:
- Setiap soal WAJIB menyertakan potongan kode (code snippet).
- Pernyataan mengacu langsung pada kode: output, error, nilai variabel, dll.
- JANGAN buat pernyataan teori umum tanpa kode.

Format JSON:
{"type": "true_false",
 "question": "Perhatikan kode berikut:\\n```python\\ndef greet(name='World'):\\n    return f'Hello, {name}!'\\nprint(greet())\\n```\\nPernyataan: Output program di atas adalah `Hello, World!`.",
 "answer": "True"}
"""

# Essay — analisis / debug / jelaskan kode
ESSAY_PROMPT = """
Kamu adalah pembuat soal pemrograman profesional.

ATURAN SOAL essay:
- Setiap soal WAJIB menyertakan potongan kode (code snippet).
- Jenis pertanyaan:
    a) "Jelaskan apa yang dilakukan kode berikut baris per baris."
    b) "Temukan dan perbaiki bug pada kode berikut."
    c) "Modifikasi kode agar memenuhi syarat <syarat>."
- answer_key berisi poin-poin kunci yang diharapkan.

Format JSON:
{"type": "essay",
 "question": "Perhatikan kode berikut:\\n```python\\ndef factorial(n):\\n    if n == 0:\\n        return 1\\n    return n * factorial(n)\\n```\\nTemukan bug pada kode di atas dan tuliskan versi yang benar.",
 "answer_key": "Bug: rekursi tanpa pengurangan n. Perbaikan: ubah `factorial(n)` menjadi `factorial(n-1)`."}
"""

# Short answer — isian potongan kode
SHORT_ANSWER_PROMPT = """
Kamu adalah pembuat soal pemrograman profesional.

ATURAN SOAL short_answer:
- Setiap soal WAJIB menyertakan potongan kode dengan satu atau lebih bagian `___` yang harus diisi.
- Jawaban berupa ekspresi, keyword, nama fungsi, atau 1–2 baris kode.
- Hindari soal yang jawabannya hanya kata kunci teori.

Format JSON:
{"type": "short_answer",
 "question": "Lengkapi kode berikut agar list diurutkan secara menurun:\\n```python\\nangka = [3, 1, 4, 1, 5]\\nangka.___(reverse=True)\\nprint(angka)\\n```",
 "answer": "sort"}
"""

# Matching — SATU-SATUNYA tipe yang boleh teoritis
MATCHING_PROMPT = """
Kamu adalah pembuat soal pemrograman profesional.

ATURAN SOAL matching:
- Tipe ini BOLEH bersifat teoritis (konsep, istilah, definisi pemrograman).
- Setiap soal memiliki TEPAT 4 keyword dan 4 penjelasan.
- Keyword bisa berupa: nama fungsi bawaan, konsep OOP, tipe data, operator, dll.
- answer_key HARUS sesuai urutan dengan pairs.

Format JSON:
{"type": "matching",
 "question": "Pasangkan istilah berikut dengan penjelasannya:",
 "pairs": [
   {"keyword": "list", "explanation": "Struktur data urut yang dapat diubah (mutable)"},
   {"keyword": "tuple", "explanation": "Struktur data urut yang tidak dapat diubah (immutable)"},
   {"keyword": "dict", "explanation": "Struktur data pasangan key-value"},
   {"keyword": "set", "explanation": "Koleksi elemen unik tanpa urutan"}
 ],
 "answer_key": [
   "Struktur data urut yang dapat diubah (mutable)",
   "Struktur data urut yang tidak dapat diubah (immutable)",
   "Struktur data pasangan key-value",
   "Koleksi elemen unik tanpa urutan"
 ]}
"""

# Map tipe soal → prompt khusus
PROMPT_BY_TYPE = {
    "multiple_choice": MC_PROMPT,
    "true_false":      TF_PROMPT,
    "essay":           ESSAY_PROMPT,
    "short_answer":    SHORT_ANSWER_PROMPT,
    "matching":        MATCHING_PROMPT,
}


# ─────────────────────────────────────────────────────────────
#  CORE FUNCTIONS
# ─────────────────────────────────────────────────────────────

def generate_questions_gemini(text: str, prompt_instructions: str = "", num_questions: int = 5):
    """
    Generate soal pemrograman berbasis snippet kode.
    Jika prompt_instructions kosong, default ke soal isian singkat kode.
    HANYA generate tipe soal yang disebutkan di instruksi.
    """
    if model is None:
        return {"error": "GEMINI_API_KEY tidak ditemukan"}

    chosen_prompt = prompt_instructions if prompt_instructions.strip() else DEFAULT_PROMPT

    base_prompt = f"""
Kamu adalah pembuat soal pemrograman profesional yang mengikuti instruksi dengan SANGAT KETAT.

ATURAN UTAMA:
- Buat TEPAT {num_questions} soal berdasarkan teks materi di bawah.
- PRIORITASKAN soal berbasis KODE (snippet, isian kode, output kode).
- HANYA generate tipe soal yang EKSPLISIT disebutkan di instruksi user.
- JANGAN buat tipe soal lain yang tidak disebutkan.
- Output HARUS berupa JSON array yang valid, tanpa teks tambahan.

Instruksi & panduan format tipe soal (IKUTI DENGAN TEPAT):
{chosen_prompt}

PERINGATAN:
✗ JANGAN buat soal murni teori tanpa kode (kecuali tipe matching)
✗ JANGAN mix tipe jika instruksi hanya menyebutkan 1 tipe
✓ Setiap soal non-matching WAJIB ada code snippet

Materi:
"""

    try:
        prompt_with_text = base_prompt + "\n" + text.strip()
        response = model.generate_content(prompt_with_text)
        raw = response.text.strip()

        if raw.startswith("```json"):
            raw = raw[7:].strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()

        data = json.loads(raw)

        if isinstance(data, dict):
            data = [data]

        return data

    except json.JSONDecodeError as e:
        return {"error": "JSON parse error", "raw": raw, "detail": str(e)}
    except Exception as e:
        return {"error": "API error", "detail": str(e)}


def generate_by_type(text: str, question_type: str, num_questions: int = 5):
    """
    Shortcut: generate soal berdasarkan tipe tertentu menggunakan prompt yang sudah disiapkan.
    question_type: 'multiple_choice' | 'true_false' | 'essay' | 'short_answer' | 'matching'
    """
    prompt = PROMPT_BY_TYPE.get(question_type, DEFAULT_PROMPT)
    return generate_questions_gemini(text, prompt, num_questions)


def generate_matching_questions(text: str, num_questions: int = 5):
    """Shortcut khusus soal matching (teoritis diizinkan)."""
    return generate_by_type(text, "matching", num_questions)


def extract_question_types(instructions: str):
    """
    Extract tipe-tipe soal yang disebutkan di instruksi.
    Returns list of valid types.
    """
    found_types = []
    instructions_lower = instructions.lower()

    type_keywords = {
        'multiple_choice': ['multiple choice', 'pilihan ganda', 'pilihan berganda'],
        'true_false':      ['true/false', 'true false', 'benar salah', 'tf'],
        'essay':           ['essay', 'uraian'],
        'short_answer':    ['isian', 'isian singkat', 'short answer', 'jawaban singkat'],
        'matching':        ['matching', 'pencocokan', 'pasangkan', 'kesesuaian'],
    }

    for qtype, keywords in type_keywords.items():
        for keyword in keywords:
            if keyword in instructions_lower:
                if qtype not in found_types:
                    found_types.append(qtype)
                break

    return found_types if found_types else ['short_answer']  # default ke isian kode


def validate_question_types(questions_data: list, allowed_types: list):
    """
    Filter soal yang tipe-nya tidak ada di allowed_types.
    Returns filtered list of questions.
    """
    if not isinstance(questions_data, list):
        return []
    return [q for q in questions_data if q.get('type', 'short_answer') in allowed_types]


# ─────────────────────────────────────────────────────────────
#  QUICK TEST
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    teks = """
    Python mendukung list comprehension untuk membuat list secara ringkas.
    Contoh: [x**2 for x in range(5)] menghasilkan [0, 1, 4, 9, 16].
    Fungsi built-in seperti sum(), len(), max(), min() sering digunakan bersama list.
    Dictionary dibuat dengan {key: value} dan diakses dengan dict[key].
    """

    print("=== SHORT ANSWER (default / isian kode) ===")
    hasil = generate_by_type(teks, "short_answer", 3)
    print(json.dumps(hasil, indent=2, ensure_ascii=False))

    print("\n=== MATCHING (teoritis) ===")
    hasil = generate_matching_questions(teks, 2)
    print(json.dumps(hasil, indent=2, ensure_ascii=False))