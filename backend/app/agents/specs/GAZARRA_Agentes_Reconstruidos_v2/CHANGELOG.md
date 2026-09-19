# Changelog v2

- `06-dctfweb-mit`: reconstruído de `08-dctfweb`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.
- `07-efd-reinf`: reconstruído de `09-efd-reinf`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.
- `08-esocial`: reconstruído de `10-esocial`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.
- `09-holerite`: reconstruído de `11-holerite`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.
- `10-ferias-13`: reconstruído de `12-ferias-13-salario`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.
- `11-rescisao`: reconstruído de `13-rescisao-clt-calculo`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.
- `12-inss`: reconstruído de `14-inss-fgts`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.
- `13-irrf`: reconstruído de `30-calculo-irrf-folha`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.
- `14-fgts-digital`: reconstruído de `14-inss-fgts`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.
- `15-folha-mensal`: reconstruído de `35-folha-pagamento-mensal`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.
- `16-admissao`: reconstruído de `15-admissao`; removidas tabelas congeladas como autoridade, reduzidas permissões e adicionados controles de fonte, competência, conciliação e aprovação.

## Correções estruturais
- INSS e FGTS separados.
- Referências entre agentes usam nomes existentes neste pacote.
- DCTFWeb/MIT e EFD-Reinf tratados como fontes integradas, não obrigações isoladas.
- IRRF 2026 exige verificação da redução legal; não reutiliza desconto simplificado antigo.
- eSocial consulta versão efetivamente vigente, sem aplicar antecipadamente leiautes futuros.
- Todos os cálculos permanecem sujeitos à homologação.
