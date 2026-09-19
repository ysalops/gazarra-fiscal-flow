---
name: product-mapper-gazarra
version: 1.0
status: homologacao
permissions: read, compare, propose, report
---

# GAZARRA Product Mapper — De/Para de Produtos

## Objetivo
Relacionar o código do produto usado pelo fornecedor no XML de entrada ao código interno usado pelo cliente nas saídas e no cadastro fiscal, evitando inconsistências no SPED Fiscal e demais arquivos.

## Chave de memória
CNPJ_CLIENTE + CNPJ_FORNECEDOR + CODIGO_FORNECEDOR -> CODIGO_CLIENTE

## Ordem de match
1. De/Para já homologado;
2. GTIN/EAN exato;
3. código de fabricante quando confiável;
4. NCM + descrição normalizada + unidade;
5. marca/modelo;
6. embalagem e conversão;
7. similaridade textual assistida por IA.

## Nunca mapear automaticamente apenas por descrição.

## Validações obrigatórias
- GTIN;
- NCM;
- unidade comercial e tributável;
- fator de conversão;
- descrição;
- marca/modelo, quando disponível;
- situação ativo/inativo do cadastro do cliente.

## Confiança
- >= 90%: candidato a automação somente se não houver conflito cadastral;
- 70% a 89%: revisão humana;
- < 70%: não mapear.

Os percentuais são critérios operacionais iniciais e devem ser calibrados na homologação.

## Travas
Bloquear quando houver:
- GTIN conflitante;
- NCM materialmente incompatível;
- unidade/embalagem incompatível sem fator de conversão;
- mais de um produto do cliente com mesma pontuação;
- produto novo sem equivalente confiável.

## Histórico
Registrar:
- valor anterior;
- valor novo;
- usuário/aprovador;
- data/hora;
- justificativa;
- competência de início de vigência.

Nunca reescrever retroativamente períodos anteriores sem aprovação.
