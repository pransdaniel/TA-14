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
from .utils.question_gen import generate_questions_gemini, extract_question_types, validate_question_types 

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
        instructions = "Buat 5 soal multiple choice dengan 4 opsi (A,B,C,D), satu jawaban benar."

    try:
        # Extract tipe soal yang diizinkan dari instruksi
        allowed_types = extract_question_types(instructions)
        
        questions_data = generate_questions_gemini(
            text=text,
            prompt_instructions=instructions,
            num_questions=int(jumlah_soal)
        )

        if isinstance(questions_data, dict) and "error" in questions_data:
            return Response(questions_data, status=500)

        # Validasi: filter hanya soal dengan tipe yang diizinkan
        validated_questions = validate_question_types(questions_data, allowed_types)
        
        if not validated_questions:
            return Response({
                "error": "Tidak ada soal yang sesuai dengan instruksi. Tipe yang diizinkan: " + ", ".join(allowed_types),
                "expected_types": allowed_types,
                "received_types": [q.get("type", "unknown") for q in questions_data]
            }, status=400)

        inserted_count = 0
        for q in validated_questions:
            # Tentukan tipe soal
            question_type = q.get("type", "multiple_choice")
            
            # Persiapan data umum
            question_data = {
                "source_id": source_id,
                "question": q.get("question", "").strip(),
                "question_type": question_type,
            }
            
            # Handling berdasarkan tipe soal
            if question_type == "matching":
                # Untuk matching: simpan pairs dan answer_key
                question_data["matching_pairs"] = {
                    "pairs": q.get("pairs", []),
                    "answer_key": q.get("answer_key", [])
                }
                question_data["correct_answer"] = str(q.get("answer_key", []))
            elif question_type == "true_false":
                # Pastikan jawaban hanya True atau False
                ans = str(q.get("answer", "")).capitalize()
                if ans not in ["True", "False"]:
                    ans = "True"  # default jika aneh
                question_data["correct_answer"] = ans
                # optional: set options for consistency
                question_data["option_a"] = "True"
                question_data["option_b"] = "False"
            else:
                # Untuk pilihan ganda atau jenis teks lain
                if "options" in q:
                    options = q.get("options", [])
                    question_data["option_a"] = options[0] if len(options) > 0 else ""
                    question_data["option_b"] = options[1] if len(options) > 1 else ""
                    question_data["option_c"] = options[2] if len(options) > 2 else ""
                    question_data["option_d"] = options[3] if len(options) > 3 else ""
                
                # Jawaban (essay, isian, atau pilihan ganda)
                question_data["correct_answer"] = q.get("answer") or q.get("answer_key") or ""
            
            question_obj = Question.objects.create(**question_data)
            inserted_count += 1

        return Response({
            "message": "Berhasil generate soal",
            "jumlah": inserted_count,
            "tipe_soal": allowed_types,
            "preview": validated_questions[:50]
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def get_questions(request):
    questions = Question.objects.all()
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)