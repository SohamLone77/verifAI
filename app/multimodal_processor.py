# MULTIMODAL
from __future__ import annotations

"""
app/multimodal_processor.py

Handles multi-modal action payloads before they reach the graders.

Three public functions:
  - extract_text_from_image(b64, url)  ->  str
  - validate_structured_output(output, schema)  ->  ValidationResult
  - normalize_to_text(action)          ->  str
"""

import base64
import json
import os
from typing import Any, Optional

from app.models import Action, ValidationResult


# ---------------------------------------------------------------------------
# Vision: extract text description from an image using an OpenAI-compat API
# ---------------------------------------------------------------------------

def extract_text_from_image(
    b64: Optional[str] = None,
    url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Call a vision-capable LLM to produce a textual description of an image.

    Priority: base64 > URL.  Falls back to a placeholder if no API key is set
    (so the rest of the pipeline still works during tests without network calls).

    Returns:
        A string description of the image content.
    """
    if not b64 and not url:
        raise ValueError("extract_text_from_image requires either b64 or url.")

    key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        # Graceful degradation: return a generic placeholder so graders can run
        return "[Image provided — vision API key not set; treating as empty text for grading]"

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
            default_headers={"HTTP-Referer": "https://verifai.local", "X-Title": "VerifAI"},
        )
        vision_model = "google/gemma-3-4b-it:free"

        # Build vision message content
        if b64:
            # Detect MIME type from leading bytes
            mime = _detect_mime(b64)
            image_content: dict[str, Any] = {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            }
        else:
            image_content = {
                "type": "image_url",
                "image_url": {"url": url},
            }

        messages = [
            {
                "role": "user",
                "content": [
                    image_content,
                    {
                        "type": "text",
                        "text": (
                            "Describe the content of this image clearly and concisely. "
                            "Focus on text visible in the image, key objects, and context."
                        ),
                    },
                ],
            }
        ]

        response = client.chat.completions.create(
            model=vision_model,
            messages=messages,
            max_tokens=400,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    except Exception as exc:  # pragma: no cover
        return f"[Vision API error: {exc}]"


def _detect_mime(b64: str) -> str:
    """Infer image MIME type from the first bytes of a base64 string."""
    try:
        header = base64.b64decode(b64[:12] + "==")[:4]
        if header[:2] == b"\xff\xd8":
            return "image/jpeg"
        if header[:4] == b"\x89PNG":
            return "image/png"
        if header[:4] == b"GIF8":
            return "image/gif"
        if header[:4] == b"RIFF":
            return "image/webp"
    except Exception:
        pass
    return "image/png"  # safe default


# ---------------------------------------------------------------------------
# Structured output validation
# ---------------------------------------------------------------------------

def validate_structured_output(
    output: dict[str, Any],
    schema: dict[str, Any],
) -> ValidationResult:
    """
    Validate a structured JSON output dict against a JSON-Schema-like schema dict.

    The schema dict supports:
      - "required": list[str]  — keys that must be present
      - "properties": dict[str, {"type": str}]  — per-key type checks
      - "additionalProperties": bool  — whether unknown keys are allowed (default True)

    Returns a ValidationResult with .valid, .errors, and .normalized_text.
    """
    errors: list[str] = []

    required_keys: list[str] = schema.get("required", [])
    for key in required_keys:
        if key not in output:
            errors.append(f"Missing required field: '{key}'")

    properties: dict[str, Any] = schema.get("properties", {})
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }
    for field_name, field_schema in properties.items():
        if field_name not in output:
            continue  # missing required keys already caught above
        expected_type_name = field_schema.get("type")
        if expected_type_name:
            expected_type = type_map.get(expected_type_name)
            if expected_type and not isinstance(output[field_name], expected_type):
                actual = type(output[field_name]).__name__
                errors.append(
                    f"Field '{field_name}': expected {expected_type_name}, got {actual}"
                )

    if not schema.get("additionalProperties", True):
        known_keys = set(properties.keys()) | set(required_keys)
        for key in output:
            if key not in known_keys:
                errors.append(f"Unexpected field: '{key}'")

    # Produce a normalized text representation for grading
    normalized = _structured_to_text(output)

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        normalized_text=normalized,
    )


def _structured_to_text(data: dict[str, Any]) -> str:
    """Convert a structured dict to a human-readable text string for grading."""
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Normalize any modality to plain text for grader compatibility
# ---------------------------------------------------------------------------

def normalize_to_text(action: Action) -> str:
    """
    Convert any action (text / image / structured) into a plain string
    that the rubric and semantic graders can consume.

    - text      → action.content (pass-through)
    - image     → extract_text_from_image(b64 or url), prepend action.content if non-empty
    - structured → _structured_to_text(action.structured_data), prepend action.content if set
    """
    modality = getattr(action, "modality", "text")

    if modality == "image":
        image_text = extract_text_from_image(
            b64=action.image_b64,
            url=action.image_url,
        )
        prefix = f"{action.content}\n\n" if action.content.strip() else ""
        return f"{prefix}[Image description]: {image_text}"

    if modality == "structured":
        struct_text = _structured_to_text(action.structured_data or {})
        prefix = f"{action.content}\n\n" if action.content.strip() else ""
        return f"{prefix}{struct_text}"

    # Default: text modality — return content as-is
    return action.content
