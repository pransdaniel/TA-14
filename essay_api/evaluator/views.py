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

    # TF-IDF Similarity
    similarity = calculate_similarity(reference, essay)

    # Gemini Scoring
    ai_score = gemini_score(reference, essay)

    # Final Score
    final_score = (0.4 * similarity) + (0.6 * ai_score)

    return Response({
        "similarity": similarity,
        "gemini_score": ai_score,
        "final_score": final_score
    })
