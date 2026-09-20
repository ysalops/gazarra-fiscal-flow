GAZARRA IA V15 - FASE 1
========================

Objetivo
--------
Conectar a GAZARRA IA ao Ollama/Qwen 3.5 local, mantendo a arquitetura pronta
para trocar para Claude via Amazon Bedrock depois.

Incluído
--------
- OllamaProvider via API HTTP do Ollama
- LLM_PROVIDER=ollama
- qwen3.5:4b
- thinking desativado
- keep_alive configurável
- tool calling real do Ollama
- tool list_companies com filtro Admin/Analista
- tool get_fiscal_dashboard com validação de acesso 403
- /api/ai/status reconhece provider ollama
- /api/ai/chat preserva autenticação e autorização existentes
- DemoProvider/Bedrock/OpenAI continuam disponíveis como arquitetura alternativa

NÃO substitua seu .env pelo .env.example.
Edite seu .env local e adicione/ajuste:

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3.5:4b
OLLAMA_THINK=false
OLLAMA_KEEP_ALIVE=10m
OLLAMA_TIMEOUT_SECONDS=180

Depois:
  docker compose build --no-cache backend
  docker compose up -d --force-recreate backend
  docker compose logs backend --tail 100

Testes no navegador:
1) Entrar como Admin
2) GAZARRA IA
3) Perguntar: Quais empresas existem na base?
   Esperado: Alpha, Beta e Gamma (conforme mock atual)
4) Entrar como Analista
5) Perguntar a mesma coisa
   Esperado: apenas empresas atribuídas ao analista

IMPORTANTE
----------
O Ollama precisa estar aberto/rodando no Windows.
O backend Docker acessa o Ollama em host.docker.internal:11434.
