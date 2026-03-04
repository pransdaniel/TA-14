from rest_framework import serializers

class EssayRequestSerializer(serializers.Serializer):
    reference = serializers.CharField()
    essay = serializers.CharField()