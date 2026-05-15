import logging
import time
from typing import Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.utils.llm_json import parse_json_strict, validate_model

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - handled at runtime
    genai = None


logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        self.temperature = settings.gemini_temperature if temperature is None else temperature
        self.max_retries = settings.gemini_max_retries if max_retries is None else max_retries

        if genai is None:
            raise RuntimeError("google-generativeai package is not installed")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

        genai.configure(api_key=self.api_key)

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        last_error: Optional[Exception] = None
        prompt = f"{system_prompt.strip()}\n\n{user_prompt.strip()}"

        for attempt in range(self.max_retries + 1):
            try:
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self.temperature,
                        "response_mime_type": "application/json",
                    },
                )
                raw_text = _extract_text(response)
                data = parse_json_strict(raw_text)
                return validate_model(response_model, data)
            except (ValueError, ValidationError, RuntimeError) as exc:
                last_error = exc
                logger.warning(
                    "Gemini response invalid (attempt %s/%s): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 4))
                    continue
                break

        raise RuntimeError("Gemini response invalid after retries") from last_error


def _extract_text(response: object) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text

    try:
        return response.candidates[0].content.parts[0].text
    except Exception as exc:  # pragma: no cover - defensive path
        raise RuntimeError("Gemini response contained no text") from exc
