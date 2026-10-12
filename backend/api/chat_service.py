"""Gemini client isolated from the prediction/XAI pipeline."""

from django.conf import settings
from google import genai
from google.genai import errors

_client = None


def _get_client():
    global _client
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client


def _is_temporary_provider_error(exc):
    """Recognize temporary Gemini capacity/rate-limit errors across SDK versions."""
    status_code = getattr(exc, "status_code", None)
    if status_code in {429, 503}:
        return True

    code = getattr(exc, "code", None)
    if code in {429, 503}:
        return True

    message = str(exc).upper()
    return (
        "429" in message
        or "503" in message
        or "RESOURCE_EXHAUSTED" in message
        or "UNAVAILABLE" in message
        or "HIGH DEMAND" in message
    )


def _generate_with_model(model, prompt):
    """Make one application-level request; the SDK manages its own retries."""
    response = _get_client().models.generate_content(
        model=model,
        contents=prompt,
    )
    answer = (getattr(response, "text", "") or "").strip()
    if not answer:
        raise RuntimeError("The assistant returned an empty response.")
    return answer


def generate_chat_answer(prompt):
    """Try Gemini models in low-latency order for scan-aware chat."""
    primary_model = getattr(
        settings,
        "GEMINI_CHAT_MODEL",
        "gemini-3.5-flash-lite",
    )
    fallback_model = getattr(
        settings,
        "GEMINI_CHAT_FALLBACK_MODEL",
        "gemini-3.7-flash",
    )
    emergency_model = getattr(
        settings,
        "GEMINI_CHAT_EMERGENCY_MODEL",
        getattr(settings, "GEMINI_MODEL", "gemini-3.8-flash"),
    )

    models = []
    for model in (primary_model, fallback_model, emergency_model):
        if model and model not in models:
            models.append(model)

    last_error = None
    for index, model in enumerate(models):
        try:
            return _generate_with_model(model, prompt)
        except (errors.ServerError, errors.ClientError) as exc:
            last_error = exc
            if not _is_temporary_provider_error(exc):
                raise
            if index == len(models) - 1:
                raise

    if last_error is not None:
        raise last_error
    raise RuntimeError("No Gemini chat model is configured.")
