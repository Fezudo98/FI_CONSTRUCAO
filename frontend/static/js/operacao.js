function showAlert(msg, ok) {
  const el = document.getElementById('alert');
  el.className = ok ? 'alert ok' : 'alert err';
  el.textContent = msg;
  el.hidden = false;
  setTimeout(() => { el.hidden = true; }, 5000);
}

const TAB_RELOAD = {
  auditoria: () => loadAuditLogs(),
  clientes: () => loadCustomers(),
};

const MODULE_META = {
  estoque: { title: 'Estoque', description: 'Produtos, endereços e saldos disponíveis.', actions: [['Novo produto', 'form-product'], ['Ajustar saldo', 'form-adjustment'], ['Novo endereço', 'form-location']] },
  clientes: { title: 'Clientes', description: 'Cadastro e consulta rápida para vendas e pedidos.', actions: [['Novo cliente', 'form-customer']] },
  orcamentos: { title: 'Orçamentos', description: 'Propostas comerciais prontas para aprovação e conversão.', actions: [['Novo orçamento', 'form-quote']] },
  pedidos: { title: 'Pedidos', description: 'Reserva, separação, retirada e entrega.', actions: [['Novo pedido', 'form-order']] },
  compras: { title: 'Compras', description: 'Fornecedores, pedidos de compra e recebimentos.', actions: [['Novo pedido de compra', 'form-purchase'], ['Novo fornecedor', 'form-supplier']] },
  financeiro: { title: 'Financeiro', description: 'Contas a pagar e baixas de pagamento.', actions: [] },
  entregas: { title: 'Entregas', description: 'Recursos, agendamentos e acompanhamento da rota.', actions: [['Agendar entrega', 'form-delivery'], ['Recursos logísticos', 'form-logistics-resources']] },
  auditoria: { title: 'Auditoria', description: 'Histórico das ações sensíveis realizadas no sistema.', actions: [] },
};

document.querySelectorAll('[data-form-panel]').forEach(panel => panel.hidden = true);

function renderModuleActions(meta) {
  const container = document.getElementById('operation-actions');
  container.replaceChildren();
  meta.actions.forEach(([label, targetId], index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = index === 0 ? 'primary' : 'secondary';
    button.textContent = label;
    button.addEventListener('click', () => {
      const panel = document.getElementById(targetId);
      const willOpen = panel.hidden;
      document.querySelectorAll('#' + panel.closest('.section').id + ' [data-form-panel]').forEach(item => item.hidden = true);
      panel.hidden = !willOpen;
      if (willOpen) {
        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
        const field = panel.querySelector('input:not([type="hidden"]), select, textarea');
        if (field) setTimeout(() => field.focus(), 250);
      }
    });
    container.appendChild(button);
  });
}

function activateTab(name, updateHash) {
  const btn = document.querySelector(`.tabs button[data-tab="${name}"]`);
  const section = document.getElementById('section-' + name);
  if (!btn || !section) return;
  document.querySelectorAll('.tabs button').forEach(b => {
    b.classList.toggle('active', b === btn);
    b.setAttribute('aria-selected', String(b === btn));
  });
  document.querySelectorAll('.section').forEach(s => s.classList.toggle('active', s === section));
  const meta = MODULE_META[name];
  document.getElementById('operation-title').textContent = meta.title;
  document.getElementById('operation-description').textContent = meta.description;
  renderModuleActions(meta);
  if (updateHash && window.location.hash !== '#' + name) history.pushState({ tab: name }, '', '#' + name);
  if (TAB_RELOAD[name]) TAB_RELOAD[name]();
}

document.querySelectorAll('.tabs button').forEach(btn => {
  btn.setAttribute('role', 'tab');
  btn.addEventListener('click', () => activateTab(btn.dataset.tab, true));
});
window.addEventListener('popstate', () => activateTab(window.location.hash.slice(1) || 'estoque', false));
activateTab(window.location.hash.slice(1) || 'estoque', false);

let PRODUCTS = [];
let LOCATIONS = [];

async function loadProducts() {
  const resp = await fetch('/api/products');
  const data = await resp.json();
  PRODUCTS = data.products;

  const tbody = document.querySelector('#products-table tbody');
  tbody.innerHTML = data.products.map(p => `
    <tr>
      <td>
        ${p.image_url ? `<img src="${p.image_url}" alt="${p.name}" style="width:40px;height:40px;object-fit:cover;border-radius:6px">` : '<span style="color:var(--muted);font-size:.75rem">sem foto</span>'}
      </td>
      <td>${p.sku}</td><td>${p.name}</td><td>${p.base_unit}</td><td>R$ ${p.cost_price}</td><td>R$ ${p.sale_price}</td>
      <td>
        <label class="secondary btn" style="padding:5px 10px; font-size:.75rem; cursor:pointer">
          Trocar foto<input type="file" accept="image/jpeg,image/png,image/webp" style="display:none" onchange="uploadProductImage(${p.id}, this)">
        </label>
      </td>
    </tr>
  `).join('');

  document.getElementById('adjust-product').innerHTML =
    data.products.map(p => `<option value="${p.id}">${p.name} (${p.sku})</option>`).join('');

  document.querySelectorAll('.item-builder').forEach(b => b.refreshProductOptions());
}

async function uploadProductImage(productId, inputEl) {
  const file = inputEl.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('image', file);
  const resp = await fetch(`/api/products/${productId}/image`, { method: 'POST', body: formData });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Imagem atualizada.', true);
  loadProducts();
}

async function loadLocations() {
  const resp = await fetch('/api/inventory/locations');
  const data = await resp.json();
  LOCATIONS = data.locations;
  const optionsHtml = data.locations.map(l => `<option value="${l.id}">${l.code} - ${l.description || ''}</option>`).join('');

  document.getElementById('adjust-location').innerHTML = optionsHtml;
  ['order-location', 'quote-convert-location', 'po-receive-location'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = optionsHtml;
  });
}

document.getElementById('create-loc-btn').addEventListener('click', async () => {
  const code = document.getElementById('loc-code').value.trim();
  const description = document.getElementById('loc-desc').value.trim();
  if (!code) { showAlert('Informe o código do endereço.'); return; }

  const resp = await fetch('/api/inventory/locations', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, description }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Endereço criado.', true);
  document.getElementById('loc-code').value = '';
  document.getElementById('loc-desc').value = '';
  loadLocations();
});

document.getElementById('create-prod-btn').addEventListener('click', async () => {
  const payload = {
    sku: document.getElementById('prod-sku').value.trim(),
    name: document.getElementById('prod-name').value.trim(),
    base_unit: document.getElementById('prod-unit').value.trim().toUpperCase(),
    cost_price: document.getElementById('prod-cost').value || 0,
    sale_price: document.getElementById('prod-price').value || 0,
    min_stock: document.getElementById('prod-min').value || 0,
    barcode: document.getElementById('prod-barcode').value.trim() || null,
  };
  if (!payload.sku || !payload.name || !payload.base_unit) {
    showAlert('Preencha SKU, nome e unidade base.');
    return;
  }

  const resp = await fetch('/api/products', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }

  const imageFile = document.getElementById('prod-image').files[0];
  if (imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);
    await fetch(`/api/products/${data.product.id}/image`, { method: 'POST', body: formData });
  }

  showAlert('Produto criado.', true);
  ['prod-sku', 'prod-name', 'prod-unit', 'prod-cost', 'prod-price', 'prod-barcode'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('prod-image').value = '';
  loadProducts();
});

document.getElementById('adjust-barcode-scan').addEventListener('keydown', async (e) => {
  if (e.key !== 'Enter') return;
  e.preventDefault();
  const code = e.target.value.trim();
  if (!code) return;

  const resp = await fetch('/api/products/lookup?code=' + encodeURIComponent(code));
  const data = await resp.json();
  e.target.value = '';
  if (!resp.ok) { showAlert(data.error); return; }

  document.getElementById('adjust-product').value = data.product.id;
  document.getElementById('adjust-qty').focus();
  showAlert(`Produto selecionado: ${data.product.name}`, true);
});

document.getElementById('adjust-btn').addEventListener('click', async () => {
  const product_id = parseInt(document.getElementById('adjust-product').value);
  const location_id = parseInt(document.getElementById('adjust-location').value);
  const new_quantity = document.getElementById('adjust-qty').value;
  if (!product_id || !location_id || new_quantity === '') { showAlert('Preencha todos os campos.'); return; }

  const resp = await fetch('/api/inventory/adjust', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id, location_id, new_quantity }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Saldo ajustado para ' + data.balance.quantity + '.', true);
});

// ---------- helpers compartilhados ----------

function actionBtn(fn, label, cls) {
  return `<button type="button" class="${cls || 'secondary'}" style="padding:5px 10px; font-size:.75rem; margin:2px 2px 0 0" onclick="${fn}">${label}</button>`;
}

/** Autocomplete de cliente cadastrado sobre um <input> de texto livre.
 * Retorna um objeto com getSelectedId()/reset(), sem travar a digitação de
 * um nome avulso (cliente nao precisa estar cadastrado). */
function setupCustomerAutocomplete(inputId, resultsId) {
  const input = document.getElementById(inputId);
  const results = document.getElementById(resultsId);
  let selectedId = null;
  let timeout;

  input.addEventListener('input', (e) => {
    selectedId = null;
    clearTimeout(timeout);
    const q = e.target.value.trim();
    if (q.length < 2) { results.innerHTML = ''; return; }
    timeout = setTimeout(async () => {
      const resp = await fetch('/api/customers?q=' + encodeURIComponent(q));
      const data = await resp.json();
      results.innerHTML = data.customers.map(c => `
        <div class="search-result" data-id="${c.id}" data-name="${c.name}" data-doc="${c.document || ''}" data-phone="${c.phone || ''}">
          <span>${c.name}</span><span style="color:var(--muted)">${c.phone || c.document || ''}</span>
        </div>
      `).join('');
      results.querySelectorAll('.search-result').forEach(el => {
        el.addEventListener('click', () => {
          selectedId = parseInt(el.dataset.id);
          input.value = el.dataset.name;
          results.innerHTML = '';
          results.dispatchEvent(new CustomEvent('customer-selected', { detail: el.dataset }));
        });
      });
    }, 250);
  });

  return { getSelectedId: () => selectedId, reset: () => { selectedId = null; input.value = ''; results.innerHTML = ''; } };
}

const STATUS_BADGE = {
  draft: 'warn', sent: 'warn', approved: 'ok', rejected: 'err', converted: 'ok',
  reserved: 'warn', separated: 'warn', picked_up: 'ok', delivered: 'ok', cancelled: 'err',
  open: 'warn', partially_paid: 'warn', paid: 'ok',
  scheduled: 'warn', in_route: 'warn', completed: 'ok', failed: 'err',
  partially_received: 'warn', received: 'ok',
};
const STATUS_LABEL = {
  draft: 'Rascunho', sent: 'Enviado', approved: 'Aprovado', rejected: 'Rejeitado', converted: 'Convertido',
  reserved: 'Reservado', separated: 'Separado', picked_up: 'Retirado', delivered: 'Entregue', cancelled: 'Cancelado',
  open: 'Em aberto', partially_paid: 'Parcial', paid: 'Pago',
  scheduled: 'Agendado', in_route: 'Em rota', completed: 'Concluído', failed: 'Falhou',
  partially_received: 'Parcial', received: 'Recebido',
};
function statusBadge(html_id_prefix, s) { return `<span class="badge ${STATUS_BADGE[s] || 'warn'}">${STATUS_LABEL[s] || s}</span>`; }

function createItemBuilder(containerId) {
  const container = document.getElementById(containerId);
  container.classList.add('item-builder');
  let items = [];

  function updateUnitPrice(productSelect, unitSelect, priceInput) {
    const product = PRODUCTS.find(p => p.id == productSelect.value);
    if (!product) return;
    if (unitSelect.value === product.base_unit) { priceInput.value = product.sale_price; return; }
    const conv = product.conversions.find(c => c.unit === unitSelect.value);
    priceInput.value = conv ? (parseFloat(product.sale_price) * parseFloat(conv.factor_to_base)).toFixed(4) : product.sale_price;
  }

  function render() {
    const productOptions = PRODUCTS.map(p => `<option value="${p.id}">${p.name} (${p.sku})</option>`).join('');
    container.innerHTML = `
      <div class="grid grid-3" style="margin-top:12px">
        <div><label>Produto</label><select class="ib-product">${productOptions}</select></div>
        <div><label>Unidade</label><select class="ib-unit"></select></div>
        <div><label>Quantidade</label><input type="number" step="0.01" class="ib-qty" value="1"></div>
      </div>
      <div class="grid grid-2" style="margin-top:8px">
        <div><label>Preço unitário</label><input type="number" step="0.0001" class="ib-price"></div>
        <div style="display:flex; align-items:flex-end"><button type="button" class="secondary ib-add" style="width:100%">+ Adicionar item</button></div>
      </div>
      <div class="table-responsive"><table style="margin-top:10px"><thead><tr><th>Produto</th><th>Qtd</th><th>Preço</th><th>Total</th><th></th></tr></thead>
        <tbody class="ib-list"></tbody></table></div>
      <div style="text-align:right; font-weight:700; margin-top:6px">Total: <span class="ib-total">R$ 0,00</span></div>
    `;

    const productSelect = container.querySelector('.ib-product');
    const unitSelect = container.querySelector('.ib-unit');
    const priceInput = container.querySelector('.ib-price');

    function refreshUnits() {
      const product = PRODUCTS.find(p => p.id == productSelect.value);
      if (!product) return;
      const units = [product.base_unit, ...product.conversions.map(c => c.unit)];
      unitSelect.innerHTML = units.map(u => `<option value="${u}">${u}</option>`).join('');
      updateUnitPrice(productSelect, unitSelect, priceInput);
    }
    productSelect.addEventListener('change', refreshUnits);
    unitSelect.addEventListener('change', () => updateUnitPrice(productSelect, unitSelect, priceInput));
    if (PRODUCTS.length) refreshUnits();

    container.querySelector('.ib-add').addEventListener('click', () => {
      const product = PRODUCTS.find(p => p.id == productSelect.value);
      if (!product) { showAlert('Cadastre um produto primeiro.'); return; }
      const quantity = parseFloat(container.querySelector('.ib-qty').value);
      const unit_price = parseFloat(priceInput.value);
      if (!quantity || quantity <= 0) { showAlert('Quantidade inválida.'); return; }
      if (isNaN(unit_price) || unit_price < 0) { showAlert('Preço inválido.'); return; }
      items.push({ product_id: product.id, name: product.name, unit: unitSelect.value, quantity, unit_price });
      renderList();
    });

    renderList();
  }

  function renderList() {
    const tbody = container.querySelector('.ib-list');
    tbody.innerHTML = items.map((it, idx) => `
      <tr><td>${it.name}</td><td>${it.quantity} ${it.unit}</td><td>R$ ${Number(it.unit_price).toFixed(2)}</td>
      <td>R$ ${(it.quantity * it.unit_price).toFixed(2)}</td>
      <td><button type="button" class="danger ib-remove" data-idx="${idx}" style="padding:4px 8px">×</button></td></tr>
    `).join('') || '<tr><td colspan="5" style="color:var(--muted)">Nenhum item ainda.</td></tr>';
    const total = items.reduce((s, i) => s + i.quantity * i.unit_price, 0);
    container.querySelector('.ib-total').textContent = 'R$ ' + total.toFixed(2);
    tbody.querySelectorAll('.ib-remove').forEach(btn => btn.addEventListener('click', () => {
      items.splice(parseInt(btn.dataset.idx), 1); renderList();
    }));
  }

  render();
  const api = {
    getItems: () => items.map(({ product_id, unit, quantity, unit_price }) => ({ product_id, unit, quantity, unit_price })),
    reset: () => { items = []; render(); },
    refreshProductOptions: () => render(),
  };
  container.refreshProductOptions = api.refreshProductOptions;
  return api;
}

// ---------- orçamentos ----------

const quoteBuilder = createItemBuilder('quote-items-builder');
const quoteCustomerAutocomplete = setupCustomerAutocomplete('quote-customer', 'quote-customer-results');

async function loadQuotes() {
  const resp = await fetch('/api/quotes');
  const data = await resp.json();
  const tbody = document.querySelector('#quotes-table tbody');
  tbody.innerHTML = data.quotes.map(q => {
    let actions = '';
    if (q.status === 'draft') actions += actionBtn(`sendQuote(${q.id})`, 'Enviar');
    if (q.status === 'draft' || q.status === 'sent') {
      actions += actionBtn(`approveQuote(${q.id})`, 'Aprovar');
      actions += actionBtn(`rejectQuote(${q.id})`, 'Rejeitar', 'danger');
    }
    if (q.status === 'approved' && !q.has_order) actions += actionBtn(`convertQuote(${q.id})`, 'Converter em pedido', 'primary');
    return `<tr><td>${q.id}</td><td>${q.customer_name}</td><td>R$ ${q.total}</td><td>${statusBadge('q', q.status)}</td><td>${actions}</td></tr>`;
  }).join('') || '<tr><td colspan="5" style="color:var(--muted)">Nenhum orçamento ainda.</td></tr>';
}

document.getElementById('quote-create-btn').addEventListener('click', async () => {
  const items = quoteBuilder.getItems();
  const customer_name = document.getElementById('quote-customer').value.trim();
  if (!customer_name) { showAlert('Informe o nome do cliente.'); return; }
  if (!items.length) { showAlert('Adicione ao menos um item.'); return; }

  const resp = await fetch('/api/quotes', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      customer_name,
      customer_document: document.getElementById('quote-document').value.trim() || null,
      customer_phone: document.getElementById('quote-phone').value.trim() || null,
      customer_id: quoteCustomerAutocomplete.getSelectedId(),
      items,
    }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Orçamento criado.', true);
  quoteCustomerAutocomplete.reset();
  document.getElementById('quote-document').value = '';
  document.getElementById('quote-phone').value = '';
  quoteBuilder.reset();
  loadQuotes();
});

async function sendQuote(id) {
  const resp = await fetch(`/api/quotes/${id}/send`, { method: 'POST' });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  loadQuotes();
}
async function approveQuote(id) {
  const resp = await fetch(`/api/quotes/${id}/approve`, { method: 'POST' });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  loadQuotes();
}
async function rejectQuote(id) {
  const resp = await fetch(`/api/quotes/${id}/reject`, { method: 'POST' });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  loadQuotes();
}
async function convertQuote(id) {
  const location_id = parseInt(document.getElementById('quote-convert-location').value);
  if (!location_id) { showAlert('Cadastre um endereço de estoque primeiro.'); return; }
  const resp = await fetch(`/api/quotes/${id}/convert`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ location_id }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Orçamento convertido em pedido #' + data.order_id + '.', true);
  loadQuotes();
  loadOrders();
}

// ---------- pedidos ----------

const orderBuilder = createItemBuilder('order-items-builder');
const orderCustomerAutocomplete = setupCustomerAutocomplete('order-customer', 'order-customer-results');
const ORDER_NEXT_LABEL = { reserved: 'Separar', separated: 'Confirmar retirada', picked_up: 'Marcar entregue' };

async function loadOrders() {
  const resp = await fetch('/api/orders');
  const data = await resp.json();
  window.ORDERS = data.orders;

  const tbody = document.querySelector('#orders-table tbody');
  tbody.innerHTML = data.orders.map(o => {
    let actions = '';
    const nextLabel = ORDER_NEXT_LABEL[o.status];
    if (nextLabel && (o.status !== 'picked_up' || o.is_delivery)) {
      actions += actionBtn(`advanceOrder(${o.id})`, nextLabel, 'primary');
    }
    if (o.status === 'reserved' || o.status === 'separated') {
      actions += actionBtn(`cancelOrder(${o.id})`, 'Cancelar', 'danger');
    }
    return `<tr><td>${o.id}</td><td>${o.customer_name}</td><td>R$ ${o.total}</td><td>${statusBadge('o', o.status)}</td><td>${o.is_delivery ? 'Sim' : 'Não'}</td><td>${actions}</td></tr>`;
  }).join('') || '<tr><td colspan="6" style="color:var(--muted)">Nenhum pedido ainda.</td></tr>';

  const deliveryOrderSelect = document.getElementById('delivery-order');
  if (deliveryOrderSelect) {
    const eligible = data.orders.filter(o => o.is_delivery && !o.has_delivery && o.status !== 'cancelled');
    deliveryOrderSelect.innerHTML = eligible.map(o => `<option value="${o.id}">#${o.id} - ${o.customer_name}</option>`).join('')
      || '<option value="">Nenhum pedido de entrega pendente</option>';
  }
}

document.getElementById('order-create-btn').addEventListener('click', async () => {
  const items = orderBuilder.getItems();
  const customer_name = document.getElementById('order-customer').value.trim();
  const location_id = parseInt(document.getElementById('order-location').value);
  if (!customer_name) { showAlert('Informe o nome do cliente.'); return; }
  if (!location_id) { showAlert('Cadastre um endereço de estoque primeiro.'); return; }
  if (!items.length) { showAlert('Adicione ao menos um item.'); return; }

  const resp = await fetch('/api/orders', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      customer_name, location_id, items,
      is_delivery: document.getElementById('order-is-delivery').checked,
      customer_id: orderCustomerAutocomplete.getSelectedId(),
    }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Pedido #' + data.order.id + ' criado.', true);
  orderCustomerAutocomplete.reset();
  document.getElementById('order-is-delivery').checked = false;
  orderBuilder.reset();
  loadOrders();
});

async function advanceOrder(id) {
  const resp = await fetch(`/api/orders/${id}/advance`, { method: 'POST' });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  loadOrders();
}
async function cancelOrder(id) {
  const resp = await fetch(`/api/orders/${id}/cancel`, { method: 'POST' });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  loadOrders();
}

// ---------- compras ----------

const poBuilder = createItemBuilder('po-items-builder');

async function loadSuppliers() {
  const resp = await fetch('/api/purchasing/suppliers');
  const data = await resp.json();
  window.SUPPLIERS = data.suppliers;
  const select = document.getElementById('po-supplier');
  select.innerHTML = data.suppliers.map(s => `<option value="${s.id}">${s.name}</option>`).join('')
    || '<option value="">Cadastre um fornecedor</option>';
}

document.getElementById('supplier-create-btn').addEventListener('click', async () => {
  const name = document.getElementById('supplier-name').value.trim();
  if (!name) { showAlert('Informe o nome do fornecedor.'); return; }
  const resp = await fetch('/api/purchasing/suppliers', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      document: document.getElementById('supplier-document').value.trim() || null,
      phone: document.getElementById('supplier-phone').value.trim() || null,
    }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Fornecedor criado.', true);
  document.getElementById('supplier-name').value = '';
  document.getElementById('supplier-document').value = '';
  document.getElementById('supplier-phone').value = '';
  loadSuppliers();
  loadCarrierSelects();
});

async function loadPurchaseOrders() {
  const resp = await fetch('/api/purchasing/orders');
  const data = await resp.json();
  window.PURCHASE_ORDERS = data.purchase_orders;
  const tbody = document.querySelector('#po-table tbody');
  tbody.innerHTML = data.purchase_orders.map(po => {
    let actions = '';
    if (po.status === 'sent' || po.status === 'partially_received') {
      actions += actionBtn(`openReceivePanel(${po.id})`, 'Receber', 'primary');
    }
    return `<tr><td>${po.id}</td><td>${po.supplier_name || ''}</td><td>R$ ${po.total}</td><td>${statusBadge('po', po.status)}</td><td>${actions}</td></tr>`;
  }).join('') || '<tr><td colspan="5" style="color:var(--muted)">Nenhum pedido de compra ainda.</td></tr>';
}

document.getElementById('po-create-btn').addEventListener('click', async () => {
  const items = poBuilder.getItems();
  const supplier_id = parseInt(document.getElementById('po-supplier').value);
  if (!supplier_id) { showAlert('Cadastre um fornecedor primeiro.'); return; }
  if (!items.length) { showAlert('Adicione ao menos um item.'); return; }

  const resp = await fetch('/api/purchasing/orders', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ supplier_id, items }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Pedido de compra #' + data.purchase_order.id + ' criado.', true);
  poBuilder.reset();
  loadPurchaseOrders();
});

function openReceivePanel(poId) {
  const po = window.PURCHASE_ORDERS.find(p => p.id === poId);
  if (!po) return;
  document.getElementById('po-receive-id').textContent = po.id;
  document.getElementById('po-receive-panel').hidden = false;
  document.getElementById('po-receive-panel').dataset.poId = poId;

  const tbody = document.getElementById('po-receive-items');
  tbody.innerHTML = po.items.map(item => {
    const product = PRODUCTS.find(p => p.id === item.product_id);
    const pending = (parseFloat(item.quantity) - parseFloat(item.quantity_received)).toFixed(4);
    if (parseFloat(pending) <= 0) return '';
    return `<tr data-po-item-id="${item.id}" data-pending="${pending}">
      <td>${product ? product.name : item.product_id}</td>
      <td>${pending} ${item.unit}</td>
      <td><input type="number" step="0.01" class="receive-qty" max="${pending}" placeholder="0"></td>
    </tr>`;
  }).join('');
  document.getElementById('po-receive-panel').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

document.getElementById('po-receive-cancel').addEventListener('click', () => {
  document.getElementById('po-receive-panel').hidden = true;
});

document.getElementById('po-receive-confirm').addEventListener('click', async () => {
  const panel = document.getElementById('po-receive-panel');
  const poId = panel.dataset.poId;
  const location_id = parseInt(document.getElementById('po-receive-location').value);
  if (!location_id) { showAlert('Selecione o endereço de recebimento.'); return; }

  const items = [];
  panel.querySelectorAll('tr[data-po-item-id]').forEach(row => {
    const qty = parseFloat(row.querySelector('.receive-qty').value);
    if (qty && qty > 0) {
      items.push({ purchase_order_item_id: parseInt(row.dataset.poItemId), quantity: qty });
    }
  });
  if (!items.length) { showAlert('Informe a quantidade recebida de ao menos um item.'); return; }

  const resp = await fetch(`/api/purchasing/orders/${poId}/receive`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ location_id, items }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Recebimento confirmado.', true);
  panel.hidden = true;
  loadPurchaseOrders();
  loadProducts();
  loadPayables();
});

// ---------- financeiro ----------

async function loadPayables() {
  const resp = await fetch('/api/finance/payables');
  const data = await resp.json();
  const tbody = document.querySelector('#payables-table tbody');
  tbody.innerHTML = data.payables.map(p => {
    let actions = '';
    if (p.status !== 'paid') actions += actionBtn(`openSettlePanel(${p.id}, ${p.amount_open})`, 'Baixar', 'primary');
    return `<tr><td>${p.supplier_name || ''}</td><td>${p.description || ''}</td><td>R$ ${p.amount}</td>
      <td>R$ ${p.amount_paid}</td><td>R$ ${p.amount_open}</td><td>${p.due_date || ''}</td>
      <td>${statusBadge('p', p.status)}</td><td>${actions}</td></tr>`;
  }).join('') || '<tr><td colspan="8" style="color:var(--muted)">Nenhuma conta a pagar.</td></tr>';
}

function openSettlePanel(payableId, amountOpen) {
  document.getElementById('settle-payable-id').value = payableId;
  document.getElementById('settle-amount').value = amountOpen;
  document.getElementById('settle-amount').max = amountOpen;
  document.getElementById('settle-context').textContent = `Saldo em aberto: R$ ${amountOpen}`;
  openDialog('settle-dialog', 'settle-amount');
}

async function settlePayable(payableId, amount, method) {
  const error = document.getElementById('settle-error');
  try {
    const resp = await fetch(`/api/finance/payables/${payableId}/settle`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount, method }),
    });
    const data = await resp.json();
    if (!resp.ok) { error.textContent = data.error || 'Não foi possível registrar a baixa.'; error.hidden = false; return false; }
    showAlert('Baixa registrada.', true);
    closeDialog('settle-dialog');
    loadPayables();
    return true;
  } catch (_) {
    error.textContent = 'Servidor indisponível. Tente novamente.';
    error.hidden = false;
    return false;
  }
}

// ---------- entregas ----------

async function loadCarrierSelects() {
  const resp = await fetch('/api/logistics/carriers');
  const data = await resp.json();
  const options = data.carriers.map(c => `<option value="${c.id}">${c.name}</option>`).join('') || '<option value="">Cadastre uma transportadora</option>';
  ['vehicle-carrier', 'driver-carrier'].forEach(id => document.getElementById(id).innerHTML = options);
}

async function loadVehiclesAndDrivers() {
  const [vResp, dResp] = await Promise.all([fetch('/api/logistics/vehicles'), fetch('/api/logistics/drivers')]);
  const vData = await vResp.json();
  const dData = await dResp.json();
  document.getElementById('delivery-vehicle').innerHTML =
    '<option value="">Nenhum</option>' + vData.vehicles.map(v => `<option value="${v.id}">${v.plate}</option>`).join('');
  document.getElementById('delivery-driver').innerHTML =
    '<option value="">Nenhum</option>' + dData.drivers.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
}

document.getElementById('carrier-create-btn').addEventListener('click', async () => {
  const name = document.getElementById('carrier-name').value.trim();
  if (!name) { showAlert('Informe o nome da transportadora.'); return; }
  const resp = await fetch('/api/logistics/carriers', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Transportadora criada.', true);
  document.getElementById('carrier-name').value = '';
  loadCarrierSelects();
});

document.getElementById('vehicle-create-btn').addEventListener('click', async () => {
  const carrier_id = parseInt(document.getElementById('vehicle-carrier').value);
  const plate = document.getElementById('vehicle-plate').value.trim();
  if (!carrier_id || !plate) { showAlert('Selecione a transportadora e informe a placa.'); return; }
  const resp = await fetch('/api/logistics/vehicles', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ carrier_id, plate }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Veículo criado.', true);
  document.getElementById('vehicle-plate').value = '';
  loadVehiclesAndDrivers();
});

document.getElementById('driver-create-btn').addEventListener('click', async () => {
  const carrier_id = parseInt(document.getElementById('driver-carrier').value);
  const name = document.getElementById('driver-name').value.trim();
  if (!carrier_id || !name) { showAlert('Selecione a transportadora e informe o nome.'); return; }
  const resp = await fetch('/api/logistics/drivers', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ carrier_id, name }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Motorista criado.', true);
  document.getElementById('driver-name').value = '';
  loadVehiclesAndDrivers();
});

async function loadDeliveries() {
  const resp = await fetch('/api/logistics/deliveries');
  const data = await resp.json();
  const DELIVERY_NEXT_LABEL = { scheduled: 'Iniciar rota', in_route: 'Confirmar entrega' };
  const tbody = document.querySelector('#deliveries-table tbody');
  tbody.innerHTML = data.deliveries.map(d => {
    let actions = '';
    const nextLabel = DELIVERY_NEXT_LABEL[d.status];
    if (nextLabel) actions += actionBtn(`advanceDelivery(${d.id})`, nextLabel, 'primary');
    if (d.status !== 'completed' && d.status !== 'failed') {
      actions += actionBtn(`addOccurrence(${d.id})`, 'Registrar ocorrência');
    }
    return `<tr><td>${d.id}</td><td>${d.customer_name || ''}</td><td>${d.address || ''}</td><td>${statusBadge('d', d.status)}</td><td>${actions}</td></tr>`;
  }).join('') || '<tr><td colspan="5" style="color:var(--muted)">Nenhuma entrega ainda.</td></tr>';
}

document.getElementById('delivery-create-btn').addEventListener('click', async () => {
  const order_id = parseInt(document.getElementById('delivery-order').value);
  const address = document.getElementById('delivery-address').value.trim();
  if (!order_id) { showAlert('Selecione um pedido de entrega pendente.'); return; }
  if (!address) { showAlert('Informe o endereço de entrega.'); return; }

  const vehicle_id = document.getElementById('delivery-vehicle').value || null;
  const driver_id = document.getElementById('delivery-driver').value || null;

  const resp = await fetch('/api/logistics/deliveries', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ order_id, address, vehicle_id, driver_id }),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Entrega agendada.', true);
  document.getElementById('delivery-address').value = '';
  loadDeliveries();
  loadOrders();
});

async function advanceDelivery(id) {
  const resp = await fetch(`/api/logistics/deliveries/${id}/advance`, { method: 'POST' });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  loadDeliveries();
  loadOrders();
}

function addOccurrence(deliveryId) {
  document.getElementById('occurrence-delivery-id').value = deliveryId;
  document.getElementById('occurrence-kind').value = 'atraso';
  document.getElementById('occurrence-description').value = '';
  openDialog('occurrence-dialog', 'occurrence-kind');
}

let dialogTrigger = null;
function openDialog(id, focusId) {
  dialogTrigger = document.activeElement;
  const dialog = document.getElementById(id);
  dialog.hidden = false;
  document.body.classList.add('dialog-open');
  requestAnimationFrame(() => document.getElementById(focusId).focus());
}

function closeDialog(id) {
  document.getElementById(id).hidden = true;
  document.body.classList.remove('dialog-open');
  if (dialogTrigger) dialogTrigger.focus();
}

document.querySelectorAll('.dialog-close').forEach(btn => btn.addEventListener('click', () => closeDialog(btn.dataset.dialog)));
document.querySelectorAll('.dialog-overlay').forEach(dialog => dialog.addEventListener('click', e => {
  if (e.target === dialog) closeDialog(dialog.id);
}));
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') document.querySelectorAll('.dialog-overlay:not([hidden])').forEach(dialog => closeDialog(dialog.id));
});

document.getElementById('settle-form').addEventListener('submit', async e => {
  e.preventDefault();
  const button = e.currentTarget.querySelector('[type="submit"]');
  const error = document.getElementById('settle-error');
  const amount = document.getElementById('settle-amount').value;
  const max = Number(document.getElementById('settle-amount').max);
  error.hidden = true;
  if (Number(amount) <= 0 || Number(amount) > max) {
    error.textContent = `Informe um valor entre R$ 0,01 e R$ ${max}.`;
    error.hidden = false;
    return;
  }
  button.disabled = true;
  try {
    await settlePayable(Number(document.getElementById('settle-payable-id').value), amount, document.getElementById('settle-method').value || null);
  } finally { button.disabled = false; }
});

document.getElementById('occurrence-form').addEventListener('submit', async e => {
  e.preventDefault();
  const button = e.currentTarget.querySelector('[type="submit"]');
  const deliveryId = Number(document.getElementById('occurrence-delivery-id').value);
  const kind = document.getElementById('occurrence-kind').value;
  const description = document.getElementById('occurrence-description').value.trim() || null;
  const error = document.getElementById('occurrence-error');
  error.hidden = true;
  button.disabled = true;
  try {
    const response = await fetch(`/api/logistics/deliveries/${deliveryId}/occurrences`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kind, description }),
    });
    const data = await response.json();
    if (!response.ok) { error.textContent = data.error || 'Não foi possível registrar a ocorrência.'; error.hidden = false; return; }
    showAlert('Ocorrência registrada.', true);
    closeDialog('occurrence-dialog');
    loadDeliveries();
  } finally { button.disabled = false; }
});

// ---------- clientes ----------

async function loadCustomers(q) {
  const resp = await fetch('/api/customers' + (q ? '?q=' + encodeURIComponent(q) : ''));
  const data = await resp.json();
  const tbody = document.querySelector('#customers-table tbody');
  tbody.innerHTML = data.customers.map(c => `
    <tr>
      <td>${c.name}</td><td>${c.document || ''}</td><td>${c.phone || ''}</td>
      <td>${c.full_address || ''}</td>
      <td>${actionBtn(`deleteCustomer(${c.id})`, 'Remover', 'danger')}</td>
    </tr>
  `).join('') || '<tr><td colspan="5" style="color:var(--muted)">Nenhum cliente cadastrado.</td></tr>';
}

document.getElementById('customer-search').addEventListener('input', (e) => {
  loadCustomers(e.target.value.trim());
});

document.getElementById('customer-create-btn').addEventListener('click', async () => {
  const payload = {
    name: document.getElementById('cust-name').value.trim(),
    document: document.getElementById('cust-document').value.trim() || null,
    phone: document.getElementById('cust-phone').value.trim() || null,
    email: document.getElementById('cust-email').value.trim() || null,
    address_street: document.getElementById('cust-street').value.trim() || null,
    address_number: document.getElementById('cust-number').value.trim() || null,
    address_district: document.getElementById('cust-district').value.trim() || null,
    address_city: document.getElementById('cust-city').value.trim() || null,
    address_state: document.getElementById('cust-state').value.trim().toUpperCase() || null,
  };
  if (!payload.name) { showAlert('Informe o nome do cliente.'); return; }

  const resp = await fetch('/api/customers', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Cliente criado.', true);
  ['cust-name', 'cust-document', 'cust-phone', 'cust-email', 'cust-street', 'cust-number', 'cust-district', 'cust-city', 'cust-state']
    .forEach(id => document.getElementById(id).value = '');
  loadCustomers();
});

async function deleteCustomer(id) {
  if (!confirm('Remover este cliente?')) return;
  const resp = await fetch(`/api/customers/${id}`, { method: 'DELETE' });
  const data = await resp.json();
  if (!resp.ok) { showAlert(data.error); return; }
  showAlert('Cliente removido.', true);
  loadCustomers();
}

// ---------- auditoria ----------

async function loadAuditLogs() {
  const resp = await fetch('/api/audit/logs');
  if (!resp.ok) return; // usuario sem permissao (nao-admin); aba fica vazia silenciosamente
  const data = await resp.json();
  const tbody = document.querySelector('#audit-table tbody');
  tbody.innerHTML = data.logs.map(log => `
    <tr>
      <td>${new Date(log.timestamp).toLocaleString('pt-BR')}</td>
      <td>${log.user_name || 'Sistema'}</td>
      <td>${log.action}</td>
      <td>${log.details || ''}</td>
    </tr>
  `).join('') || '<tr><td colspan="4" style="color:var(--muted)">Nenhum registro ainda.</td></tr>';
}

// ---------- init ----------

loadProducts();
loadLocations();
loadCustomers();
loadQuotes();
loadOrders();
loadSuppliers();
loadPurchaseOrders();
loadPayables();
loadCarrierSelects();
loadVehiclesAndDrivers();
loadDeliveries();
loadAuditLogs();
