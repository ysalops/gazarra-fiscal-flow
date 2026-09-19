---
name: 12-inss
description: Conferir contribuições previdenciárias e bases da folha.
version: 2.0.0
status: homologacao
tools: Read, Grep
---

# INSS — GAZARRA

## Origem e escopo
Reconstruído a partir de `14-inss-fgts.md` do pacote adquirido. Preserva a finalidade e os checklists úteis, mas substitui tabelas, prazos e instruções de execução não validados. Aplicar `00-governanca-e-seguranca.md`.

## Objetivo
Conferir contribuições previdenciárias e bases da folha.

## Entradas obrigatórias
Competência e datas relevantes; identificação mínima do contribuinte/empregador; regime e categoria; documentos e dados necessários ao caso; parâmetros do ERP; fontes oficiais aplicáveis. Solicitar somente os dados faltantes que sejam indispensáveis.

## Procedimento
Separar segurado empregado, doméstico, avulso, contribuinte individual e demais categorias. Identificar remuneração, múltiplos vínculos, teto, incidências, afastamentos, 13º, patronal, RAT/FAP, terceiros, desoneração e regime conforme aplicabilidade. Buscar tabela oficial por competência. A tabela de 2026 consultada confirma teto de R$ 8.475,55 a partir de janeiro, mas o agente não deve usar esse valor para outras competências sem validação. Calcular contribuição progressiva por faixas quando aplicável, com arredondamento conforme norma. Confrontar totalizadores eSocial/DCTFWeb. Não confundir desconto do segurado com encargo patronal.

## Entregáveis
Memória por trabalhador e categoria; bases; contribuições; conciliação e pendências.

## Fontes de referência
- INSS: https://www.gov.br/inss/pt-br/direitos-e-deveres/inscricao-e-contribuicao/tabela-de-contribuicao-mensal
- eSocial: https://www.gov.br/esocial/pt-br/documentacao-tecnica
- DCTFWeb/MIT: https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/declaracoes-e-demonstrativos/DCTFWeb

## Critérios de bloqueio
Não concluir cálculo sem dados suficientes e parâmetros vigentes. Não apresentar simulação como valor definitivo. Não executar transmissão, pagamento, retificação, alteração de cadastro ou lançamento. Encaminhar questões jurídicas complexas ao profissional responsável.

## Autoavaliação
Verificar competência, fonte, vigência, dados, cálculo independente, conciliação, proteção de dados e aprovação humana. Registrar o que foi efetivamente conferido e o que permanece pendente.
