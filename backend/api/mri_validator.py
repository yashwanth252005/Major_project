"""
Brain MRI image validator using Google Gemini.

This module checks whether an uploaded image appears to be
a valid brain MRI image before sending it to the DenseNet121
tumor classification model.

IMPORTANT:
This is an image-type validation step only.
It is NOT a medical diagnosis.
"""

import json
import os
import re

from django.conf import settings
from google import genai
from google.genai import types


class MRIValidator:
    """
    Validates whether an uploaded image appears to be
    a brain MRI image using Gemini.
    """

    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.model = getattr(
            settings,
            "GEMINI_MODEL",
            "gemini-3.8-flash",
        )

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Please set the GEMINI_API_KEY environment variable."
            )

        self.client = genai.Client(api_key=self.api_key)

    def validate(self, image_path: str, mime_type: str) -> dict:
        """
        Check whether the supplied image appears to be
        a brain MRI.

        Args:
            image_path: Path to the uploaded image.
            mime_type: MIME type such as image/jpeg or image/png.

        Returns:
            {
                "is_mri": True/False,
                "message": "..."
            }
        """

        if not os.path.exists(image_path):
            raise FileNotFoundError(
                f"Image file not found: {image_path}"
            )

        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        prompt = """
You are an image validation system for a Brain Tumor MRI
classification application.

Your ONLY task is to determine whether the uploaded image
appears to be a brain MRI image.

Classify the image as:

TRUE if:
- It appears to be an MRI scan/image of the human brain or head.
- It has characteristics consistent with a brain MRI slice or
  brain MRI study.
- It may contain common MRI display elements, labels, borders,
  or radiology-style presentation.

FALSE if:
- It is a normal photograph.
- It is a selfie or human face photograph.
- It is an X-ray.
- It is a CT scan.
- It is an ultrasound image.
- It is a non-medical image.
- It is an image of another body part without a brain MRI.
- It is clearly unrelated to brain MRI imaging.
- The image cannot reasonably be identified as a brain MRI.

Do NOT try to diagnose a tumor.
Do NOT determine whether the MRI is normal or abnormal.
Do NOT determine the tumor type.

Return ONLY valid JSON in exactly this format:

{
  "is_mri": true,
  "message": "The image appears to be a brain MRI."
}

or

{
  "is_mri": false,
  "message": "The uploaded image does not appear to be a brain MRI."
}

Do not include Markdown.
Do not include ```json.
Do not include any additional text.
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                prompt,
            ],
        )

        response_text = response.text.strip()

        result = self._parse_response(response_text)

        return result

    @staticmethod
    def _parse_response(response_text: str) -> dict:
        """
        Safely parse Gemini's response.

        Gemini is instructed to return JSON, but this method also
        handles the occasional case where the response is wrapped
        in a Markdown JSON code block.
        """

        cleaned = response_text.strip()

        # Remove accidental Markdown code fences.
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(
                "Gemini returned an invalid validation response."
            )

        if "is_mri" not in result:
            raise ValueError(
                "Gemini validation response is missing 'is_mri'."
            )

        is_mri = result["is_mri"]

        if not isinstance(is_mri, bool):
            raise ValueError(
                "Gemini validation response contains an invalid "
                "'is_mri' value."
            )

        if is_mri:
            message = result.get(
                "message",
                "The image appears to be a brain MRI.",
            )
        else:
            message = result.get(
                "message",
                "The uploaded image does not appear to be a brain MRI.",
            )

        return {
            "is_mri": is_mri,
            "message": message,
        }


# ------------------------------------------------------------
# Convenience function
# ------------------------------------------------------------

_validator = None


def validate_mri(image_path: str, mime_type: str) -> dict:
    """
    Validate an image using a cached MRIValidator instance.

    This prevents creating a new Gemini client for every request.
    """

    global _validator

    if _validator is None:
        _validator = MRIValidator()

    return _validator.validate(
        image_path=image_path,
        mime_type=mime_type,
    )