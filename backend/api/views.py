import base64
import os
import tempfile
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .inference import run_prediction
from .mri_validator import validate_mri
from .models import Scan
from .serializers import ScanDetailSerializer, ScanListSerializer


# ============================================================
# ALLOWED IMAGE TYPES
# ============================================================

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
}


ALLOWED_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".bmp": "image/bmp",
}


# ============================================================
# PREDICTION API
# ============================================================

@api_view(["POST"])
def predict_view(request):
    """
    Main prediction endpoint.

    Flow:

        1. Receive uploaded image
        2. Validate file type
        3. Save temporarily
        4. Validate whether image appears to be a brain MRI
        5. If not MRI -> return friendly error
        6. If MRI -> run DenseNet121 + XAI
        7. Save result to database
        8. Return prediction + explanations
    """

    # --------------------------------------------------------
    # 1. Get uploaded image
    # --------------------------------------------------------

    file_obj = request.FILES.get("image")

    if not file_obj:
        return Response(
            {
                "error": (
                    "No image uploaded. "
                    "Send it as multipart/form-data under "
                    "the key 'image'."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


    # --------------------------------------------------------
    # 2. Validate file extension
    # --------------------------------------------------------

    ext = os.path.splitext(file_obj.name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return Response(
            {
                "error": (
                    f"Unsupported file type '{ext}'. "
                    f"Allowed: {sorted(ALLOWED_EXTENSIONS)}"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


    # --------------------------------------------------------
    # 3. Determine MIME type
    # --------------------------------------------------------

    mime_type = ALLOWED_MIME_TYPES.get(
        ext,
        file_obj.content_type or "application/octet-stream",
    )


    # --------------------------------------------------------
    # 4. Read uploaded file
    # --------------------------------------------------------

    file_bytes = file_obj.read()

    if not file_bytes:
        return Response(
            {
                "error": "The uploaded image is empty."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


    tmp_path = None


    try:

        # ----------------------------------------------------
        # 5. Create temporary image file
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=ext,
        ) as tmp:

            tmp.write(file_bytes)
            tmp_path = tmp.name


        # ====================================================
        # 6. GEMINI MRI VALIDATION
        # ====================================================

        try:

            validation_result = validate_mri(
                image_path=tmp_path,
                mime_type=mime_type,
            )

        except Exception as validation_error:

            traceback.print_exc()

            return Response(
                {
                    "error": "MRI image validation failed.",
                    "detail": str(validation_error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


        # ----------------------------------------------------
        # 7. Reject non-MRI images
        # ----------------------------------------------------

        if not validation_result.get("is_mri", False):

            return Response(
                {
                    "valid_mri": False,
                    "error": "Invalid MRI image.",
                    "message": validation_result.get(
                        "message",
                        (
                            "The uploaded image does not appear "
                            "to be a brain MRI. Please upload a "
                            "valid brain MRI image."
                        ),
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        # ====================================================
        # 8. RUN DENSENET + XAI
        # ====================================================

        result = run_prediction(tmp_path)


        # ====================================================
        # 9. SAVE SCAN HISTORY
        # ====================================================

        scan = Scan.objects.create(
            predicted_class=result["prediction"]["class"],
            confidence=result["prediction"]["confidence"],
            processing_time=result.get("processing_time"),
            summary=result.get("summary", ""),
            original_image_b64=base64.b64encode(
                file_bytes
            ).decode("utf-8"),
            gradcam_b64=result.get("gradcam", ""),
            shap_b64=result.get("shap", ""),
            integrated_gradients_b64=result.get(
                "integrated_gradients",
                "",
            ),
        )


        # ====================================================
        # 10. PREPARE RESPONSE
        # ====================================================

        response_data = dict(result)

        response_data["id"] = str(scan.id)

        response_data["created_at"] = (
            scan.created_at.isoformat()
        )

        response_data["original_image"] = (
            scan.original_image_b64
        )

        # Let frontend know that the image passed
        # the MRI validation stage.
        response_data["valid_mri"] = True


        # ====================================================
        # 11. RETURN SUCCESS RESPONSE
        # ====================================================

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )


    except Exception as exc:

        traceback.print_exc()

        return Response(
            {
                "error": "Inference failed.",
                "detail": str(exc),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


    finally:

        # ----------------------------------------------------
        # 12. Remove temporary file
        # ----------------------------------------------------

        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================================
# HISTORY LIST API
# ============================================================

@api_view(["GET"])
def history_list_view(request):

    scans = Scan.objects.all()

    return Response(
        ScanListSerializer(
            scans,
            many=True,
        ).data
    )


# ============================================================
# HISTORY DETAIL / DELETE API
# ============================================================

@api_view(["GET", "DELETE"])
def history_detail_view(request, scan_id):

    try:

        scan = Scan.objects.get(
            id=scan_id
        )

    except Scan.DoesNotExist:

        return Response(
            {
                "error": "Scan not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )


    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    if request.method == "DELETE":

        scan.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    return Response(
        ScanDetailSerializer(scan).data
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@api_view(["GET"])
def health_view(request):

    return Response(
        {
            "status": "ok"
        }
    )