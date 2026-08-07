from rest_framework import serializers

from .models import Scan


class ScanListSerializer(serializers.ModelSerializer):
    """Lightweight shape for the history grid - includes the original image
    as a thumbnail preview, but not the (larger) XAI overlay images."""

    class Meta:
        model = Scan
        fields = [
            "id",
            "predicted_class",
            "confidence",
            "processing_time",
            "created_at",
            "original_image_b64",
        ]


class ScanDetailSerializer(serializers.ModelSerializer):
    """Full shape for a single scan's report page / PDF export."""

    class Meta:
        model = Scan
        fields = "__all__"
