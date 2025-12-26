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
    source_id = request.data.get("source_id")
    text = request.data.get("text")
    instructions = request.data.get("instructions", "")   # <-- ini yang paling penting
    jumlah_soal = request.data.get("jumlah_soal", 5)

    if not text:
        return Response({"error": "Field 'text' wajib"}, status=400)

    if not instructions.strip():
        instructions = "Buat 5 soal pilihan ganda dengan 4 opsi (A,B,C,D), satu jawaban benar."

    try:
        questions_data = generate_questions_gemini(
            text=text,
            prompt_instructions=instructions,
            num_questions=int(jumlah_soal)
        )

        if isinstance(questions_data, dict) and "error" in questions_data:
            return Response(questions_data, status=500)

        inserted_count = 0
        for q in questions_data:
            # Kita simpan secara fleksibel, tergantung jenis soal
            question_obj = Question.objects.create(
                source_id=source_id,
                question=q.get("question", "").strip(),
                # Untuk pilihan ganda
                option_a=q.get("options", [""]*4)[0] if "options" in q else "",
                option_b=q.get("options", [""]*4)[1] if "options" in q else "",
                option_c=q.get("options", [""]*4)[2] if "options" in q else "",
                option_d=q.get("options", [""]*4)[3] if "options" in q else "",
                # Jawaban (fleksibel)
                correct_answer=q.get("answer") or q.get("answer_key") or "",
                # Tambahan
            #     question_type=q.get("type", "pilihan_ganda"),  # bisa diisi model jika mau
            #     difficulty=q.get("difficulty", "sedang"),
            #     rubrik=q.get("rubrik", None)  # kalau essay, bisa simpan rubrik di sini
            )
            inserted_count += 1

        return Response({
            "message": "Berhasil generate soal",
            "jumlah": inserted_count,
            "preview": questions_data[:2]  # tampilkan 2 soal pertama
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def get_questions(request):
    questions = Question.objects.all()
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)