from app.core.config import settings
from app.services.llm.bedrock_provider import BedrockClaudeProvider
from app.services.llm.openai_provider import OpenAIProvider


def get_llm_provider():
    provider = settings.llm_provider.lower().strip()

    if provider == "bedrock":
        return BedrockClaudeProvider()

    if provider == "openai":
        return OpenAIProvider()

    return None
