---
name: 13-irrf
description: Calcular e conferir retenção de imposto de renda por pagamento.
version: 2.0.0
status: homologacao
tools: Read, Grep
---

# IRRF da folha — GAZARRA

## Origem e escopo
Reconstruído a partir de `30-calculo-irrf-folha.md` do pacote adquirido. Preserva a finalidade e os checklists úteis, mas substitui tabelas, prazos e instruções de execução não validados. Aplicar `00-governanca-e-seguranca.md`.

## Objetivo
Calcular e conferir retenção de imposto de renda por pagamento.

## Entradas obrigatórias
Competência e datas relevantes; identificação mínima do contribuinte/empregador; regime e categoria; documentos e dados necessários ao caso; parâmetros do ERP; fontes oficiais aplicáveis. Solicitar somente os dados faltantes que sejam indispensáveis.

## Procedimento
Identificar data de pagamento, natureza do rendimento, regime de tributação, dependentes, pensão judicial, previdência dedutível e demais deduções legais. Consultar tabela vigente na data aplicável. Comparar deduções legais com desconto simplificado quando permitido, sem cumulá-los indevidamente. Para pagamentos sujeitos às regras de 2026, verificar a Lei 15.270/2025 e a redução aplicável a rendimentos até R$ 7.350, inclusive a faixa de isenção efetiva até R$ 5.000, observando condições legais. A referência de R$ 607,20 é parâmetro de 2026, não constante universal. Separar 13º, férias e demais rendimentos quando a legislação exigir tratamento específico. Conciliar retenção, folha, eSocial e DCTFWeb.

## Entregáveis
Memória de base, deduções, tabela, redução, imposto e conciliação; pendências.

## Fontes de referência
- IRRF: https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2026
- Lei 15.270/2025: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15270.htm
- eSocial: https://www.gov.br/esocial/pt-br/documentacao-tecnica
- DCTFWeb/MIT: https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/declaracoes-e-demonstrativos/DCTFWeb

## Critérios de bloqueio
Não concluir cálculo sem dados suficientes e parâmetros vigentes. Não apresentar simulação como valor definitivo. Não executar transmissão, pagamento, retificação, alteração de cadastro ou lançamento. Encaminhar questões jurídicas complexas ao profissional responsável.

## Autoavaliação
Verificar competência, fonte, vigência, dados, cálculo independente, conciliação, proteção de dados e aprovação humana. Registrar o que foi efetivamente conferido e o que permanece pendente.
