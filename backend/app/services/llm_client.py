import json
import re
import asyncio
from typing import Any, Dict, List, Optional
import httpx

from backend.app.config import settings

def clean_json_text(text: str) -> str:
    """Removes markdown code fences and strips whitespace from LLM output."""
    if not text:
        return ""
    cleaned = text.strip()
    # Strip markdown ```json ... ``` or ``` ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()
    if not (cleaned.startswith("{") or cleaned.startswith("[")):
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
    return cleaned



class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self.model = model if model is not None else settings.LLM_MODEL
        self.base_url = base_url if base_url is not None else getattr(settings, "LLM_BASE_URL", "")
        self._client = httpx.Client(
            timeout=1.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=50)
        )

    def get_provider(self) -> str:
        """
        Determines LLM provider safely from model name, base_url, or API key format.
        - Returns 'gemini' if 'gemini' in model name.
        - Returns 'groq' if 'groq', 'llama', 'mixtral', or 'gsk_' is detected.
        - Returns 'openai' for standard OpenAI models.
        """
        model_lower = (self.model or "").lower()
        key_str = self.api_key or ""
        base_str = (self.base_url or "").lower()

        if "gemini" in model_lower:
            return "gemini"
        elif "groq" in base_str or "groq" in model_lower or "llama" in model_lower or "mixtral" in model_lower or key_str.startswith("gsk_"):
            return "groq"
        else:
            return "openai"

    def _call_gemini_api(self, prompt: str, timeout: float = 1.0) -> str:
        """Call Gemini REST API directly if Gemini model selected."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }
        resp = self._client.post(url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_openai_compatible_api(self, prompt: str, endpoint_url: str, timeout: float = 1.0) -> str:
        """Call OpenAI-compatible REST API (Groq or OpenAI) with Bearer token authentication."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        resp = self._client.post(endpoint_url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _call_groq_api(self, prompt: str, timeout: float = 1.0) -> str:
        """Call Groq REST API (OpenAI-compatible endpoint)."""
        endpoint_url = self.base_url.rstrip("/") + "/chat/completions" if self.base_url else "https://api.groq.com/openai/v1/chat/completions"
        return self._call_openai_compatible_api(prompt, endpoint_url, timeout=timeout)

    def _call_openai_api(self, prompt: str, timeout: float = 1.0) -> str:
        """Call OpenAI REST API."""
        endpoint_url = self.base_url.rstrip("/") + "/chat/completions" if self.base_url else "https://api.openai.com/v1/chat/completions"
        return self._call_openai_compatible_api(prompt, endpoint_url, timeout=timeout)

    def generate_json(self, prompt: str, mock_fallback: Optional[Any] = None, max_retries: int = 3) -> Any:
        """
        Generates JSON from LLM prompt. Retries on failure with exponential backoff.
        If no valid API key is provided or retries fail, returns mock_fallback or raises.
        """
        if not self.api_key or self.api_key.strip() in ("", "your_api_key_here", "dummy"):
            if mock_fallback is not None:
                return mock_fallback
            raise ValueError("No valid LLM_API_KEY provided in configuration/environment.")

        last_error = None
        provider = self.get_provider()

        import time
        import random

        for attempt in range(max_retries):
            try:
                if provider == "gemini":
                    raw_text = self._call_gemini_api(prompt)
                elif provider == "groq":
                    raw_text = self._call_groq_api(prompt)
                else:
                    raw_text = self._call_openai_api(prompt)

                cleaned = clean_json_text(raw_text)
                return json.loads(cleaned)
            except httpx.TimeoutException as e:
                last_error = e
                if mock_fallback is not None:
                    return mock_fallback
                if attempt < max_retries - 1:
                    time.sleep(0.5)
            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code if e.response is not None else 0
                
                # Immediate break on non-retriable client configuration errors
                if status_code in (400, 401, 403, 404):
                    break

                # Exponential backoff on rate limits (429) or server errors (5xx)
                if status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                    retry_after = None
                    if e.response is not None and "retry-after" in e.response.headers:
                        try:
                            retry_after = float(e.response.headers["retry-after"])
                        except ValueError:
                            pass
                    
                    sleep_time = retry_after if retry_after is not None else (1.5 ** (attempt + 1) + random.uniform(0.1, 0.5))
                    time.sleep(min(3.0, sleep_time))
                elif attempt < max_retries - 1:
                    time.sleep(1.0 * (attempt + 1))
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(1.0 * (attempt + 1))

        if mock_fallback is not None:
            return mock_fallback
        raise RuntimeError(f"Failed to generate valid JSON from LLM after {max_retries} attempts. Error: {last_error}")

llm_client = LLMClient()

