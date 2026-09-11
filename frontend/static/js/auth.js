async function requireAuth() {
  const resp = await fetch('/api/auth/me');
  const data = await resp.json();
  if (!data.user) {
    window.location.href = '/login.html';
    return null;
  }
  const nameEl = document.getElementById('current-user-name');
  if (nameEl) nameEl.textContent = data.user.name + ' (' + data.user.role + ')';
  return data.user;
}

function setupLogout() {
  const btn = document.getElementById('logout-btn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login.html';
  });
}

document.addEventListener('DOMContentLoaded', () => {
  requireAuth();
  setupLogout();
});
