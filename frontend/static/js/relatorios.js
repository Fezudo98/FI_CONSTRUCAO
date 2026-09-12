let salesChart, paymentChart, productsChart;

function fmtMoney(v) {
  return 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function defaultDates() {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 30);
  document.getElementById('date-end').value = end.toISOString().slice(0, 10);
  document.getElementById('date-start').value = start.toISOString().slice(0, 10);
}

async function loadDashboard() {
  const date_start = document.getElementById('date-start').value;
  const date_end = document.getElementById('date-end').value;
  const button = document.getElementById('apply-filter-btn');
  const status = document.getElementById('report-status');
  button.disabled = true;
  button.textContent = 'Atualizando…';
  status.hidden = false;
  status.className = 'alert';
  status.textContent = 'Atualizando os indicadores do período…';
  try {
    const resp = await fetch(`/api/reports/dashboard?date_start=${date_start}&date_end=${date_end}`);
    if (!resp.ok) throw new Error('request');
    const data = await resp.json();

  document.getElementById('kpi-revenue').textContent = fmtMoney(data.kpis.revenue);
  document.getElementById('kpi-count').textContent = data.kpis.sale_count;
  document.getElementById('kpi-ticket').textContent = fmtMoney(data.kpis.average_ticket);
  document.getElementById('kpi-profit').textContent = fmtMoney(data.kpis.gross_profit);

  renderSalesChart(data.sales_by_day);
  renderPaymentChart(data.payment_breakdown);
  renderProductsChart(data.top_products);
    if (data.kpis.sale_count) {
      status.hidden = true;
    } else {
      status.className = 'alert ok';
      status.textContent = 'Não há vendas registradas no período selecionado.';
    }
  } catch (_) {
    status.className = 'alert err';
    status.textContent = 'Não foi possível carregar os relatórios. Verifique a conexão e tente novamente.';
  } finally {
    button.disabled = false;
    button.textContent = 'Aplicar';
  }
}

function renderSalesChart(rows) {
  const ctx = document.getElementById('sales-chart');
  const config = {
    type: 'line',
    data: {
      labels: rows.map(r => r.day),
      datasets: [{ label: 'Vendas (R$)', data: rows.map(r => parseFloat(r.total)), borderColor: '#123B5D', backgroundColor: 'rgba(18,59,93,.1)', fill: true, tension: .3 }],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
  };
  if (salesChart) { salesChart.data = config.data; salesChart.update(); } else { salesChart = new Chart(ctx, config); }
}

function renderPaymentChart(rows) {
  const ctx = document.getElementById('payment-chart');
  const labels = { dinheiro: 'Dinheiro', pix: 'Pix', cartao_debito: 'Débito', cartao_credito: 'Crédito', boleto: 'Boleto', transferencia: 'Transferência' };
  const config = {
    type: 'doughnut',
    data: {
      labels: rows.map(r => labels[r.method] || r.method),
      datasets: [{ data: rows.map(r => parseFloat(r.total)), backgroundColor: ['#123B5D', '#F28C28', '#287A4B', '#B93632', '#577A8D', '#945214'] }],
    },
    options: { responsive: true, maintainAspectRatio: false },
  };
  if (paymentChart) { paymentChart.data = config.data; paymentChart.update(); } else { paymentChart = new Chart(ctx, config); }
}

function renderProductsChart(rows) {
  const ctx = document.getElementById('products-chart');
  const config = {
    type: 'bar',
    data: {
      labels: rows.map(r => r.name),
      datasets: [{ label: 'Quantidade vendida', data: rows.map(r => parseFloat(r.quantity)), backgroundColor: '#F28C28' }],
    },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
  };
  if (productsChart) { productsChart.data = config.data; productsChart.update(); } else { productsChart = new Chart(ctx, config); }
}

document.getElementById('apply-filter-btn').addEventListener('click', loadDashboard);

defaultDates();
loadDashboard();
