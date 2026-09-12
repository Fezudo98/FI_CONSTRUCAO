# Conversão para monodepósito

## Objetivo

Converter o sistema para uma única instalação por depósito, removendo a camada de empresa/filial. A instalação consulta uma VPS somente para validar a mensalidade e não compartilha dados operacionais com ela.

Os dados atuais são fictícios. A instalação pode recriar o banco local do zero.

## Modelo de dados

- Remover `Company`, `company_id` e as relações/FKs correspondentes.
- Manter usuários, papéis e permissões locais, agora sem vínculo a empresa.
- Produtos, estoque, clientes, caixa, vendas, pedidos, compras, financeiro, logística e auditoria pertencem diretamente ao depósito local.
- Simplificar índices e restrições que hoje incluem `company_id`.
- Tornar o código de barras único quando informado, impedindo leitura ambígua no PDV.
- Recriar a cadeia de migrações como esquema inicial monodepósito. O instalador inicial limpa e recria o banco explicitamente; o inicializador diário aplica apenas atualizações incrementais futuras.

## Aplicação e API

- Remover parâmetros `company_id` de serviços, filtros e serializações.
- Trocar consultas por ID para escopo direto do depósito, preservando a verificação de permissões por papel.
- Remover `company_id` da resposta de autenticação e da configuração de ambiente.
- Manter auditoria local com usuário, ação, detalhes e data.
- O PDV calcula o preço de cada item no servidor a partir do produto cadastrado. O valor recebido do navegador não define o total; futuras regras de desconto exigirão autorização explícita.
- A criação de veículos e motoristas valida a transportadora local antes de persistir o vínculo.

## Operação e licença

- `instalar_sistema` continua atualizando o repositório, preparando dependências e criando um banco local vazio no esquema monodepósito.
- `iniciar_sistema` continua atualizando o repositório, instalando dependências novas, aplicando migrações, consultando a licença e iniciando a aplicação.
- A VPS recebe somente a `LICENSE_KEY` para retornar `active` ou `suspended`; não recebe vendas, estoque, clientes nem dados de caixa.
- A última validação `active` é armazenada localmente por prazo configurável para tolerar indisponibilidade temporária da internet.
- O `.env` exige uma `SECRET_KEY` diferente do valor de exemplo antes de iniciar em produção.

## Interfaces

- Nenhuma tela exibirá empresa, filial ou seleção de empresa.
- A administração de usuários continua local, com os mesmos papéis atuais.
- Cadastro por câmera, PDV em tela cheia, leitor físico e atalhos permanecem inalterados na experiência do usuário.

## Erros e segurança

- Uma chave de licença ausente, inválida ou suspensa impede o início conforme a política já existente.
- O instalador não apaga dados sem uma confirmação explícita na execução; esta entrega usará essa confirmação para recriar o banco fictício.
- O inicializador diário nunca recria o banco.
- Falhas de atualização, migração ou licença interrompem a inicialização com uma mensagem clara.

## Verificação

- Atualizar testes de modelos, autenticação, catálogo, estoque, PDV, pedidos, compras, relatórios e auditoria para não dependerem de empresa.
- Adicionar testes para preço calculado no servidor, código de barras único e validação de vínculos logísticos.
- Executar a suíte completa em banco limpo e validar os scripts PowerShell por sintaxe.
