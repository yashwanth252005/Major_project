import base64
import os
import tempfile
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .inference import run_prediction
from .mri_validator import validate_mri
from .models import ChatMessage, ChatSession, Scan
from .serializers import ScanDetailSerializer, ScanListSerializer
from .scan_context import build_scan_context
from .chat_prompt import build_chat_prompt
from .chat_service import generate_chat_answer


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
            xai_consistency=result.get("xai_consistency", {}),
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


# ============================================================
# SCAN-AWARE XAI CHATBOT API
# ============================================================

@api_view(["GET", "POST", "DELETE"])
def scan_chat_view(request, scan_id):
    try:
        scan = Scan.objects.get(id=scan_id)
    except Scan.DoesNotExist:
        return Response(
            {"error": "Scan not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    session = ChatSession.objects.filter(scan=scan).first()

    if request.method == "GET":
        if not session:
            return Response(
                {"scan_id": str(scan.id), "mode": "simple", "messages": []},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "scan_id": str(scan.id),
                "mode": session.mode,
                "messages": [
                    {
                        "id": message.id,
                        "role": message.role,
                        "content": message.content,
                        "mode": message.mode,
                        "sources": message.sources,
                        "created_at": message.created_at.isoformat(),
                    }
                    for message in session.messages.all()
                ],
            },
            status=status.HTTP_200_OK,
        )

    if request.method == "DELETE":
        if session:
            session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    question = request.data.get("message", "")
    if not isinstance(question, str) or not question.strip():
        return Response(
            {"error": "A non-empty 'message' is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    question = question.strip()
    if len(question) > 4000:
        return Response(
            {"error": "Message is too long. Maximum length is 4000 characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    mode = request.data.get("mode", "simple")
    allowed_modes = {"simple", "technical", "clinical_research"}
    if mode not in allowed_modes:
        return Response(
            {"error": f"Invalid mode. Choose one of: {sorted(allowed_modes)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session, _ = ChatSession.objects.get_or_create(
        scan=scan,
        defaults={"mode": mode},
    )
    if session.mode != mode:
        session.mode = mode
        session.save(update_fields=["mode", "updated_at"])

    persisted_messages = list(
        session.messages.order_by("-created_at", "-id")[:6]
    )
    persisted_messages.reverse()
    conversation = [
        {"role": item.role, "content": item.content}
        for item in persisted_messages
    ]

    scan_context = build_scan_context(scan)
    prompt = build_chat_prompt(
        scan_context=scan_context,
        question=question,
        mode=mode,
        conversation=conversation,
    )

    try:
        answer = generate_chat_answer(prompt)
    except Exception:
        traceback.print_exc()
        return Response(
            {
                "error": "The NeuroScan XAI Assistant is temporarily unavailable.",
                "message": (
                    "The scan analysis remains available. "
                    "Please try the assistant again later."
                ),
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    sources = ["DenseNet121"]
    if scan.gradcam_b64:
        sources.append("Grad-CAM")
    if scan.integrated_gradients_b64:
        sources.append("Integrated Gradients")
    if scan.shap_b64:
        sources.append("SHAP")

    ChatMessage.objects.create(
        session=session,
        role="user",
        content=question,
        mode=mode,
    )
    ChatMessage.objects.create(
        session=session,
        role="assistant",
        content=answer,
        mode=mode,
        sources=sources,
    )

    return Response(
        {
            "scan_id": str(scan.id),
            "answer": answer,
            "mode": mode,
            "sources": sources,
        },
        status=status.HTTP_200_OK,
    )
