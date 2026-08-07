import uuid

from django.db import models


class Scan(models.Model):
    """One saved MRI analysis: the uploaded image + the model's prediction
    and its three XAI visualizations, all as base64 PNG text so nothing
    extra (media storage, file cleanup) is needed for a student project."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    predicted_class = models.CharField(max_length=64)
    confidence = models.FloatField()
    processing_time = models.FloatField(null=True, blank=True)
    summary = models.TextField(blank=True, default="")

    original_image_b64 = models.TextField()
    gradcam_b64 = models.TextField(blank=True, default="")
    shap_b64 = models.TextField(blank=True, default="")
    integrated_gradients_b64 = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.predicted_class} ({self.confidence}%) @ {self.created_at:%Y-%m-%d %H:%M}"
