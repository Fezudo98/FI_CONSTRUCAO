(function () {
  const steps = [
    {
      label: 'Comece aqui',
      title: 'Bem-vindo ao seu depósito organizado.',
      description: 'O sistema acompanha a rotina desde a leitura do produto até o fechamento e os relatórios. Este guia leva menos de dois minutos.',
      tips: ['Use o Painel para saber o que pede atenção.', 'As quatro áreas principais ficam sempre no menu.', 'No celular, o menu abre pelo botão no alto da tela.'],
      demo: 'map'
    },
    {
      label: 'Venda no balcão',
      title: 'No PDV, o leitor faz o trabalho rápido.',
      description: 'Abra o caixa, leia o código de barras e o produto entra no carrinho automaticamente. Confira o total e finalize com a forma de pagamento.',
      tips: ['Não precisa apertar Enter depois da leitura.', 'F2 volta o foco para a busca e F6 finaliza.', 'Dinheiro, Pix e cartão ficam registrados no caixa.'],
      demo: 'pdv',
      href: '/pdv.html',
      action: 'Abrir o PDV'
    },
    {
      label: 'Cadastre produtos',
      title: 'Use o celular para cadastrar o estoque.',
      description: 'Abra o sistema pelo endereço mostrado na inicialização. Em Operação, use a câmera para ler o código que já existe na embalagem.',
      tips: ['O código de barras identifica o produto; preço e tributação são cadastrados à parte.', 'Informe descrição, unidade, preço e estoque mínimo.', 'Cada código pode pertencer a somente um produto.'],
      demo: 'mobile',
      href: '/operacao.html#estoque',
      action: 'Ir para produtos'
    },
    {
      label: 'Controle materiais',
      title: 'Toda entrada ou saída deixa um rastro.',
      description: 'Compras alimentam o estoque. Vendas dão baixa. Ajustes manuais servem para corrigir contagens e sempre ficam registrados.',
      tips: ['Cadastre o fornecedor antes da compra.', 'Confirme o recebimento para aumentar o saldo.', 'Consulte os itens abaixo do mínimo no Painel.'],
      demo: 'stock',
      href: '/operacao.html#compras',
      action: 'Ver compras e estoque'
    },
    {
      label: 'Feche o dia',
      title: 'Termine o expediente com tudo conferido.',
      description: 'Feche o caixa, confira os pagamentos e acompanhe vendas e produtos nos Relatórios. O backup diário é feito automaticamente.',
      tips: ['Feche o caixa informando o valor contado.', 'Use o período dos relatórios para conferir o movimento.', 'Mantenha a janela do sistema aberta durante o uso.'],
      demo: 'report',
      href: '/relatorios.html',
      action: 'Conhecer os relatórios'
    }
  ];

  const overlay = document.getElementById('onboarding-overlay');
  if (!overlay) return;
  const title = document.getElementById('onboarding-title');
  const description = document.getElementById('onboarding-description');
  const tips = document.getElementById('onboarding-tips');
  const demo = document.getElementById('onboarding-demo');
  const counter = document.getElementById('onboarding-counter');
  const progress = document.getElementById('onboarding-progress');
  const back = document.getElementById('onboarding-back');
  const next = document.getElementById('onboarding-next');
  const skip = document.getElementById('onboarding-skip');
  const help = document.getElementById('onboarding-help');
  let current = 0;
  let returnFocus = null;

  function demoMarkup(type) {
    if (type === 'pdv') return '<div class="tour-pdv"><div class="tour-screen-head">CAIXA LIVRE</div><div class="tour-scan"><i></i><span>7891234567890</span></div><div class="tour-item"><b>Cimento CP II 50 kg</b><span>1 × R$ 39,90</span></div><div class="tour-total"><small>TOTAL</small><strong>R$ 39,90</strong></div></div>';
    if (type === 'mobile') return '<div class="tour-phone"><div class="tour-phone-top"></div><div class="tour-camera"><span></span><b>Enquadre o código</b></div><div class="tour-form-line wide"></div><div class="tour-form-line"></div><button tabindex="-1">Cadastrar produto</button></div>';
    if (type === 'stock') return '<div class="tour-flow"><div><b>Compra recebida</b><span>+ materiais</span></div><i>›</i><div class="active"><b>Estoque</b><span>saldo atualizado</span></div><i>›</i><div><b>Venda</b><span>− materiais</span></div></div>';
    if (type === 'report') return '<div class="tour-report"><div class="tour-report-head"><span>Movimento do dia</span><b>Hoje</b></div><div class="tour-bars"><i style="height:38%"></i><i style="height:62%"></i><i style="height:48%"></i><i style="height:82%"></i><i style="height:70%"></i><i style="height:94%"></i></div><div class="tour-report-result"><span>Vendas conferidas</span><strong>✓</strong></div></div>';
    return '<div class="tour-map"><div class="tour-map-brand"><img src="/static/img/logo.jpg" alt=""><span>F.I Construção</span></div><div class="tour-map-grid"><span>PAINEL</span><span>PDV</span><span>OPERAÇÃO</span><span>RELATÓRIOS</span></div></div>';
  }

  function render() {
    const step = steps[current];
    counter.textContent = `${current + 1} de ${steps.length}`;
    title.textContent = step.title;
    description.textContent = step.description;
    tips.replaceChildren(...step.tips.map(text => {
      const item = document.createElement('li');
      item.textContent = text;
      return item;
    }));
    demo.innerHTML = demoMarkup(step.demo);
    if (step.href) {
      const link = document.createElement('a');
      link.href = step.href;
      link.className = 'onboarding-destination';
      link.textContent = step.action;
      link.addEventListener('click', async event => {
        event.preventDefault();
        await complete();
        window.location.href = step.href;
      });
      demo.appendChild(link);
    }
    progress.querySelectorAll('li').forEach((item, index) => {
      item.classList.toggle('active', index === current);
      item.classList.toggle('done', index < current);
      if (index === current) item.setAttribute('aria-current', 'step');
      else item.removeAttribute('aria-current');
    });
    back.hidden = current === 0;
    next.textContent = current === steps.length - 1 ? 'Começar a usar' : 'Continuar';
    title.focus?.();
  }

  async function complete() {
    try {
      const response = await fetch('/api/auth/onboarding/complete', { method: 'POST' });
      if (!response.ok) throw new Error();
      return true;
    } catch (_) {
      // Falha ao salvar não deve travar o usuário no tour: sem confirmação
      // no servidor, o guia volta a aparecer no próximo login.
      return false;
    }
  }

  function openTour() {
    returnFocus = document.activeElement;
    current = 0;
    overlay.hidden = false;
    document.body.classList.add('dialog-open');
    render();
    skip.focus();
  }

  function closeTour() {
    overlay.hidden = true;
    document.body.classList.remove('dialog-open');
    if (returnFocus?.focus) returnFocus.focus();
  }

  function skipTour() {
    closeTour();
    complete();
  }

  progress.replaceChildren(...steps.map((step, index) => {
    const item = document.createElement('li');
    item.innerHTML = `<span>${index + 1}</span><b>${step.label}</b>`;
    return item;
  }));
  back.addEventListener('click', () => { if (current > 0) { current--; render(); } });
  next.addEventListener('click', () => {
    if (current < steps.length - 1) { current++; render(); return; }
    closeTour();
    complete();
  });
  skip.addEventListener('click', skipTour);
  help?.addEventListener('click', openTour);
  document.addEventListener('fi:user-ready', event => {
    const requested = new URLSearchParams(window.location.search).get('tour') === '1';
    if (requested) window.history.replaceState({}, '', window.location.pathname);
    if (!event.detail.onboarding_completed || requested) openTour();
  });
  overlay.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); skipTour(); return; }
    if (event.key !== 'Tab') return;
    const focusable = [...overlay.querySelectorAll('button:not([hidden]),a[href]')].filter(el => el.offsetParent !== null);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
})();
