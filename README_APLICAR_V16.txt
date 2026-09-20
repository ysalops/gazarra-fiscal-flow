GAZARRA V16 — CHAT-FIRST
========================

O que muda
-----------
- GAZARRA IA deixa de exigir Cliente + Competência antes de conversar.
- Remove os 4 botões fixos (Resumir fechamento, Verificar pendências, Explicar DAS, Analisar ST e DIFAL).
- Conversa geral: pode perguntar assuntos não fiscais também.
- Agentes continuam automáticos e entram quando a pergunta pede contexto especializado.
- Streaming real com Ollama: a resposta aparece progressivamente.
- Contexto de empresa passa a ser OPCIONAL (menu "Contexto automático").
- Competência é identificada pela própria pergunta quando necessária.
- Botão + para anexar PDF, DOCX, XLSX, CSV, TXT, MD, XML, JSON e imagens.
- Qwen recebe imagens diretamente; documentos têm texto extraído no backend.
- Histórico de conversas por usuário salvo no PostgreSQL.
- Detalhes técnicos ficam recolhidos e deixam de poluir o chat.
- Controle de acesso continua no backend: tools só retornam empresas autorizadas.

IMPORTANTE
----------
Este ZIP é OVERLAY. Extraia seu conteúdo diretamente sobre:
C:\Users\Ysa Martinho\Documents\gazarra-poc

e aceite substituir os arquivos.

Não há .env neste ZIP e ele não altera suas credenciais locais.

Aplicação
---------
1) Antes de aplicar, vale salvar o checkpoint atual:

   git add .
   git commit -m "V15.3 estável - IA local, tools e sessão"
   git push

2) Extraia este ZIP por cima da pasta gazarra-poc.

3) Como há novas dependências do backend, reconstrua backend e frontend:

   Set-Location "C:\Users\Ysa Martinho\Documents\gazarra-poc"
   docker compose build --no-cache backend frontend
   docker compose up -d --force-recreate backend frontend
   docker compose ps

4) Abra http://localhost:8080 e faça Ctrl+F5.

Testes sugeridos
----------------
1. Pergunta geral (sem cliente/competência):
   Explique a diferença entre IA generativa e machine learning de forma simples.

2. Conhecimento fiscal sem consultar cliente:
   O que é DAS e para que ele serve?

3. Tool de acesso:
   Quais empresas eu posso acessar?

4. Consulta com empresa/competência escritas na própria pergunta:
   Qual foi o DAS da empresa Beta em maio de 2026?

5. Continuidade de conversa:
   Primeira: O que é ICMS-ST?
   Depois: Explique com um exemplo simples.

6. Arquivo:
   Clique no +, anexe um XML/TXT/PDF e pergunte:
   Analise este arquivo e me diga os principais pontos de atenção.

7. Imagem:
   Clique no +, anexe PNG/JPG e pergunte:
   O que aparece nesta imagem e o que merece atenção?

Validação visual
----------------
- Não deve existir seletor obrigatório de competência.
- Não devem existir os 4 botões antigos.
- O botão + deve anexar arquivos.
- A resposta do Ollama deve aparecer progressivamente.
- "Detalhes técnicos" deve ficar recolhido.
- Conversas devem aparecer no histórico somente para o usuário logado.

Se algo falhar
--------------
Backend:
   docker compose logs backend --tail 150

Frontend:
   docker compose logs frontend --tail 80

Git (depois que os testes passarem)
-----------------------------------
   git add .
   git commit -m "V16 chat-first - streaming, anexos e histórico"
   git push
