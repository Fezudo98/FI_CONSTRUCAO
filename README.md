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
- Endpoint de licenciamento na VPS (o script `check_license.py` já existe e
  funciona, mas hoje não bloqueia nada porque o endpoint ainda não foi criado
  no lado do servidor — ver seção "Licenciamento" abaixo).
- Cotações formais de compra com múltiplos fornecedores (`SupplierOffer`) —
  modelo de dados já existe, mas o pedido de compra hoje é criado direto com
  um fornecedor já escolhido.
- Algumas ações administrativas de baixa frequência (baixar conta a pagar,
  registrar ocorrência de entrega) usam caixas de diálogo nativas do
  navegador (`prompt()`) em vez de formulário embutido na página — funcional,
  mas menos refinado visualmente que o resto da interface.

## Instalação no computador do depósito (PC-servidor)

Requisitos: **Python 3.11+** e **PostgreSQL** instalados na máquina que vai
atuar como servidor (as demais máquinas do depósito não precisam de nada além
de um navegador).

1. Clone este repositório no PC-servidor.
2. Copie `.env.example` para `.env` e preencha:
   - `SECRET_KEY`: uma string aleatória longa.
   - `DATABASE_URL`: string de conexão do PostgreSQL local (crie o banco e o
     usuário antes, ex.: `createdb fi_construcao`).
   - `CORS_ORIGINS`: os IPs dos outros PCs do depósito na rede local, se forem
     acessar via IP direto (ex.: `http://192.168.0.10:5000`).
   - `DEV_ADMIN_EMAIL` / `DEV_ADMIN_PASSWORD`: credenciais do primeiro usuário.
3. Rode `instalar_sistema.bat` (duplo clique). Ele busca atualizações,
   prepara o Python, instala as dependências, abre o `.env` para configuração
   e cria a estrutura inicial do banco.
4. Rode uma vez, manualmente, a criação do administrador:
   ```
   .venv\Scripts\python.exe create_dev_admin.py
   ```
5. Nas próximas vezes, é só rodar `iniciar_sistema.bat` — ele busca e aplica
   atualizações do repositório, instala dependências novas se existirem,
   aplica migrações pendentes, verifica a licença e inicia o servidor,
   abrindo o navegador automaticamente. Para proteger os dados, ele para se
   detectar alterações locais não versionadas.

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

Enquanto `LICENSE_CHECK_URL`/`LICENSE_KEY` não estiverem configurados, a
verificação é **pulada** (não bloqueia nada) — isso é intencional, para
permitir usar o sistema antes do endpoint de licenciamento existir na VPS.
Esse endpoint ainda precisa ser construído (ver plano de implementação),
integrado aos scripts `suspend-client.sh`/`resume-client.sh` da plataforma
Puma já existente na VPS.

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
scripts/                bootstrap_database.py, check_license.py
instalar_sistema.bat   instalação inicial (update + dependências + banco)
iniciar_sistema.bat    inicialização diária (update + migrações + licença)
atualizar.bat          só atualiza (git pull + migrações), sem iniciar
```

## Segurança

- `.env`, banco local e `license_cache.json` nunca são versionados.
- Senhas com hash bcrypt; sessão via cookie assinado (`SECRET_KEY`).
- Permissões por papel (admin/manager/cashier/stock), com exceções por
  usuário via `UserPermissionOverride`.
- **Repositório GitHub hoje é público.** Para um produto comercial com lógica
  de licenciamento no código, recomenda-se torná-lo privado.
