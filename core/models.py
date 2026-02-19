from django.db import models
import json

class Source(models.Model):
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Pilihan Ganda'),
        ('true_false', 'Benar / Salah'),
        ('essay', 'Essay'),
        ('isian', 'Isian Singkat'),
        ('matching', 'Matching'),
    ]
    
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)
    topic = models.CharField(max_length=255, blank=True, null=True)
    question = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    
    # Untuk pilihan ganda
    option_a = models.TextField(blank=True, null=True)
    option_b = models.TextField(blank=True, null=True)
    option_c = models.TextField(blank=True, null=True)
    option_d = models.TextField(blank=True, null=True)
    
    # Untuk matching: disimpan sebagai JSON
    # Format: {"pairs": [{"keyword": "...", "explanation": "...", "correct_match": 0}, ...]}
    matching_pairs = models.JSONField(default=dict, blank=True, null=True)
    
    # Allow long answers (essay, rubrik, full-text keys)
    correct_answer = models.TextField(blank=True, null=True)
    difficulty = models.FloatField(default=0.5)
    discrimination = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    theta = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

class Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
