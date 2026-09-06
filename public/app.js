const API_BASE = '/api';
let jwtToken = localStorage.getItem('nibss_token');

// DOM Elements
const loginSection = document.getElementById('login-section');
const dashboardSection = document.getElementById('dashboard-section');
const navFintechInfo = document.getElementById('nav-fintech-info');
const fintechNameEl = document.getElementById('fintech-name');
const fintechBankCodeEl = document.getElementById('fintech-bank-code');

// Check initial auth state
if (jwtToken) {
  showDashboard();
}

// ─── LOGIN ────────────────────────────────────────────────────────────────
document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const apiKey = document.getElementById('api-key').value;
  const apiSecret = document.getElementById('api-secret').value;
  const errorEl = document.getElementById('login-error');
  
  errorEl.classList.add('hidden');

  try {
    const res = await fetch(`${API_BASE}/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ apiKey, apiSecret })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.message || 'Login failed');

    jwtToken = data.token;
    localStorage.setItem('nibss_token', jwtToken);
    
    // Store basic info for display
    localStorage.setItem('nibss_fintech_name', data.fintech.name);
    localStorage.setItem('nibss_fintech_code', data.fintech.bankCode);

    showDashboard();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  }
});

// ─── LOGOUT ───────────────────────────────────────────────────────────────
document.getElementById('logout-btn').addEventListener('click', () => {
  localStorage.removeItem('nibss_token');
  jwtToken = null;
  loginSection.classList.remove('hidden');
  dashboardSection.classList.add('hidden');
  navFintechInfo.classList.add('hidden');
});

// ─── UI STATE ─────────────────────────────────────────────────────────────
function showDashboard() {
  loginSection.classList.add('hidden');
  dashboardSection.classList.remove('hidden');
  navFintechInfo.classList.remove('hidden');
  
  fintechNameEl.textContent = localStorage.getItem('nibss_fintech_name') || 'Fintech';
  fintechBankCodeEl.textContent = localStorage.getItem('nibss_fintech_code') || '000';
  
  fetchAccounts();
}

function showMessage(elId, msg, isError = false) {
  const el = document.getElementById(elId);
  el.textContent = msg;
  el.className = 'form-msg ' + (isError ? 'error-msg' : 'success-msg');
  setTimeout(() => el.textContent = '', 4000);
}

// ─── FETCH ACCOUNTS ───────────────────────────────────────────────────────
async function fetchAccounts() {
  try {
    const res = await fetch(`${API_BASE}/accounts`, {
      headers: { 'Authorization': `Bearer ${jwtToken}` }
    });
    
    if (res.status === 401) {
      document.getElementById('logout-btn').click(); // Token expired
      return;
    }
    
    const data = await res.json();
    const tbody = document.getElementById('accounts-table-body');
    const select = document.getElementById('transfer-from');
    
    tbody.innerHTML = '';
    select.innerHTML = '<option value="" disabled selected>Select Account</option>';

    data.accounts.forEach(acc => {
      // Add to table
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${acc.accountName}</strong></td>
        <td><code>${acc.accountNumber}</code></td>
        <td>₦${acc.balance.toLocaleString()}</td>
      `;
      tbody.appendChild(tr);

      // Add to transfer dropdown
      const opt = document.createElement('option');
      opt.value = acc.accountNumber;
      opt.textContent = `${acc.accountName} (₦${acc.balance})`;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error('Failed to fetch accounts', err);
  }
}

document.getElementById('refresh-accounts-btn').addEventListener('click', fetchAccounts);

// ─── CREATE ACCOUNT ───────────────────────────────────────────────────────
document.getElementById('create-account-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const kycType = document.getElementById('kyc-type').value;
  const kycID = document.getElementById('kyc-id').value;
  const dob = document.getElementById('kyc-dob').value;
  
  try {
    const res = await fetch(`${API_BASE}/account/create`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwtToken}`
      },
      body: JSON.stringify({ kycType, kycID, dob })
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || 'Creation failed');
    
    showMessage('create-msg', `Success! Acc: ${data.accountNumber}`);
    document.getElementById('create-account-form').reset();
    fetchAccounts();
  } catch (err) {
    showMessage('create-msg', err.message, true);
  }
});

// ─── TRANSFER FUNDS ───────────────────────────────────────────────────────
document.getElementById('transfer-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const from = document.getElementById('transfer-from').value;
  const to = document.getElementById('transfer-to').value;
  const amount = document.getElementById('transfer-amount').value;
  
  try {
    const res = await fetch(`${API_BASE}/transfer`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwtToken}`
      },
      body: JSON.stringify({ from, to, amount })
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || 'Transfer failed');
    
    showMessage('transfer-msg', `Success! TSQ: ${data.transactionId}`);
    document.getElementById('transfer-form').reset();
    fetchAccounts(); // Update balances
  } catch (err) {
    showMessage('transfer-msg', err.message, true);
  }
});
