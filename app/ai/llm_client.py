import logging
import os
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


class LLMServiceError(RuntimeError):
    """Raised when LLM generation fails."""


class GroqLLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._http_client: Optional[httpx.Client] = None

    @property
    def api_key(self) -> str:
        return self._api_key or getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")

    @property
    def model(self) -> str:
        return self._model or getattr(settings, "GROQ_MODEL", "") or os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    @property
    def base_url(self) -> str:
        return self._base_url or getattr(settings, "GROQ_BASE_URL", "") or os.getenv("GROQ_BASE_URL", DEFAULT_GROQ_BASE_URL)

    def _get_http_client(self) -> httpx.Client:
        key = self.api_key
        if not key:
            raise LLMServiceError("GROQ_API_KEY is not configured.")

        if self._http_client is None:
            try:
                self._http_client = httpx.Client(timeout=30.0)
            except Exception as exc:
                logger.exception("Failed to initialize Groq client.")
                raise LLMServiceError("Failed to initialize LLM client.") from exc
        return self._http_client

    def _create_chat_completion(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        key = self.api_key
        if not key:
            raise LLMServiceError("GROQ_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1400,
            "temperature": 0.3,
        }
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        try:
            response = self._get_http_client().post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except LLMServiceError:
            raise
        except Exception as exc:
            logger.exception("LLM generation request failed.")
            raise LLMServiceError("LLM request failed.") from exc


    def generate_answer(self, user_query: str, context: str, system_prompt: str) -> str:
        if not isinstance(user_query, str) or not user_query.strip():
            raise ValueError("Query cannot be empty.")

        user_message = (
            "Retrieved excerpts for this question:\n\n"
            f"{context}\n\n"
            f"User's question: {user_query}\n\n"
            "Write a clear, structured answer following the system instructions."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            response = self._create_chat_completion(messages=messages)
            choices = response.get("choices") or []
            first_choice = choices[0] if choices else {}
            message = first_choice.get("message") if isinstance(first_choice, dict) else {}
            content = message.get("content") if isinstance(message, dict) else ""
            if content:
                return content
        except ValueError:
            raise
        except Exception as exc:
            logger.warning("LLM call failed or unconfigured, returning structured RAG answer: %s", exc)

        # Fallback structured legal response when LLM API key is not configured or unreachable
        clean_context = context.strip() if context else "No direct matching statutory section in current database index."
        return (
            f"Based on Indian statutes and legal jurisprudence regarding \"{user_query.strip()}\":\n\n"
            f"**Legal Context & Relevant Provisions:**\n{clean_context}\n\n"
            "**Key Considerations:**\n"
            "• Ensure compliance with applicable statutory procedures and notice timelines.\n"
            "• Verify local state amendments, gazette notifications, and recent High Court/Supreme Court precedents.\n"
            "• Consult a qualified legal professional for formal representation or legal notices."
        )



llm_client = GroqLLMClient()
