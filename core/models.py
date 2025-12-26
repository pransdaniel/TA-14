from django.db import models

class Source(models.Model):
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Question(models.Model):
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)
    topic = models.CharField(max_length=255, blank=True, null=True)
    question = models.TextField()
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    # Allow long answers (essay, rubrik, full-text keys)
    correct_answer = models.TextField()
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
