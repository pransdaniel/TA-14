from rest_framework import serializers
from .models import Source, Question, User, Response

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'
    
    def to_representation(self, instance):
        """
        Customize output berdasarkan question_type
        """
        ret = super().to_representation(instance)
        
        # Untuk matching, tambahkan informasi pairs dengan format yang lebih jelas
        if instance.question_type == 'matching' and instance.matching_pairs:
            ret['matching_data'] = {
                'pairs': instance.matching_pairs.get('pairs', []),
                'answer_key': instance.matching_pairs.get('answer_key', [])
            }
        
        return ret

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = '__all__'
