import base64
import os
import tempfile
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .inference import run_prediction
from .models import Scan
from .serializers import ScanDetailSerializer, ScanListSerializer

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


@api_view(["POST"])
def predict_view(request):
    file_obj = request.FILES.get("image")

    if not file_obj:
        return Response(
            {"error": "No image uploaded. Send it as multipart/form-data under the key 'image'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return Response(
            {"error": f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    file_bytes = file_obj.read()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        result = run_prediction(tmp_path)

        scan = Scan.objects.create(
            predicted_class=result["prediction"]["class"],
            confidence=result["prediction"]["confidence"],
            processing_time=result.get("processing_time"),
            summary=result.get("summary", ""),
            original_image_b64=base64.b64encode(file_bytes).decode("utf-8"),
            gradcam_b64=result.get("gradcam", ""),
            shap_b64=result.get("shap", ""),
            integrated_gradients_b64=result.get("integrated_gradients", ""),
        )

        response_data = dict(result)
        response_data["id"] = str(scan.id)
        response_data["created_at"] = scan.created_at.isoformat()
        response_data["original_image"] = scan.original_image_b64
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        return Response(
            {"error": "Inference failed.", "detail": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@api_view(["GET"])
def history_list_view(request):
    scans = Scan.objects.all()
    return Response(ScanListSerializer(scans, many=True).data)


@api_view(["GET", "DELETE"])
def history_detail_view(request, scan_id):
    try:
        scan = Scan.objects.get(id=scan_id)
    except Scan.DoesNotExist:
        return Response({"error": "Scan not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "DELETE":
        scan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(ScanDetailSerializer(scan).data)


@api_view(["GET"])
def health_view(request):
    return Response({"status": "ok"})
