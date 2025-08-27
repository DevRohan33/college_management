from django.db import models

# Create your models here.
class dataChunks(models.Model):
    source = models.CharField(max_length=255)
    text = models.TextField()
    embedding = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} ({len(self.text)} chars)"