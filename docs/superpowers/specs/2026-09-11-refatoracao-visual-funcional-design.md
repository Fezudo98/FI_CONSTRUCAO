# Refatoração visual e funcional — F.I Construção

## Objetivo

Modernizar integralmente a identidade visual do sistema e agilizar a operação
diária no balcão e no estoque, preservando as APIs e as regras de negócio já
validadas. A interface deve funcionar bem tanto em computadores com mouse e
teclado quanto em tablets com interação por toque.

## Direção de design

A identidade seguirá o conceito **canteiro organizado**: estrutura visual
robusta, linguagem direta e alta legibilidade, inspiradas na operação de um
depósito de materiais de construção. O azul continuará garantindo o
reconhecimento da marca; o laranja será reservado para ações importantes e
estados que exigem atenção.

### Tokens principais

- Azul estrutural: `#123B5D`.
- Azul escuro: `#0A263B`.
- Laranja de ação: `#F28C28`.
- Concreto claro: `#F2F4F3`.
- Branco: `#FFFFFF`.
- Grafite: `#24313A`.
- Cores semânticas adicionais deverão atender a contraste WCAG AA e nunca
  comunicar um estado apenas pela cor.

A tipografia será uma família sem serifa robusta e legível, disponível
localmente ou pela pilha de fontes do sistema. O sistema não dependerá de
internet para carregar fontes, ícones ou recursos essenciais.

Os componentes usarão cantos moderados, bordas firmes e sombras discretas.
Ícones vetoriais consistentes substituirão os emojis usados como elementos de
navegação. Controles essenciais terão área interativa mínima de 44 por 44 px.

## Arquitetura da interface

As páginas Painel, PDV, Operação e Relatórios compartilharão uma estrutura de
aplicação composta por:

- cabeçalho compacto com identidade, contexto do usuário e saída;
- navegação lateral recolhível no desktop;
- painel de navegação deslizante no tablet;
- cabeçalho contextual da página, com título, resumo e ações primárias;
- área principal responsiva, sem largura artificialmente limitada em telas de
  trabalho maiores;
- sistema comum de botões, campos, tabelas, painéis, modais, notificações,
  indicadores e estados vazios.

O CSS será separado conceitualmente em tokens, base, estrutura, componentes,
utilitários estritamente necessários e regras responsivas. Estilos embutidos
nos arquivos HTML serão migrados para classes semânticas. JavaScript
compartilhado cuidará apenas do comportamento comum da interface; regras de
domínio continuarão nos fluxos já existentes e no backend.

A página Operação continuará reunindo seus módulos atuais, evitando uma
alteração desnecessária nas rotas e no backend. Sua navegação interna será
reorganizada para oferecer contexto claro e acesso rápido, sem manter todos os
formulários de criação expostos ao mesmo tempo.

## Fluxos principais

### Painel

O Painel será orientado ao trabalho atual. Além dos acessos aos módulos, ele
mostrará somente informações disponíveis nas APIs existentes durante a
primeira etapa, começando pelo estoque crítico. Indicadores adicionais, como
pedidos aguardando separação e entregas do dia, só serão incluídos quando
puderem ser derivados com segurança dos endpoints existentes ou forem
explicitamente adicionados ao plano de backend.

Atalhos destacados permitirão iniciar venda, cadastrar cliente, cadastrar
produto e ajustar saldo. O conteúdo será priorizado por urgência operacional,
não por uma grade uniforme de cartões.

### PDV

Busca ou leitura de produto, carrinho e fechamento formarão uma área de
trabalho única. No desktop, catálogo e carrinho ficarão lado a lado. Em telas
menores, o carrinho será um painel acessível por uma ação persistente que
exibe quantidade de itens e total.

O leitor de código de barras manterá o comportamento atual: a leitura exata
seguida de Enter adiciona o item sem etapas extras. Fluxos frequentes deverão
funcionar por teclado; os controles também terão tamanho adequado para toque.

### Operação

Cada módulo abrirá pela listagem e pelos dados mais úteis para decisão. Ações
de criação ou edição serão abertas sob demanda em painel lateral ou modal,
conforme a complexidade do formulário. Formulários extensos poderão usar
seções internas, mas não serão transformados em assistentes de várias etapas
sem necessidade operacional.

Ações frequentes permanecerão visíveis. Ações destrutivas e ações de baixa
frequência ficarão em menus contextuais e exigirão confirmação explícita. As
caixas nativas `prompt()` usadas em tarefas administrativas serão substituídas
por formulários integrados, com validação e contexto da operação.

### Relatórios

Filtros e período ficarão próximos ao título e permanecerão fáceis de alterar.
Indicadores terão hierarquia tipográfica clara, e gráficos compartilharão a
nova paleta. Tabelas ou mensagens de ausência de dados deverão orientar o
usuário sem apresentar áreas vazias ou silenciosas.

### Login

O login refletirá a mesma identidade do restante do produto, mantendo o fluxo
simples, rápido e acessível. Mensagens de erro indicarão o problema e a ação
possível sem expor informações sensíveis.

## Estados, erros e feedback

- Notificações globais serão consistentes e não interromperão a operação.
- Erros de preenchimento serão exibidos junto ao campo relevante.
- Ações assíncronas terão estado de carregamento e proteção contra envio
  duplicado.
- Listagens terão estados explícitos de carregamento, vazio e falha.
- Confirmações usarão o mesmo verbo da ação iniciada.
- O foco será movido de forma previsível ao abrir e fechar painéis ou modais.
- Falhas de rede preservarão os dados digitados sempre que possível.

## Responsividade e acessibilidade

O desktop privilegiará densidade e comparação de dados. O tablet reorganizará
colunas, navegação e ações sem apenas reduzir toda a interface. Tabelas
permanecerão compactas no desktop e poderão usar rolagem controlada ou uma
representação em blocos no tablet quando isso preservar melhor a compreensão.

Todos os fluxos essenciais devem oferecer foco visível, ordem lógica de
tabulação, rótulos associados aos controles, contraste WCAG AA, mensagens que
não dependam apenas de cor e suporte a `prefers-reduced-motion`. O layout será
validado inicialmente nas larguras de 1280 px e 768 px, além de uma verificação
de segurança em 375 px para impedir quebra grave em celulares.

## Compatibilidade e dados

Os contratos HTTP, permissões, autenticação, modelos e regras de negócio
existentes serão preservados por padrão. Mudanças de endpoint só poderão ser
introduzidas quando necessárias para um indicador ou fluxo aprovado e deverão
ter cobertura automatizada própria.

Dados vindos da API deverão ser inseridos na interface de forma segura, sem
ampliar o uso atual de HTML construído diretamente a partir de valores não
confiáveis. A refatoração deverá preferir criação de nós ou escape explícito
nos pontos alterados.

## Estratégia de implementação

A execução será incremental para manter o sistema utilizável:

1. fundação visual, estrutura compartilhada e componentes básicos;
2. login e Painel;
3. PDV e seus fluxos de teclado/toque;
4. navegação e módulos da página Operação;
5. Relatórios, estados e acabamento transversal;
6. auditoria visual, responsiva, funcional e de acessibilidade.

Cada etapa deverá preservar os seletores e contratos necessários aos scripts
existentes ou atualizar marcação e comportamento em conjunto.

## Verificação e critérios de aceite

- A suíte automatizada atual permanece verde.
- Login, logout e proteção de sessão continuam funcionando.
- O PDV permite abrir caixa, localizar ou escanear produto, adicionar item,
  selecionar cliente, concluir venda, imprimir recibo e fechar caixa.
- Estoque, clientes, orçamentos, pedidos, compras, financeiro, entregas e
  auditoria continuam acessíveis e operáveis.
- Criações, edições, confirmações e erros não usam `prompt()` nos fluxos
  refatorados.
- Não há dependência de internet para recursos essenciais da interface.
- Login, Painel, PDV, Operação e Relatórios são inspecionados visualmente em
  1280 px e 768 px; 375 px não apresenta quebra grave ou ação inacessível.
- A navegação essencial funciona por teclado e os alvos de toque essenciais
  têm pelo menos 44 por 44 px.
- A identidade é reconhecível como F.I Construção sem reproduzir rigidamente a
  paleta anterior.

## Fora do escopo

- Alterar regras comerciais, estoque, pagamentos, licenciamento ou permissões.
- Criar um novo frontend baseado em framework sem necessidade comprovada.
- Adicionar recursos que dependam permanentemente de internet.
- Reestruturar banco de dados ou dividir a página Operação em novas rotas
  apenas por preferência estética.
