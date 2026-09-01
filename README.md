# Raio X — Backend

Aplicação Next.js, API REST e banco PostgreSQL para substituir a planilha operacional de atendimentos. A documentação interativa fica disponível em `/docs` quando a API está em execução.

## Executar com Docker

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec api python -m scripts.bootstrap
```

API: `http://localhost:8000` · OpenAPI: `http://localhost:8000/docs`

Frontend: `http://localhost:3000`

Se o frontend usar outra porta, inclua a origem completa em `CORS_ORIGINS` no `.env`, separada por vírgula, e reinicie a API. Exemplo: `http://localhost:3001`.

O bootstrap cria `SPL`, os três coordenadores, a loja `EXCEL`, os motivos iniciais e o primeiro administrador:

```text
admin@raiox.local / TroqueEstaSenha123
```

Troque essa senha imediatamente e nunca use essa credencial fora do ambiente local.

## Importar lojas e consultores

O importador aceita cabeçalho e as colunas Consultor (A), Loja (B), Coordenador (C) e Gerente (D). Ele ignora linhas exatamente duplicadas e cria uma conta `OPERATOR` por loja, vinculada somente àquela loja. O login remove o código numérico e o sufixo `COMM`: por exemplo, `08 - MAUA - COMM` usa `maua` e a senha inicial `maua@321`.

```bash
docker cp "C:/caminho/arquivo.xlsx" felipevivo-api-1:/tmp/spl.xlsx
docker compose exec api python -m scripts.import_spl /tmp/spl.xlsx
```

Para importar o grupo do Sergio na regional SPC e criar o gerente em uma única execução:

```bash
docker compose exec api python -m scripts.migrate_manager_role
docker cp "C:/caminho/sergio-gerente.xlsx" felipevivo-api-1:/tmp/sergio.xlsx
docker compose exec api python -m scripts.import_spl /tmp/sergio.xlsx --regional SPC --manager-login sergio --manager-name "Sergio"
docker compose exec api python -m scripts.provision_manager felipe "Felipe" "HENRIQUE BRITO" "MARCUS PAULO" "MARISTELA RODRIGUES"
```

## Arquitetura e regras

- PostgreSQL mantém a fonte única de verdade; o dashboard agrega `attendances` e não persiste indicadores calculados.
- A integridade Regional → Coordenador → Loja → Consultor é validada antes de cada lançamento.
- `UNIQUE(store_id, date, password_number)` impede senhas duplicadas por loja e dia; a senha é informada manualmente no lançamento.
- Uma conta vinculada a apenas uma loja recebe Regional, Coordenador e Loja já selecionados na entrada de dados; apenas o consultor permanece selecionável.
- Cada criação, alteração e exclusão de atendimento gera um item em `audit_logs` com usuário e estado anterior/posterior.
- Perfis: `ADMIN` tem acesso total; `MANAGER` administra lojas, operadores e consultores de suas coordenadoras; `COORDINATOR` é limitado aos coordenadores vinculados; `OPERATOR`, às lojas vinculadas.
- A fórmula de “Disponibilidade Real” está centralizada em `app/services.py::availability_real`; a regra inicial é `disponível para venda / senhas`.

## Endpoints principais

Use `POST /api/auth/login` para obter um Bearer token. A API inclui catálogos dependentes em `/api/catalog/*`, lançamentos em `/api/attendances`, consolidado em `/api/dashboard/consolidated`, detalhamento por consultor, exportação Excel e administração em `/api/admin/*`.

Os filtros de período usam `start_date` e `end_date` no formato `YYYY-MM-DD`. CPF/CNPJ é armazenado como texto para preservar zeros à esquerda.

## Desenvolvimento do frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Use `npm run lint` e `npm run build` antes de entregar alterações. O frontend usa Next.js 16, TypeScript, Recharts e Lucide; os tokens e padrões visuais estão em `design-system/MASTER.md`.
