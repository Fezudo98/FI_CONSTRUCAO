# F.I Construção — Sistema de Gestão e PDV

Sistema interno para depósito de materiais de construção: PDV, estoque por
endereço/lote, orçamentos e pedidos, compras e fornecedores, financeiro e
logística de entrega e permissões locais por papel para um único depósito.

**Importante:** este sistema roda **localmente**, no computador do próprio
depósito — não é hospedado na nuvem. Um PC atua como servidor (aplicação +
banco de dados); os demais computadores do depósito acessam pela rede local,
apenas com um navegador.

## Estado atual da implementação

Alguns módulos foram adaptados do **PUMA Commerce Core** (base interna de
e-commerce/PDV da Puma Systems), simplificados para o contexto de um depósito
B2B/balcão (sem loja virtual, cupons ou integrações de pagamento online).

✅ **Pronto e testado** (36 testes automatizados, todos os fluxos validados no
navegador de ponta a ponta):
- Autenticação (login/logout por sessão), papéis e permissões.
- Catálogo de produtos com conversão de unidades (ex.: 1 pallet = 40 unidades).
- Estoque por endereço/lote, saldo disponível vs. reservado, ajustes manuais.
- PDV completo: abertura/fechamento de caixa, venda com múltiplos itens e
  unidades, baixa automática de estoque, validação de pagamento.
- Orçamentos: criação, envio, aprovação/rejeição, conversão em pedido
  (reservando estoque automaticamente).
- Pedidos: criação direta ou via orçamento, fluxo reservado → separado →
  retirado → (entregue, se for entrega), cancelamento com liberação de reserva.
- Compras: fornecedores, pedidos de compra, recebimento parcial ou total —
  atualiza custo médio ponderado do produto, dá entrada no estoque e gera
  conta a pagar automaticamente.
- Financeiro: contas a pagar com baixa total ou parcial.
- Logística: transportadoras, veículos, motoristas, agendamento de entrega,
  fluxo agendado → em rota → concluída (marca o pedido como entregue
  automaticamente), registro de ocorrências.
- Modelo de dados monodepósito com permissões locais por papel.
- **Clientes (CRM)**: cadastro com endereço, busca rápida (usada no PDV,
  orçamentos e pedidos), exclusão segura — apaga de verdade só quem nunca
  teve movimento; quem já comprou é apenas inativado, preservando o histórico.
- **Alertas de estoque baixo**: `min_stock` por produto, card no Painel e
  endpoint dedicado (`/api/reports/low-stock`).
- **Recibo de venda**: modal de impressão no PDV após cada venda, com dois
  formatos — bobina térmica 74mm e A4 — via CSS `@media print`.
- **Relatórios** (`/relatorios.html`): receita, ticket médio, lucro bruto,
  gráfico de vendas no período, ranking de produtos e formas de pagamento
  (Chart.js servido localmente — funciona sem internet).
- **Auditoria**: log das ações sensíveis (venda registrada, caixa
  aberto/fechado, produto criado, estoque ajustado, cliente criado/editado),
  consultável em Operação → Auditoria (admin).
- **Código de barras**: geração sob demanda (Code128/SVG) a partir do SKU, ou
  cadastro do código já impresso pelo fabricante.
- **Imagem por produto**: upload (JPG/PNG/WEBP, até 5MB) exibida no cadastro
  e no PDV ao selecionar o item.
- **Leitor de código de barras**: funciona por ser HID (o leitor "digita" o
  código + Enter, como um teclado — não precisa de driver). No PDV, escanear
  e apertar Enter adiciona 1 unidade direto no carrinho. No ajuste de
  estoque, escanear seleciona o produto automaticamente e foca o campo de
  quantidade, para gravação rápida de saldo.
- **Maquininha de cartão (registro manual)**: ao escolher "Cartão débito" ou
  "Cartão crédito" no PDV, aparece um campo opcional para o código
  NSU/autorização impresso pela maquininha, salvo junto ao pagamento e
  exibido no recibo — útil para conferência de caixa. Ainda não há
  integração eletrônica com nenhuma operadora específica (Stone, PagBank,
  GetNet etc.); isso depende de saber qual maquininha/operadora o cliente
  usa e se ela oferece API/SDK de integração.

🚧 **Pendente** (fora do escopo desta entrega):
- Cotações formais de compra com múltiplos fornecedores (`SupplierOffer`) —
  modelo de dados já existe, mas o pedido de compra hoje é criado direto com
  um fornecedor já escolhido.
- Algumas ações administrativas de baixa frequência (baixar conta a pagar,
  registrar ocorrência de entrega) usam caixas de diálogo nativas do
  navegador (`prompt()`) em vez de formulário embutido na página — funcional,
  mas menos refinado visualmente que o resto da interface.

## Instalação no computador do depósito (PC-servidor)

O PC-servidor precisa do **Instalador de Aplicativo/winget**, presente nas
versões atuais do Windows 10 e 11. Git, Python 3.12 e PostgreSQL são instalados
automaticamente quando estiverem ausentes.

1. Entregue somente o arquivo `instalar_sistema.bat` à cliente, por exemplo na
   Área de Trabalho, e execute-o com duplo clique. Ele baixa o instalador oficial
   do GitHub, solicita permissão de administrador e clona o sistema em
   `C:\ProgramData\FIConstrucao`. Quando executado dentro de uma cópia Git
   existente, utiliza o `instalar_sistema.ps1` local e atualiza essa cópia.
2. Informe a chave de licença e crie a senha do primeiro administrador quando
   solicitado. A chave secreta da aplicação, o banco PostgreSQL, o usuário do
   banco, as ferramentas de backup, as permissões da pasta, a regra de firewall,
   os atalhos e o backup diário das 22h são configurados automaticamente.
3. Nas próximas vezes, é só rodar `iniciar_sistema.bat` — ele busca e aplica
   atualizações do repositório, instala dependências novas se existirem,
   cria um backup, aplica migrações pendentes, verifica a licença e inicia o servidor,
   abrindo o navegador automaticamente. Para proteger os dados, ele para se
   detectar alterações locais não versionadas. Em produção o servidor é o
   **Waitress** (WSGI de verdade, multi-thread), não o servidor de
   desenvolvimento do Flask.

Reexecutar o instalador preserva `.env`, usuários e banco. Antes de qualquer
migração em uma instalação existente, ele exige que o backup seja concluído.

## Backup e restauração

O backup é do banco PostgreSQL, não da pasta do sistema — os arquivos de
código são recuperáveis pelo Git, os dados não.

- **Agendar backup diário** (uma vez, após a instalação): `agendar_backup.bat`
  — pergunta o horário e registra uma tarefa no Agendador de Tarefas do
  Windows. Pode pedir para rodar como Administrador.
- **Backup manual, a qualquer momento**: `backup_agora.bat`.
- Os arquivos ficam em `backups/` (fora do Git), formato `.dump` do
  `pg_dump`, com um backup por dia — mantidos por `BACKUP_RETENTION_DAYS`
  dias (padrão 14; ajustável no `.env`).
- O instalador localiza `pg_dump`/`pg_restore` mesmo quando não estiverem no
  PATH e grava os caminhos no `.env`. Em uma configuração manual, os campos
  `PG_DUMP_PATH`/`PG_RESTORE_PATH` continuam disponíveis.
- **Restaurar um backup** (substitui os dados atuais — peça confirmação
  antes de rodar, isso é irreversível):
  ```
  .venv\Scripts\python.exe scripts\restore_database.py backups\fi_construcao_20260101_220000.dump
  ```
- Recomenda-se copiar periodicamente os arquivos de `backups/` para fora do
  PC-servidor (pendrive, nuvem, outro computador) — um backup que mora no
  mesmo disco que pode falhar não protege contra falha de disco.

## Acesso pelos outros computadores do depósito

Nenhuma instalação é necessária. Basta abrir o navegador e acessar:
```
http://<IP-do-PC-servidor-na-rede-local>:5000
```
Para descobrir o IP do PC-servidor na rede local, rode `ipconfig` nele e
procure o "Endereço IPv4" da rede local (Wi-Fi ou cabo).

## Desenvolvimento local

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
copy .env.example .env
# edite .env — para dev rápido, DATABASE_URL=sqlite:///fi_construcao.db funciona
.venv\Scripts\python -m flask db upgrade
.venv\Scripts\python create_dev_admin.py
.venv\Scripts\python run.py
```
Acesse `http://localhost:5000`.

### Testes
```bash
.venv\Scripts\python -m pytest tests/ -v
```

## Licenciamento (mensalidade)

O script `scripts/check_license.py`, chamado automaticamente por
`iniciar_sistema.bat`, contata `LICENSE_CHECK_URL` (configurável no `.env`)
enviando `LICENSE_KEY` e espera `{"status": "active" | "suspended"}`. O
resultado fica em cache local (`license_cache.json`, fora do git) por até
`LICENSE_GRACE_DAYS` dias (padrão 7), para o sistema continuar funcionando
se a internet do depósito cair temporariamente.

Se `LICENSE_CHECK_URL`/`LICENSE_KEY` não estiverem configurados, ou a chave
for inválida/suspensa, a inicialização **bloqueia por segurança** — não é
possível rodar o sistema em produção sem uma licença ativa.

O endpoint já está no ar, dentro do painel Puma existente na VPS
(`admin/app.py`, rota pública `GET /api/licenses/check?key=...`, em
`https://vps69719.publiccloud.com.br/puma/servidores/api/licenses/check`).
Licenças são geradas e suspensas na própria tela do painel
(seção "Instalações locais licenciadas"), independente dos clientes
hospedados em container — o endpoint recebe só a `LICENSE_KEY` e devolve
`active`/`suspended`, sem acesso a vendas, estoque, clientes ou caixa.

## Estrutura principal

```text
app/models/            modelos de dados por domínio (user, catalog,
                        inventory, sales, purchasing, finance, logistics)
app/services/          regras de negócio (pdv, inventory, units, auth,
                        permissions)
app/routes/api/        API REST usada pelo frontend
app/routes/web.py      serve as páginas do frontend
frontend/index.html    painel executivo (módulos)
frontend/login.html    tela de login
frontend/pdv.html      frente de caixa
frontend/operacao.html retaguarda: estoque, clientes, orçamentos, pedidos,
                        compras, financeiro, entregas e auditoria
frontend/relatorios.html vendas, ranking de produtos e formas de pagamento
migrations/            evolução versionada do banco (Alembic)
scripts/                bootstrap_database.py, check_license.py,
                        backup_database.py, restore_database.py,
                        agendar_backup.ps1
instalar_sistema.bat   instalação inicial (update + dependências + banco)
iniciar_sistema.bat    inicialização diária (update + migrações + licença)
atualizar.bat          só atualiza (git pull + migrações), sem iniciar
agendar_backup.bat     agenda o backup diário do banco (Agendador de Tarefas)
backup_agora.bat       roda um backup do banco na hora
```

## Segurança

- `.env`, banco local e `license_cache.json` nunca são versionados.
- Senhas com hash bcrypt; sessão via cookie assinado (`SECRET_KEY`).
- Permissões por papel (admin/manager/cashier/stock), com exceções por
  usuário via `UserPermissionOverride`.
- **Repositório GitHub hoje é público.** Para um produto comercial com lógica
  de licenciamento no código, recomenda-se torná-lo privado.
