# Plano de implementação — refatoração visual e funcional

## Resultado esperado

Entregar a identidade **canteiro organizado** em todas as páginas, com
navegação responsiva, fluxos operacionais mais rápidos, formulários sob
demanda e feedback consistente, sem alterar contratos de API ou regras de
negócio existentes.

## Regras de execução

- Trabalhar em incrementos pequenos e manter os seletores usados pelo
  JavaScript até que marcação e comportamento sejam atualizados juntos.
- Rodar a suíte automatizada após cada etapa funcional.
- Não adicionar dependências remotas ou recursos que exijam internet.
- Usar JavaScript e CSS nativos, compatíveis com a arquitetura atual.
- Revisar visualmente desktop (1280 px), tablet (768 px) e a segurança do
  layout em 375 px.
- Não misturar mudanças de backend que não sejam necessárias para os fluxos
  aprovados.

## Etapa 1 — Fundação da interface

### Arquivos

- Modificar 'frontend/static/css/app.css'.
- Criar 'frontend/static/js/ui.js'.
- Criar 'frontend/static/img/icons.svg' somente se um sprite local reduzir
  repetição sem prejudicar acessibilidade.
- Modificar 'frontend/static/js/auth.js' para integrar dados do usuário à nova
  estrutura, sem mudar autenticação.

### Trabalho

1. Implementar os tokens de cor, tipografia, espaçamento, raio, sombra,
   largura e camadas definidos na especificação.
2. Criar estilos-base de foco, estado desabilitado, leitura por leitores de
   tela e 'prefers-reduced-motion'.
3. Criar a estrutura '.app-shell', cabeçalho, navegação lateral, conteúdo e
   navegação móvel.
4. Padronizar botões, campos, grupos de formulário, painéis, indicadores,
   tabelas, badges, alertas, modais, drawers, estados vazios e carregamento.
5. Implementar em 'ui.js' os comportamentos compartilhados de abertura e
   fechamento da navegação, modal/drawer, foco, Escape e notificações.
6. Garantir que os componentes possam ser usados sem JavaScript quando forem
   apenas estruturais.

### Verificação

- Conferir contraste dos tokens e foco visível.
- Conferir que controles essenciais têm 44 por 44 px no modo touch.
- Rodar 'pytest tests/test_auth.py -q'.

## Etapa 2 — Login e estrutura compartilhada

### Arquivos

- Modificar 'frontend/login.html'.
- Modificar 'frontend/index.html'.
- Modificar 'frontend/pdv.html'.
- Modificar 'frontend/operacao.html'.
- Modificar 'frontend/relatorios.html'.

### Trabalho

1. Aplicar a nova identidade ao login, removendo CSS embutido e mantendo os
   IDs 'login-form', 'email', 'password' e 'alert'.
2. Introduzir a estrutura compartilhada nas quatro páginas autenticadas.
3. Substituir emojis de navegação por ícones locais com rótulos acessíveis.
4. Marcar corretamente a página atual e permitir recolher ou abrir a
   navegação por teclado e toque.
5. Manter 'current-user-name' e 'logout-btn' compatíveis com 'auth.js'.
6. Remover estilos inline migrados para classes semânticas.

### Verificação

- Testar login correto, erro de credencial, logout e redirecionamento.
- Navegar por todas as páginas somente com teclado.
- Rodar 'pytest tests/test_auth.py -q'.

## Etapa 3 — Painel operacional

### Arquivos

- Modificar 'frontend/index.html'.
- Modificar 'frontend/static/css/app.css'.

### Trabalho

1. Criar um cabeçalho com saudação curta, contexto do depósito e ações
   rápidas para venda, cliente, produto e ajuste de saldo.
2. Transformar estoque baixo na principal fila de atenção, com quantidade,
   mínimo e ação contextual.
3. Reorganizar os módulos em grupos operacionais, sem uma coleção uniforme de
   cartões.
4. Criar estados de carregamento, vazio e falha para o estoque baixo.
5. Inserir dados de produtos de forma segura, evitando interpolação direta de
   conteúdo não confiável em 'innerHTML'.

### Verificação

- Validar o painel com zero, um e muitos produtos em estoque baixo.
- Rodar 'pytest tests/test_reports.py -q'.

## Etapa 4 — PDV rápido para teclado e toque

### Arquivos

- Modificar 'frontend/pdv.html'.
- Modificar 'frontend/static/css/app.css'.
- Usar 'frontend/static/js/ui.js' para comportamentos compartilhados.

### Trabalho

1. Reorganizar o PDV em busca/catálogo e resumo do carrinho lado a lado no
   desktop.
2. No tablet, oferecer carrinho em drawer com ação persistente, quantidade e
   total, sem ocultar o andamento da venda.
3. Transformar abertura e fechamento de caixa em estados claros da mesma
   área, substituindo o formulário de fechamento embutido por modal acessível.
4. Preservar a leitura por código de barras e o foco de retorno para a busca
   após adicionar um item.
5. Melhorar seleção de produto, unidade, quantidade e cliente sem acrescentar
   passos ao fluxo atual.
6. Oferecer remoção de item, resumo de pagamento, prevenção de envio duplicado
   e mensagens de validação no contexto correto.
7. Modernizar o modal de recibo preservando impressão térmica e A4.
8. Substituir interpolação insegura de resultados de produto e cliente nos
   trechos alterados.

### Verificação

- Executar manualmente abrir caixa, buscar produto, escanear SKU/código,
  alterar unidade e quantidade, selecionar cliente, vender e imprimir.
- Conferir falta de estoque e divergência no pagamento.
- Rodar 'pytest tests/test_pdv.py tests/test_product_image_and_lookup.py -q'.

## Etapa 5 — Estrutura e navegação de Operação

### Arquivos

- Modificar 'frontend/operacao.html'.
- Criar 'frontend/static/js/operacao.js' e mover para ele o script da página
  sem alterar a ordem de inicialização.
- Modificar 'frontend/static/css/app.css'.

### Trabalho

1. Converter as abas em navegação contextual responsiva com título, descrição
   e ação primária própria de cada módulo.
2. Preservar hashes ('#estoque', '#clientes', '#orcamentos', '#pedidos',
   '#compras', '#financeiro', '#entregas', '#auditoria') e histórico do
   navegador.
3. Extrair o JavaScript embutido para 'operacao.js', mantendo nomes e IDs
   inicialmente para reduzir risco.
4. Criar uma API local de configuração de módulo apenas para título,
   descrição, ação e função de recarga; não duplicar regras de domínio.
5. Padronizar cabeçalhos de listagem, busca, ações, estados vazios e tabelas.
6. Adaptar tabelas para rolagem controlada ou blocos no tablet conforme a
   quantidade e a importância das colunas.

### Verificação

- Abrir diretamente cada hash e usar voltar/avançar do navegador.
- Confirmar que cada função de carga é chamada somente quando necessário.
- Rodar a suíte completa 'pytest tests/ -q'.

## Etapa 6 — Formulários sob demanda em Operação

### Arquivos

- Modificar 'frontend/operacao.html'.
- Modificar 'frontend/static/js/operacao.js'.
- Modificar 'frontend/static/css/app.css'.

### Trabalho

1. Mover criação de endereço, produto e ajuste de saldo para drawers ou
   modais adequados ao tamanho do formulário.
2. Mover criação de cliente para drawer amplo, preservando busca e listagem.
3. Abrir orçamentos e pedidos em uma área dedicada sob demanda, mantendo os
   construtores de itens e autocomplete.
4. Reorganizar fornecedores e pedidos de compra, preservando recebimento
   parcial e atualização de saldo.
5. Substituir 'prompt()' da baixa financeira por modal com valor aberto,
   valor da baixa e forma de pagamento.
6. Reorganizar transportadora, veículo, motorista e agendamento em ações
   contextuais da logística.
7. Substituir 'prompt()' de ocorrência por modal com tipo e descrição.
8. Incluir validação junto ao campo, estado de envio, foco inicial e retorno
   do foco ao elemento acionador.
9. Preservar dados digitados quando ocorrer falha de rede ou validação.

### Verificação

- Testar cadastro, busca e exclusão segura de clientes.
- Testar orçamento até conversão, pedido até entrega e cancelamento.
- Testar compra, recebimento parcial/total e baixa financeira.
- Testar agendamento, avanço de entrega e ocorrência.
- Rodar 'pytest tests/test_customers_audit.py tests/test_quotes_orders.py tests/test_purchasing_finance.py tests/test_logistics.py -q'.

## Etapa 7 — Relatórios e acabamento transversal

### Arquivos

- Modificar 'frontend/relatorios.html'.
- Modificar 'frontend/static/css/app.css'.
- Modificar 'frontend/static/js/ui.js' se surgir comportamento genuinamente
  compartilhado.

### Trabalho

1. Levar filtro de período ao cabeçalho contextual e exibir claramente o
   intervalo aplicado.
2. Redesenhar os indicadores com hierarquia tipográfica, sem usar cartões
   idênticos como decoração.
3. Aplicar a paleta de marca aos gráficos e garantir rótulos compreensíveis.
4. Criar feedback para carregamento, ausência de dados e falha do relatório.
5. Revisar vocabulário, nomes das ações e mensagens em todas as páginas.
6. Remover CSS embutido e utilitários pontuais que tenham substituição
   semântica.

### Verificação

- Validar período com dados e sem dados.
- Rodar 'pytest tests/test_reports.py -q'.

## Etapa 8 — Auditoria final

### Trabalho

1. Rodar 'pytest tests/ -q' e corrigir regressões.
2. Procurar 'prompt(', estilos inline remanescentes, links sem estado ativo,
   imagens sem texto alternativo e controles sem rótulo.
3. Inspecionar todas as páginas em 1280 px, 768 px e 375 px.
4. Testar teclado: navegação, modais, drawers, Escape, foco e envio.
5. Testar 'prefers-reduced-motion' e zoom do navegador a 200%.
6. Conferir os principais fluxos com mouse e emulação de toque.
7. Revisar console do navegador e requisições com falha.
8. Atualizar 'README.md' apenas se a navegação ou operação descrita tiver sido
   materialmente alterada.

## Critério de conclusão

A refatoração estará concluída quando todas as páginas compartilharem a nova
identidade, os fluxos prioritários puderem ser executados com menos exposição
de formulários e sem diálogos nativos, a suíte automatizada estiver verde e a
auditoria responsiva e de acessibilidade não encontrar bloqueios operacionais.
