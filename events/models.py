from django.db import models
from django.conf import settings

class Notice(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notices")

    # department wise
    department = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.title
