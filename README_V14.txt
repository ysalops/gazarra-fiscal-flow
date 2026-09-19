GAZARRA V14 — ACESSO POR PERFIL + BUSCA DE EMPRESAS + MICROINTERAÇÕES

Esta versão é um overlay para a pasta gazarra-poc atual.
Extraia o conteúdo deste ZIP diretamente em:
C:\Users\Ysa Martinho\Documents\gazarra-poc

O QUE MUDA

1. Dashboard / gráficos
- corrige as barras do gráfico de XML para partirem da mesma linha de base;
- adiciona animação de entrada das barras;
- adiciona desenho animado dos sparklines do Dashboard Fiscal;
- adiciona entrada suave de cards, painéis e linhas de tabelas;
- respeita prefers-reduced-motion.

2. Busca de empresas
- substitui o select visual gigante por pesquisa de empresa;
- campo separado de CNPJ;
- pesquisa por razão social ou CNPJ;
- sugestões aparecem em dropdown;
- endpoint /api/fiscal/companies aceita ?search=.

3. Autenticação e perfis
- login local da POC;
- perfis Admin e Analista;
- Admin vê todas as empresas;
- Analista só recebe as empresas atribuídas;
- autorização é validada também no backend (403 ao tentar acessar empresa sem permissão).

4. Administração
- nova tela Administração, visível só para Admin;
- lista de usuários;
- criação de usuário;
- atribuição/remoção de empresas por analista;
- pesquisa de empresa/CNPJ;
- trilha simples de auditoria de alterações de acesso.

5. Rodapé
- © 2026 GAZARRA · Desenvolvido por Ylume.dev.br

CONTAS DEMONSTRATIVAS LOCAIS

Administrador:
admin@gazarra.local
Gazarra@123

Analista:
analista@gazarra.local
Analista@123

O analista demonstrativo inicia apenas com acesso à empresa Alpha (ID 1).
O Admin pode atribuir Beta/Gamma pela tela Administração.

IMPORTANTE
Estas credenciais são SOMENTE para ambiente local/POC.
Antes de publicar, altere AUTH_SECRET e remova/troque as senhas demonstrativas.

VARIÁVEIS OPCIONAIS NO .env
AUTH_SECRET=uma-chave-longa-e-aleatoria
AUTH_TOKEN_HOURS=10
SEED_DEMO_USERS=true
DEMO_ADMIN_EMAIL=admin@gazarra.local
DEMO_ADMIN_PASSWORD=Gazarra@123
DEMO_ANALYST_EMAIL=analista@gazarra.local
DEMO_ANALYST_PASSWORD=Analista@123

INSTALAÇÃO

1. Faça backup do projeto atual.
2. Extraia o ZIP sobre a raiz gazarra-poc e aceite substituir os arquivos.
3. Rode:

docker compose build --no-cache backend frontend
docker compose up -d --force-recreate backend frontend
docker compose ps

4. Abra:
http://localhost:8080

5. Faça Ctrl + F5.

TESTE RECOMENDADO

A) Entre como Admin.
- Dashboard Fiscal deve permitir Alpha/Beta/Gamma.
- Pesquise empresa pelo nome e pelo CNPJ.
- Abra Administração.
- Selecione o Analista Demonstrativo.
- Marque/desmarque empresas e salve.

B) Saia e entre como Analista.
- Só as empresas atribuídas devem aparecer na pesquisa.
- Se tentar chamar manualmente uma empresa não permitida, a API retorna 403.

C) Teste Dashboard Fiscal, XML, Product Mapper, Revisão humana, Consulta ISS e GAZARRA IA.

NOTA TÉCNICA
A autenticação desta V14 foi feita para a POC local, com token assinado e hash PBKDF2 de senha usando apenas bibliotecas já disponíveis no projeto. Para produção, a camada pode ser substituída por um provedor de identidade/SSO sem alterar o modelo de segregação por empresa.
