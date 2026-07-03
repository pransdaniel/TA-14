from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import EssayRequestSerializer
from .similarity_service import calculate_similarity
from .gemini_service import gemini_score


@api_view(['POST'])
def evaluate(request):

    serializer = EssayRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    reference = serializer.validated_data["reference"]
    essay = serializer.validated_data["essay"]

    similarity = round(calculate_similarity(reference, essay), 2)

    ai_score = round(gemini_score(reference, essay), 2)

    if ai_score is not None:
        final_score = round((0.4 * similarity) + (0.6 * ai_score), 2)
        response_data = {
            "similarity": similarity,
            "gemini_score": ai_score,
            "final_score": final_score
        }
    else:
        # If both Gemini API keys are limited, use similarity only
        final_score = similarity
        response_data = {
            "similarity": similarity,
            "gemini_score": None,
            "final_score": final_score,
            "note": "Both Gemini API keys reached limit, using cosine similarity only"
        }

    return Response(response_data)
