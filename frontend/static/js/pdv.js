let cart = [];
let selectedProduct = null;
let selectedCustomerId = null;

function fmtMoney(v) {
  return 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;',
  })[char]);
}

function showAlert(msg, ok) {
  const el = document.getElementById('alert');
  el.className = ok ? 'alert ok' : 'alert err';
  el.textContent = msg;
  el.hidden = false;
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  setTimeout(() => { el.hidden = true; }, 6000);
}

async function loadLocations() {
  const resp = await fetch('/api/inventory/locations');
  const data = await resp.json();
  const select = document.getElementById('location-select');
  select.innerHTML = data.locations.map(l => `<option value="${l.id}">${l.code} - ${l.description || ''}</option>`).join('');
}

async function checkCashSession() {
  const resp = await fetch('/api/pdv/cash-session');
  const data = await resp.json();
  const status = document.getElementById('pdv-session-status');
  if (data.cash_session) {
    document.getElementById('cash-closed-card').hidden = true;
    document.getElementById('pdv-card').hidden = false;
    status.classList.add('is-open');
    status.innerHTML = '<span></span> Caixa aberto';
    await loadLocations();
  } else {
    document.getElementById('cash-closed-card').hidden = false;
    document.getElementById('pdv-card').hidden = true;
    status.classList.remove('is-open');
    status.innerHTML = '<span></span> Caixa fechado';
  }
}

document.getElementById('open-cash-btn').addEventListener('click', async () => {
  const opening_amount = document.getElementById('opening-amount').value || '0';
  const resp = await fetch('/api/pdv/cash-session/open', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ opening_amount }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  checkCashSession();
});

document.getElementById('close-cash-btn').addEventListener('click', () => {
  document.getElementById('close-cash-form').hidden = false;
});

document.getElementById('close-cash-cancel').addEventListener('click', () => {
  document.getElementById('close-cash-form').hidden = true;
});

document.getElementById('close-cash-confirm').addEventListener('click', async () => {
  const resp = await fetch('/api/pdv/cash-session');
  const data = await resp.json();
  if (!data.cash_session) return;

  const closing = document.getElementById('closing-amount').value || '0';
  const closeResp = await fetch(`/api/pdv/cash-session/${data.cash_session.id}/close`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ closing_amount: closing }),
  });
  const closeData = await closeResp.json();
  if (!closeResp.ok) { showAlert(closeData.error); return; }
  document.getElementById('close-cash-form').hidden = true;
  checkCashSession();
});

let searchTimeout;
document.getElementById('search-input').addEventListener('input', (e) => {
  clearTimeout(searchTimeout);
  const q = e.target.value.trim();
  const resultsEl = document.getElementById('search-results');
  if (!q) { resultsEl.innerHTML = ''; return; }
  searchTimeout = setTimeout(async () => {
    const resp = await fetch('/api/products?q=' + encodeURIComponent(q));
    const data = await resp.json();
    resultsEl.innerHTML = data.products.map(p => `
      <div class="search-result" data-id="${p.id}">
        <span>${escapeHtml(p.name)} <span style="color:var(--muted)">(${escapeHtml(p.sku)})</span></span>
        <span>${fmtMoney(p.sale_price)} / ${escapeHtml(p.base_unit)}</span>
      </div>
    `).join('') || '<div style="padding:10px;color:var(--muted)">Nenhum produto encontrado.</div>';

    resultsEl.querySelectorAll('.search-result').forEach(el => {
      el.addEventListener('click', () => openAddItemForm(data.products.find(p => p.id == el.dataset.id)));
    });
  }, 250);
});

// Leitor de codigo de barras: o leitor "digita" o codigo e envia Enter em
// seguida. Ao apertar Enter, tenta um match exato (SKU ou codigo de barras)
// e ja adiciona 1 unidade direto no carrinho — sem abrir o formulario,
// para agilizar a venda no balcao.
document.getElementById('search-input').addEventListener('keydown', async (e) => {
  if (e.key !== 'Enter') return;
  e.preventDefault();
  clearTimeout(searchTimeout);
  const code = e.target.value.trim();
  if (!code) return;

  const resp = await fetch('/api/products/lookup?code=' + encodeURIComponent(code));
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }

  cart.push({ product_id: data.product.id, name: data.product.name, unit: data.product.base_unit, quantity: 1, unit_price: parseFloat(data.product.sale_price) });
  renderCart();
  showAlert(`+1 ${data.product.base_unit} ${data.product.name}`, true);
  e.target.value = '';
  document.getElementById('search-results').innerHTML = '';
});

function openAddItemForm(product) {
  selectedProduct = product;
  document.getElementById('add-item-name').textContent = product.name + ' — ' + fmtMoney(product.sale_price) + ' / ' + product.base_unit;

  const imageEl = document.getElementById('add-item-image');
  if (product.image_url) { imageEl.src = product.image_url; imageEl.style.display = 'block'; }
  else { imageEl.style.display = 'none'; }

  const unitSelect = document.getElementById('add-item-unit');
  const units = [product.base_unit, ...product.conversions.map(c => c.unit)];
  unitSelect.innerHTML = units.map(u => `<option value="${u}">${u}</option>`).join('');

  document.getElementById('add-item-qty').value = '1';
  document.getElementById('add-item-form').hidden = false;
  document.getElementById('search-results').innerHTML = '';
}

function closeAddItemForm() {
  selectedProduct = null;
  document.getElementById('add-item-form').hidden = true;
  document.getElementById('search-input').value = '';
  document.getElementById('search-input').focus();
}

document.getElementById('add-item-cancel').addEventListener('click', closeAddItemForm);

document.getElementById('add-item-confirm').addEventListener('click', () => {
  if (!selectedProduct) return;
  const unit = document.getElementById('add-item-unit').value;
  const quantity = parseFloat(document.getElementById('add-item-qty').value);
  if (!quantity || quantity <= 0) { showAlert('Informe uma quantidade válida.'); return; }

  let unitPrice = parseFloat(selectedProduct.sale_price);
  if (unit !== selectedProduct.base_unit) {
    const conv = selectedProduct.conversions.find(c => c.unit === unit);
    unitPrice = unitPrice * parseFloat(conv.factor_to_base);
  }

  cart.push({ product_id: selectedProduct.id, name: selectedProduct.name, unit, quantity, unit_price: unitPrice });
  renderCart();
  closeAddItemForm();
});

function renderCart() {
  const el = document.getElementById('cart-items');
  if (cart.length === 0) {
    el.innerHTML = '<p style="color:var(--muted); font-size:.85rem">Nenhum item ainda.</p>';
  } else {
    el.innerHTML = cart.map((item, idx) => `
      <div class="cart-item">
        <div class="info">
          ${escapeHtml(item.name)}
          <div class="qty">${item.quantity} ${escapeHtml(item.unit)} x ${fmtMoney(item.unit_price)}</div>
        </div>
        <div>
          ${fmtMoney(item.quantity * item.unit_price)}
          <button class="danger" style="padding:4px 8px; margin-left:8px" data-idx="${idx}">×</button>
        </div>
      </div>
    `).join('');
    el.querySelectorAll('button[data-idx]').forEach(btn => {
      btn.addEventListener('click', () => { cart.splice(btn.dataset.idx, 1); renderCart(); });
    });
  }
  const total = cart.reduce((sum, i) => sum + i.quantity * i.unit_price, 0);
  document.getElementById('cart-total-value').textContent = fmtMoney(total);
  document.getElementById('mobile-cart-count').textContent = cart.length === 1 ? '1 item' : cart.length + ' itens';
  document.getElementById('mobile-cart-total').textContent = fmtMoney(total);
}

function setMobileCart(open) {
  document.body.classList.toggle('cart-open', open);
  document.getElementById('cart-scrim').hidden = !open;
  document.getElementById('mobile-cart-trigger').setAttribute('aria-expanded', String(open));
  if (open) document.getElementById('customer-name').focus();
  else document.getElementById('search-input').focus();
}

document.getElementById('mobile-cart-trigger').addEventListener('click', () => setMobileCart(true));
document.getElementById('cart-close-btn').addEventListener('click', () => setMobileCart(false));
document.getElementById('cart-scrim').addEventListener('click', () => setMobileCart(false));

function focusCart() {
  if (window.matchMedia('(max-width: 820px)').matches) {
    setMobileCart(true);
    return;
  }
  const panel = document.getElementById('pdv-cart-panel');
  panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  panel.focus({ preventScroll: true });
}

function isPdvOpen() {
  return !document.getElementById('pdv-card').hidden;
}

function runPdvAction(action) {
  if (action === 'search' && isPdvOpen()) document.getElementById('search-input').focus();
  if (action === 'finalize' && isPdvOpen()) document.getElementById('finalize-btn').click();
  if (action === 'cart' && isPdvOpen()) focusCart();
}

document.querySelectorAll('[data-pdv-action]').forEach(button => {
  button.addEventListener('click', () => runPdvAction(button.dataset.pdvAction));
});

document.addEventListener('keydown', event => {
  if (event.ctrlKey || event.altKey || event.metaKey) return;
  const routes = { F1: '/index.html', F3: '/operacao.html', F4: '/relatorios.html' };
  if (routes[event.key]) {
    event.preventDefault();
    window.location.assign(routes[event.key]);
    return;
  }
  if (['F2', 'F6', 'F8'].includes(event.key)) {
    event.preventDefault();
    runPdvAction({ F2: 'search', F6: 'finalize', F8: 'cart' }[event.key]);
    return;
  }
  if (event.key !== 'Escape') return;
  if (document.body.classList.contains('cart-open')) {
    setMobileCart(false);
  } else if (!document.getElementById('add-item-form').hidden) {
    closeAddItemForm();
  } else if (!document.getElementById('close-cash-form').hidden) {
    document.getElementById('close-cash-form').hidden = true;
    document.getElementById('search-input').focus();
  }
});

let customerSearchTimeout;
document.getElementById('customer-name').addEventListener('input', (e) => {
  selectedCustomerId = null;
  clearTimeout(customerSearchTimeout);
  const q = e.target.value.trim();
  const resultsEl = document.getElementById('customer-results');
  if (q.length < 2) { resultsEl.innerHTML = ''; return; }
  customerSearchTimeout = setTimeout(async () => {
    const resp = await fetch('/api/customers?q=' + encodeURIComponent(q));
    const data = await resp.json();
    resultsEl.innerHTML = data.customers.map(c => `
      <div class="search-result" data-id="${c.id}" data-name="${escapeHtml(c.name)}">
        <span>${escapeHtml(c.name)}</span>
        <span style="color:var(--muted)">${escapeHtml(c.phone || c.document || '')}</span>
      </div>
    `).join('');
    resultsEl.querySelectorAll('.search-result').forEach(el => {
      el.addEventListener('click', () => {
        selectedCustomerId = parseInt(el.dataset.id);
        document.getElementById('customer-name').value = el.dataset.name;
        resultsEl.innerHTML = '';
      });
    });
  }, 250);
});

function isCardPayment(method) {
  return method === 'cartao_debito' || method === 'cartao_credito';
}

document.getElementById('payment-method').addEventListener('change', (e) => {
  const cardField = document.getElementById('card-reference-field');
  cardField.hidden = !isCardPayment(e.target.value);
  if (cardField.hidden) document.getElementById('card-reference').value = '';
});

document.getElementById('finalize-btn').addEventListener('click', async () => {
  if (cart.length === 0) { showAlert('Adicione ao menos um item.'); return; }
  const total = cart.reduce((sum, i) => sum + i.quantity * i.unit_price, 0);
  const paymentMethod = document.getElementById('payment-method').value;
  const cardReference = document.getElementById('card-reference').value.trim();

  const payload = {
    location_id: parseInt(document.getElementById('location-select').value),
    items: cart.map(i => ({ product_id: i.product_id, unit: i.unit, quantity: i.quantity, unit_price: i.unit_price })),
    payments: [{
      method: paymentMethod,
      amount: total.toFixed(2),
      card_reference: isCardPayment(paymentMethod) && cardReference ? cardReference : null,
    }],
    customer_name: document.getElementById('customer-name').value || null,
    customer_id: selectedCustomerId,
  };

  const resp = await fetch('/api/pdv/sales', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }

  showAlert('Venda #' + data.sale.id + ' registrada com sucesso! Total: ' + fmtMoney(data.sale.total), true);
  cart = [];
  renderCart();
  document.getElementById('customer-name').value = '';
  document.getElementById('card-reference').value = '';
  document.getElementById('card-reference-field').hidden = true;
  document.getElementById('payment-method').value = 'dinheiro';
  selectedCustomerId = null;

  await showReceipt(data.sale.id);
});

async function showReceipt(saleId) {
  const resp = await fetch('/api/pdv/sales/' + saleId);
  const data = await resp.json();
  if (!resp.ok) return;
  const sale = data.sale;

  const itemsHtml = sale.items.map(i => `
    <div class="row"><span>${i.quantity} ${escapeHtml(i.unit)} x ${escapeHtml(i.product_name)}</span><span>${fmtMoney(i.total)}</span></div>
  `).join('');
  const paymentMethodLabels = {
    dinheiro: 'Dinheiro', pix: 'Pix', cartao_debito: 'Cartão débito',
    cartao_credito: 'Cartão crédito', boleto: 'Boleto', transferencia: 'Transferência',
  };
  const paymentsHtml = sale.payments.map(p => `
    <div class="row"><span>${escapeHtml(paymentMethodLabels[p.method] || p.method)}</span><span>${fmtMoney(p.amount)}</span></div>
    ${p.card_reference ? `<div class="row"><span style="color:var(--muted); font-size:.8rem">NSU/autorização</span><span style="color:var(--muted); font-size:.8rem">${escapeHtml(p.card_reference)}</span></div>` : ''}
  `).join('');

  document.getElementById('receipt-content').innerHTML = `
    <div style="text-align:center; margin-bottom:10px">
      <strong>F.I Construção</strong><br>
      <span style="color:var(--muted); font-size:.8rem">Comprovante de venda #${sale.id}</span>
    </div>
    <div class="row"><span>Data</span><span>${new Date(sale.created_at).toLocaleString('pt-BR')}</span></div>
    ${sale.customer_name ? `<div class="row"><span>Cliente</span><span>${escapeHtml(sale.customer_name)}</span></div>` : ''}
    <hr>
    ${itemsHtml}
    <hr>
    <div class="row total-row"><span>Total</span><span>${fmtMoney(sale.total)}</span></div>
    <hr>
    <div style="font-weight:600; margin-bottom:4px">Pagamento</div>
    ${paymentsHtml}
    <div style="text-align:center; margin-top:14px; color:var(--muted); font-size:.75rem">Obrigado pela preferência!</div>
  `;
  document.getElementById('receipt-content').classList.remove('thermal');
  document.getElementById('receipt-overlay').hidden = false;
}

document.getElementById('receipt-close-btn').addEventListener('click', () => {
  document.getElementById('receipt-overlay').hidden = true;
  setMobileCart(false);
  document.getElementById('search-input').focus();
});
document.getElementById('print-thermal-btn').addEventListener('click', () => {
  document.getElementById('receipt-content').classList.add('thermal');
  window.print();
});
document.getElementById('print-a4-btn').addEventListener('click', () => {
  document.getElementById('receipt-content').classList.remove('thermal');
  window.print();
});

checkCashSession();
