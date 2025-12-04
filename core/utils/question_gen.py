import os
import json
import google.generativeai as genai

# Pastikan nama environment variable disesuaikan (misal: GEMINI_API_KEY atau GOOGLE_API_KEY)
api_key = os.getenv("GEMINI_API_KEY") 
if not api_key:
    raise ValueError("GEMINI_API_KEY tidak ditemukan! Pastikan sudah diset di environment.")

# 1. Konfigurasi API
genai.configure(api_key=api_key)

# 2. Inisialisasi Model dengan JSON Mode
# 'response_mime_type' memaksa model hanya mengeluarkan JSON raw, 
# jadi kita tidak perlu regex/cleaning manual lagi.
generation_config = {
    "temperature": 0.2,
    "response_mime_type": "application/json" 
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-lite", 
    generation_config=generation_config
)

def generate_questions_gemini(text):
    prompt = f"""
    Buat 5 soal pilihan ganda dari teks berikut.
    
    Format JSON yang diinginkan:
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

    try:
        # 3. Generate Content
        response = model.generate_content(prompt)
        
        # Karena sudah pakai JSON mode, response.text pasti JSON valid
        raw = response.text 
        
        # Langsung parse ke dictionary
        data = json.loads(raw)
        return data

    except json.JSONDecodeError as e:
        # Fallback jika model entah kenapa gagal format (sangat jarang di Gemini 1.5)
        return {"error": "Gagal parsing JSON", "details": str(e), "raw": response.text}
    except Exception as e:
        return {"error": "Terjadi kesalahan API", "details": str(e)}

# --- Contoh Penggunaan ---
if __name__ == "__main__":
    teks_materi = """
    Fotosintesis adalah proses yang digunakan oleh tumbuhan, alga, dan bakteri tertentu 
    untuk mengubah energi cahaya menjadi energi kimia. Energi kimia ini disimpan dalam 
    ikatan gula karbohidrat. Fotosintesis terjadi di kloroplas, menggunakan klorofil.
    """
    
    result = generate_questions_gemini(teks_materi)
    
    # Print hasil (pretty print)
    print(json.dumps(result, indent=2))