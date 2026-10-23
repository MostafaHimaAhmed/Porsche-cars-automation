
import json
import re

from google import genai
from google.genai import types


def analyze_sticker(client, image_bytes, mime_type="image/jpeg"):
    prompt = """
    Extract all options and their prices from this Porsche window sticker.
    Include delivery and processing fees if present.
    Extract the total price as well.

    Be extremely accurate when transcribing option names. Preserve every character exactly as printed, including all parentheses (), spaces, punctuation, symbols, capitalization, and spelling. Do not add, remove, or modify any characters or spaces. Do not skip any options. Double-check each option name against the image to ensure nothing is missing or changed.

    Return valid JSON only:
    {
        "options": {
            "option_name": 123
        },
        "total": 123
    }
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            prompt,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            ),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    return json.loads(response.text)
