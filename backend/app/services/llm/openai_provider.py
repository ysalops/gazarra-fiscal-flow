from openai import OpenAI

from app.core.config import settings
from app.services.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self):
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY não configurada.")

        self.client = OpenAI(
            api_key=settings.openai_api_key,
        )

    def analyze(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.responses.create(
            model=settings.openai_model,
            instructions=system_prompt,
            input=user_prompt,
        )
        return response.output_text
