import json
import urllib.error
import urllib.request
from typing import Any, Callable, Iterable

from app.core.config import settings
from app.services.llm.base import LLMProvider


ToolExecutor = Callable[[str, dict[str, Any]], Any]


class OllamaProvider(LLMProvider):
    """Provider local da GAZARRA IA usando a API HTTP do Ollama."""

    def __init__(self):
        if not settings.ollama_model:
            raise RuntimeError("OLLAMA_MODEL não configurado.")

        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds

    def _payload(
        self,
        messages: list[dict],
        *,
        stream: bool,
        tools: list[dict] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "think": settings.ollama_think,
            "keep_alive": settings.ollama_keep_alive,
            "options": {
                "temperature": 0.15,
                "num_ctx": 8192,
                "num_predict": settings.ollama_num_predict,
            },
        }
        if tools:
            payload["tools"] = tools
        return payload

    def _request(self, payload: dict[str, Any]):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )

    def _chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        request = self._request(self._payload(messages, stream=False, tools=tools))
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Não foi possível conectar ao Ollama. "
                f"Verifique {self.base_url} e se o aplicativo Ollama está em execução."
            ) from exc

    def analyze(self, system_prompt: str, user_prompt: str) -> str:
        response = self._chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        return (response.get("message") or {}).get("content", "").strip()

    def stream_analyze(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        history: list[dict[str, str]] | None = None,
        images: list[str] | None = None,
    ) -> Iterable[str]:
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for item in history or []:
            if item.get("role") in {"user", "assistant"} and item.get("content"):
                messages.append({"role": item["role"], "content": item["content"]})

        user_message: dict[str, Any] = {"role": "user", "content": user_prompt}
        if images:
            user_message["images"] = images
        messages.append(user_message)

        request = self._request(self._payload(messages, stream=True))
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    event = json.loads(line)
                    content = (event.get("message") or {}).get("content") or ""
                    if content:
                        yield content
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Não foi possível conectar ao Ollama. "
                f"Verifique {self.base_url} e se o aplicativo Ollama está em execução."
            ) from exc

    def chat_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict],
        executor: ToolExecutor,
        max_rounds: int = 2,
    ) -> tuple[str, list[str]]:
        """Loop de tool calling. Usado quando a pergunta realmente exige dados internos."""
        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        tools_used: list[str] = []

        for _ in range(max_rounds):
            response = self._chat(messages, tools=tools)
            assistant_message = response.get("message") or {}
            tool_calls = assistant_message.get("tool_calls") or []

            if not tool_calls:
                content = (assistant_message.get("content") or "").strip()
                if content:
                    return content, tools_used
                return "Não consegui concluir a análise com os dados disponíveis.", tools_used

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.get("content", ""),
                    "tool_calls": tool_calls,
                }
            )

            for call in tool_calls:
                function = call.get("function") or {}
                name = function.get("name")
                arguments = function.get("arguments") or {}
                if not name:
                    continue

                if not isinstance(arguments, dict):
                    try:
                        arguments = json.loads(arguments)
                    except Exception:
                        arguments = {}

                result = executor(name, arguments)
                tools_used.append(name)
                messages.append(
                    {
                        "role": "tool",
                        "tool_name": name,
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )

        return (
            "A análise exigiu mais etapas do que o limite configurado. "
            "Refaça a pergunta de forma mais específica.",
            tools_used,
        )
