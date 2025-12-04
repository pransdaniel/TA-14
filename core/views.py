import os
import tempfile
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Question, Source
from .serializers import QuestionSerializer
from .utils.question_gen import generate_questions_openai
import json

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

        # Simpan file ke folder temporary sistem
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            for chunk in file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name

        # Ekstrak teks dari PDF
        text = extract_text_from_pdf(temp_path)

        # Hapus file temp setelah digunakan (opsional)
        os.remove(temp_path)

        return Response({
            "source_id": source.id,
            "preview": text[:10000]  # preview 500 karakter pertama
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def generate_questions(request):
    source_id = request.data.get("source_id")
    text = request.data.get("text")
    result = generate_questions_openai(text)
    try:
        data = json.loads(result)
        for q in data:
            Question.objects.create(
                source_id=source_id,
                topic=q.get("topic"),
                question=q["question"],
                option_a=q["options"]["A"],
                option_b=q["options"]["B"],
                option_c=q["options"]["C"],
                option_d=q["options"]["D"],
                correct_answer=q["correct"],
                difficulty=q.get("difficulty", 0.5)
            )
        return Response({"inserted": len(data)})
    except Exception as e:
        return Response({"error": str(e), "raw": result}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_questions(request):
    questions = Question.objects.all()
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)
