import os
import json
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY tidak ditemukan! Pastikan sudah diset di environment.")

client = OpenAI(api_key=api_key)

def generate_questions_openai(text):
    prompt = f"""
    Buat 5 soal pilihan ganda dari teks berikut.
    Jawaban HARUS dalam format JSON murni tanpa ```json atau tanda backtick.

    Format:
    [
      {{
        "question": "...",
        "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "answer": "A"
      }}
    ]

    Teks:
    {text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()

    # 🧹 Bersihkan blok markdown (```json ... ```)
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json", "", 1).strip()
        raw = raw.strip("`").strip()

    try:
        data = json.loads(raw)
        return data
    except json.JSONDecodeError:
        return {"error": "Expecting value: line 1 column 1 (char 0)", "raw": raw}