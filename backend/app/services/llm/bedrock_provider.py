import json

import boto3

from app.core.config import settings
from app.services.llm.base import LLMProvider


class BedrockClaudeProvider(LLMProvider):
    def __init__(self):
        if not settings.bedrock_model_id:
            raise RuntimeError("BEDROCK_MODEL_ID não configurado.")

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
        )

    def analyze(self, system_prompt: str, user_prompt: str) -> str:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1200,
            "temperature": 0.1,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt,
                        }
                    ],
                }
            ],
        }

        response = self.client.invoke_model(
            modelId=settings.bedrock_model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        payload = json.loads(response["body"].read())
        return payload["content"][0]["text"]
