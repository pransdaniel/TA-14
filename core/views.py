import os
import tempfile
import pdfplumber
import pytesseract
import json
from pdf2image import convert_from_path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Question, Source
from .serializers import QuestionSerializer
# Pastikan nama import sesuai dengan file utils Anda
from .utils.question_gen import generate_questions_gemini 

# ... (fungsi extract_text_from_pdf dan upload_pdf biarkan saja seperti semula) ...
def extract_text_from_pdf(path):
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        print("PDFPlumber failed:", e)
    if not text.strip():
        pages = convert_from_path(path)
        for p in pages:
            text += pytesseract.image_to_string(p) + "\n"
    return text


@api_view(['POST'])
def upload_pdf(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "File PDF tidak ditemukan"}, status=status.HTTP_400_BAD_REQUEST)

        source = Source.objects.create(filename=file.name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            for chunk in file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name

        text = extract_text_from_pdf(temp_path)
        os.remove(temp_path)

        return Response({
            "source_id": source.id,
            "preview": text[:100000] 
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- BAGIAN YANG DIPERBAIKI ----

@api_view(['POST'])
def generate_questions(request):
    # 1. Ambil data dari request
    source_id = request.data.get("source_id")
    text = request.data.get("text") # Pastikan key yang dikirim dari frontend adalah 'text'

    # 2. Validasi input
    if not text:
        return Response({"error": "Field 'text' diperlukan"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 3. Panggil Gemini
        # Result sudah berupa List/Dict Python, JANGAN di-json.loads lagi
        data = generate_questions_gemini(text)
        
        # Cek jika util mengembalikan error
        if isinstance(data, dict) and "error" in data:
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        inserted_count = 0
        
        # 4. Looping data untuk disimpan ke DB
        for q in data:
            # Handling opsi jawaban: Gemini mengembalikan list ["A...", "B..."]
            # Kita perlu memecahnya ke kolom option_a, option_b, dst.
            options = q.get("options", [])
            
            # Ambil opsi dengan aman (antisipasi jika opsi kurang dari 4)
            opt_a = options[0] if len(options) > 0 else ""
            opt_b = options[1] if len(options) > 1 else ""
            opt_c = options[2] if len(options) > 2 else ""
            opt_d = options[3] if len(options) > 3 else ""

            Question.objects.create(
                source_id=source_id,
                topic=q.get("topic", "General"), # Default topic jika kosong
                question=q.get("question", ""),
                
                # Mapping options
                option_a=opt_a,
                option_b=opt_b,
                option_c=opt_c,
                option_d=opt_d,
                
                # Mapping kunci jawaban (sesuaikan key dari output Gemini)
                correct_answer=q.get("answer", "A"), 
                
                # Mapping difficulty
                difficulty=q.get("difficulty_level", 0.5)
            )
            inserted_count += 1
            
        return Response({
            "message": "Sukses generate soal",
            "inserted": inserted_count,
            "data": data  # Kirim balik data agar bisa dilihat di frontend/postman
        })

    except Exception as e:
        # Debugging: print error ke console server
        print(f"Error Generate: {e}")
        return Response(
            {"error": str(e), "hint": "Cek format JSON output Gemini atau struktur model DB"}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def get_questions(request):
    questions = Question.objects.all()
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)