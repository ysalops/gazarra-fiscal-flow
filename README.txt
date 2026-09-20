GAZARRA V16.2 — DOCUMENTOS + AGENT SELECTOR
===========================================

O que entra nesta versão
------------------------
1. Seletor de agentes com quatro modos:
   - Automático
   - Nenhum agente
   - Manual: 1 ou 2 agentes
   - Todos disponíveis: todo o catálogo fica elegível e o roteador escolhe no máximo os relevantes

2. Catálogo de agentes:
   - resumo imediato extraído da própria especificação .md
   - capacidades
   - quando usar
   - indicador de revisão humana
   - botão "Gerar resumo com IA"
   - o resumo é cacheado em /app/data/agent_catalog.json
   - quando LLM_PROVIDER=bedrock, é o Claude que lê a especificação e gera o resumo
   - enquanto estiver em Ollama, o mesmo fluxo usa o Qwen local

3. Documentos:
   - extração continua ocorrendo uma única vez no upload
   - validação numérica determinística é salva em cache
   - páginas PDF com pouco texto extraível são sinalizadas como visualmente não validadas
   - prompt proíbe inferências sobre certidões/gráficos/imagens não lidos
   - histórico anterior não é reenviado na primeira análise do documento

4. Validações do PDF usado no teste:
   - variação de DAS Maio/2026 x Abril/2026
   - divergência de ST R$ 6.421,63 x R$ 6.423,63
   - DIFAL 18,41x x aproximadamente 5,43x
   - páginas 12, 13 e 14 marcadas como predominantemente visuais

5. Roteamento:
   - "Fechamento Fiscal" prioriza Agente Fiscal
   - menções genéricas a produto não mandam mais um fechamento ao Product Mapper
   - Manual respeita exatamente os agentes escolhidos
   - Todos disponíveis NÃO executa 26 agentes; apenas os deixa elegíveis

6. Performance local:
   - Ollama num_ctx: 8192
   - num_predict passa a respeitar OLLAMA_NUM_PREDICT (padrão atual 320)
   - documentos não carregam histórico antigo na primeira análise

COMO APLICAR
------------
1. Recomendado antes de substituir:

   git add .
   git commit -m "V16.1 estável - chat first e confiabilidade"
   git push

2. Extraia o conteúdo deste ZIP POR CIMA de:

   C:\Users\Ysa Martinho\Documents\gazarra-poc

   Aceite substituir os arquivos.

3. Reconstrua:

   Set-Location "C:\Users\Ysa Martinho\Documents\gazarra-poc"
   docker compose build --no-cache backend frontend
   docker compose up -d --force-recreate backend frontend
   docker compose ps

4. Abra:
   http://localhost:8080
   Ctrl + F5

TESTES RECOMENDADOS
-------------------
A) Automático + PDF de fechamento
   "Analise este arquivo. Separe achados objetivos, inconsistências, pontos de atenção e itens a confirmar."
   Esperado: Agente Fiscal GAZARRA e destaque para validações numéricas.

B) Manual
   Selecione Agente Fiscal GAZARRA + Agente de Revisão SPED.
   Pergunte algo com um arquivo fiscal e confirme que ambos aparecem na resposta/detalhes.

C) Nenhum agente
   "Explique a diferença entre machine learning e IA generativa."
   Esperado: GAZARRA IA geral, sem contexto especializado.

D) Todos disponíveis
   "Analise este fechamento fiscal à luz da reforma tributária CBS/IBS."
   Esperado: o roteador pode escolher até dois agentes relevantes; não os 26.

E) Resumo do agente
   Abra o seletor > "Gerar resumo com IA".
   Na POC local, Qwen gera e armazena o resumo.
   Quando LLM_PROVIDER=bedrock, o mesmo botão chama Claude e mantém o resumo em cache.

OBSERVAÇÕES
-----------
- Não altera .env.
- Não requer migration nova de banco.
- Não conecta Claude automaticamente; prepara e utiliza o provedor configurado.
- PDF visual nativo via Claude/Bedrock será a etapa de produção; nesta POC local páginas sem texto são explicitamente marcadas para não haver falsa leitura.
