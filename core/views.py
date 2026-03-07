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
from .utils.question_gen import (
    generate_questions_gemini,
    extract_question_types,
    validate_question_types,
    PROMPT_BY_TYPE,       # ← tambahan import
)


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
#  UPLOAD PDF
# ─────────────────────────────────────────────────────────────

@api_view(['POST'])
def upload_pdf(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return Response(
                {"error": "File PDF tidak ditemukan"},
                status=status.HTTP_400_BAD_REQUEST
            )

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


# ─────────────────────────────────────────────────────────────
#  GENERATE QUESTIONS
# ─────────────────────────────────────────────────────────────

@api_view(['POST'])
def generate_questions(request):
    source_id   = request.data.get("source_id")
    text        = request.data.get("text", "").strip()
    instructions = request.data.get("instructions", "").strip()
    jumlah_soal = int(request.data.get("jumlah_soal", 5))

    if not text:
        return Response({"error": "Field 'text' wajib diisi"}, status=400)

    # ── 1. Tentukan tipe yang diizinkan ───────────────────────
    allowed_types = extract_question_types(instructions)
    # allowed_types sudah fallback ke ['short_answer'] jika instruksi kosong

    # ── 2. Bangun combined prompt dari SEMUA tipe yang ditemukan
    #       Inilah penyebab utama error sebelumnya:
    #       instruksi mentah dikirim langsung → Gemini pakai nama tipe sesukanya
    combined_prompt = "\n\n".join(
        PROMPT_BY_TYPE[t] for t in allowed_types if t in PROMPT_BY_TYPE
    )

    # ── 3. Hitung total soal yang diminta
    #       Kalikan jumlah_soal dengan jumlah tipe agar tiap tipe
    #       mendapat kuota, lalu kita trim di langkah validasi
    total_to_generate = jumlah_soal * len(allowed_types)

    try:
        # ── 4. Generate ───────────────────────────────────────
        questions_data = generate_questions_gemini(
            text=text,
            prompt_instructions=combined_prompt,   # ← combined, bukan instructions mentah
            num_questions=total_to_generate,
        )

        if isinstance(questions_data, dict) and "error" in questions_data:
            return Response(questions_data, status=500)

        # ── 5. Validasi & filter tipe ─────────────────────────
        #       normalize_type() sudah dipanggil di dalam
        #       generate_questions_gemini, jadi tipe sudah bersih
        validated_questions = validate_question_types(questions_data, allowed_types)

        if not validated_questions:
            return Response({
                "error": (
                    "Tidak ada soal yang sesuai dengan instruksi. "
                    "Tipe yang diizinkan: " + ", ".join(allowed_types)
                ),
                "expected_types": allowed_types,
                "received_types": [q.get("type", "unknown") for q in questions_data],
                "raw_sample": questions_data[:3],   # bantu debug di Postman
            }, status=400)

        # ── 6. Simpan ke database ─────────────────────────────
        inserted_count = 0
        for q in validated_questions:
            question_type = q.get("type", "short_answer")

            # Normalisasi legacy alias yang mungkin lolos
            if question_type == "isian":
                question_type = "short_answer"

            question_data = {
                "source_id":     source_id,
                "question":      q.get("question", "").strip(),
                "question_type": question_type,
            }

            if question_type == "matching":
                question_data["matching_pairs"] = {
                    "pairs":      q.get("pairs", []),
                    "answer_key": q.get("answer_key", []),
                }
                question_data["correct_answer"] = json.dumps(
                    q.get("answer_key", []), ensure_ascii=False
                )

            elif question_type == "true_false":
                ans = str(q.get("answer", "True")).strip().capitalize()
                if ans not in ("True", "False"):
                    ans = "True"
                question_data["correct_answer"] = ans
                question_data["option_a"] = "True"
                question_data["option_b"] = "False"

            elif question_type == "multiple_choice":
                options = q.get("options", [])
                question_data["option_a"] = options[0] if len(options) > 0 else ""
                question_data["option_b"] = options[1] if len(options) > 1 else ""
                question_data["option_c"] = options[2] if len(options) > 2 else ""
                question_data["option_d"] = options[3] if len(options) > 3 else ""
                question_data["correct_answer"] = q.get("answer", "")

            else:
                # essay / short_answer
                question_data["correct_answer"] = (
                    q.get("answer") or q.get("answer_key") or ""
                )

            Question.objects.create(**question_data)
            inserted_count += 1

        return Response({
            "message":    "Berhasil generate soal",
            "jumlah":     inserted_count,
            "tipe_soal":  allowed_types,
            "preview":    validated_questions[:50],
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=500)


# ─────────────────────────────────────────────────────────────
#  GET QUESTIONS
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
def get_questions(request):
    questions = Question.objects.all()
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)