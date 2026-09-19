# GAZARRA — Agentes Reconstruídos v1

Primeiro lote reconstruído a partir do pacote adquirido de 57 agentes. Esta versão prioriza segurança, atualização legal, rastreabilidade e revisão humana.

## Arquivos
- `00-governanca-e-seguranca.md` — regras comuns a todos os agentes.
- `01-agente-fiscal-gazarra.md` — núcleo fiscal e roteador de análises.
- `02-agente-cadastro-tributario-produtos.md` — classificação e conferência cadastral de produtos.
- `03-agente-revisao-sped-gazarra.md` — revisão EFD ICMS/IPI e EFD-Contribuições.
- `04-agente-reforma-tributaria-cbs-ibs.md` — análise da Reforma Tributária com base 2026.
- `05-agente-conferencia-guias.md` — conferência de guias sem emissão/pagamento automático.
- `CHANGELOG.md` — o que foi corrigido em relação ao pacote original.

## Princípios
1. Nenhum agente presume legislação congelada como atual.
2. Toda conclusão tributária relevante deve indicar fonte, período e jurisdição.
3. Sem fonte oficial suficiente, a saída é `PENDENTE DE VALIDAÇÃO`.
4. Nenhum agente paga guia, transmite obrigação, altera ERP ou cadastro definitivo sem aprovação humana explícita.
5. Agentes analíticos operam, por padrão, com leitura; escrita/execução é exceção.
6. Cálculos devem expor memória de cálculo e premissas.
7. Classificação por NCM/CEST/CST/CFOP não deve ser inferida apenas pela descrição comercial.

## Status
Lote 1 concluído. Próximos lotes sugeridos: Folha/eSocial/INSS/IRRF/FGTS Digital; DCTFWeb/MIT/EFD-Reinf; Contábil/Conciliações; Societário/Atendimento.
