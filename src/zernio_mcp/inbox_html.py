"""HTML shell + CSS for the universal inbox SPA. CDiT Design System 2026."""

INBOX_LOGIN_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Sign In — Zernio Inbox</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Space+Mono:wght@400&display=swap" rel="stylesheet">
<style>
:root {
  --bg: oklch(0.9923 0.0104 91.4994);
  --fg: oklch(0.1759 0.0275 161.2531);
  --card: oklch(1.0 0 0);
  --primary: oklch(0.5687 0.1498 151.938);
  --primary-fg: oklch(1.0 0 0);
  --destructive: oklch(0.5799 0.2380 29.2339);
  --muted-fg: oklch(0.4500 0.0200 161.0);
  --border: oklch(0 0 0);
  --shadow: 4px 4px 0px 0px oklch(0 0 0);
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html {
  font-family: 'Montserrat', sans-serif;
  background: var(--bg);
  color: var(--fg);
  min-height: 100dvh;
}
body {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  padding: 20px;
}
.login-card {
  background: var(--card);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  padding: 40px 32px;
  max-width: 420px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}
.logo-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-icon {
  width: 36px; height: 36px;
  background: var(--primary);
  display: flex; align-items: center; justify-content: center;
}
.logo-icon span {
  font-size: 18px; font-weight: 700; color: var(--primary-fg);
}
.logo-text {
  font-size: 22px; font-weight: 600;
}
.login-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.login-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid var(--border);
  font-family: inherit;
  font-size: 15px;
  outline: none;
  background: var(--card);
}
.login-input:focus {
  box-shadow: 0 0 0 2px var(--primary);
}
.btn-login {
  width: 100%;
  padding: 12px;
  background: var(--primary);
  color: var(--primary-fg);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  font-family: inherit;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.1s;
}
.btn-login:active { transform: translate(2px, 2px); box-shadow: none; }
.btn-login:disabled { opacity: 0.5; cursor: not-allowed; }
.error-msg {
  color: var(--destructive);
  font-size: 13px;
  font-weight: 500;
  display: none;
  text-align: center;
}
.error-msg.visible { display: block; }
.divider {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  color: var(--muted-fg);
  font-size: 13px;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
  opacity: 0.15;
}
.btn-magic {
  width: 100%;
  padding: 12px;
  background: var(--card);
  color: var(--fg);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.1s;
}
.btn-magic:active { transform: translate(2px, 2px); box-shadow: none; }
.btn-magic:disabled { opacity: 0.5; cursor: not-allowed; }
.success-msg {
  color: var(--primary);
  font-size: 13px;
  font-weight: 500;
  display: none;
  text-align: center;
}
.success-msg.visible { display: block; }
.magic-section { display: none; width: 100%; }
.magic-section.enabled { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.footer {
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  color: var(--muted-fg);
}
</style>
</head>
<body>
<div class="login-card">
  <div class="logo-row">
    <div class="logo-icon"><span>Z</span></div>
    <span class="logo-text">Zernio Inbox</span>
  </div>

  <form class="login-form" id="loginForm">
    <input type="password" class="login-input" id="passphrase" placeholder="Enter passphrase" autocomplete="current-password" autofocus>
    <button type="submit" class="btn-login" id="loginBtn">Sign In</button>
    <div class="error-msg" id="errorMsg"></div>
  </form>

  <div class="magic-section" id="magicSection">
    <div class="divider">or</div>
    <button type="button" class="btn-magic" id="magicBtn">Email me a magic link</button>
    <div class="success-msg" id="successMsg"></div>
    <span class="footer">__MASKED_EMAIL__</span>
  </div>
</div>

<script>
const magicEnabled = __MAGIC_ENABLED__;

if (magicEnabled) {
  document.getElementById('magicSection').classList.add('enabled');
}

document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('loginBtn');
  const errEl = document.getElementById('errorMsg');
  const input = document.getElementById('passphrase');
  btn.disabled = true;
  errEl.classList.remove('visible');

  try {
    const resp = await fetch('/inbox/auth', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({passphrase: input.value})
    });
    if (resp.ok) {
      window.location.href = '/inbox';
    } else {
      const data = await resp.json();
      errEl.textContent = data.error || 'Invalid passphrase';
      errEl.classList.add('visible');
      input.value = '';
      input.focus();
    }
  } catch (err) {
    errEl.textContent = 'Connection error. Please try again.';
    errEl.classList.add('visible');
  }
  btn.disabled = false;
});

if (magicEnabled) {
  document.getElementById('magicBtn').addEventListener('click', async () => {
    const btn = document.getElementById('magicBtn');
    const successEl = document.getElementById('successMsg');
    const errEl = document.getElementById('errorMsg');
    btn.disabled = true;
    errEl.classList.remove('visible');
    successEl.classList.remove('visible');

    try {
      const resp = await fetch('/inbox/auth/magic', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: '{}'
      });
      const data = await resp.json();
      if (resp.ok) {
        successEl.textContent = data.message || 'Magic link sent! Check your email.';
        successEl.classList.add('visible');
        btn.textContent = 'Link sent!';
      } else {
        errEl.textContent = data.error || 'Failed to send link';
        errEl.classList.add('visible');
        btn.disabled = false;
      }
    } catch (err) {
      errEl.textContent = 'Connection error. Please try again.';
      errEl.classList.add('visible');
      btn.disabled = false;
    }
  });
}
</script>
</body>
</html>
"""

INBOX_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#faf8f0">
<title>Inbox — Zernio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Space+Mono:wght@400;700&family=Lora:ital,wght@0,400;1,400&display=swap" rel="stylesheet">
<style>
/* ================================================================
   CDiT Design System 2026 — MX-Brutalist Tokens
   ================================================================ */
:root {
  --bg: oklch(0.9923 0.0104 91.4994);
  --fg: oklch(0.1759 0.0275 161.2531);
  --card: oklch(1.0 0 0);
  --card-fg: oklch(0.1759 0.0275 161.2531);
  --primary: oklch(0.5687 0.1498 151.938);
  --primary-fg: oklch(1.0 0 0);
  --secondary: oklch(0.6088 0.2498 29.2339);
  --secondary-fg: oklch(1.0 0 0);
  --accent: oklch(0.7721 0.1727 64.1585);
  --accent-fg: oklch(0.1759 0.0275 161.2531);
  --destructive: oklch(0.5799 0.2380 29.2339);
  --muted: oklch(0.96 0.008 91.5);
  --muted-fg: oklch(0.4500 0.0200 161.0);
  --border: oklch(0 0 0);
  --ring: oklch(0.5687 0.1498 151.938);
  --shadow: 4px 4px 0px 0px oklch(0 0 0);
  --shadow-sm: 4px 4px 0px 0px oklch(0 0 0 / 0.5);
  --radius: 0px;
  --font-sans: 'Montserrat', sans-serif;
  --font-mono: 'Space Mono', monospace;
  --font-serif: 'Lora', serif;
  --letter-spacing: 0.02em;
  --spacing: 0.25rem;
}

.dark {
  --bg: oklch(0.1649 0.0308 162.2739);
  --fg: oklch(0.9809 0.0260 91.6197);
  --card: oklch(0.2283 0.0445 158.2398);
  --card-fg: oklch(0.9809 0.0260 91.6197);
  --primary: oklch(0.8484 0.2275 151.1487);
  --primary-fg: oklch(0.1649 0.0308 162.2739);
  --secondary: oklch(0.6489 0.2370 26.9728);
  --accent: oklch(0.7951 0.1631 68.6392);
  --destructive: oklch(0.6280 0.2577 29.2339);
  --muted: oklch(0.22 0.035 160);
  --muted-fg: oklch(0.7 0.02 91);
  --border: oklch(0.9809 0.0260 91.6197);
  --ring: oklch(0.7951 0.1631 68.6392);
  --shadow: 4px 4px 0px 0px hsl(45 100% 80% / 1);
  --shadow-sm: 4px 4px 0px 0px hsl(45 100% 80% / 0.5);
  --letter-spacing: 0.04em;
}

/* ================================================================
   Reset & Base
   ================================================================ */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html {
  font-family: var(--font-sans);
  font-size: 16px;
  letter-spacing: var(--letter-spacing);
  color: var(--fg);
  background: var(--bg);
  -webkit-font-smoothing: antialiased;
}

body {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

button { cursor: pointer; font-family: inherit; border: none; background: none; color: inherit; }
a { color: inherit; text-decoration: none; }
input, textarea { font-family: inherit; font-size: inherit; color: inherit; }

/* ================================================================
   Layout — Desktop (3 columns)
   ================================================================ */
#app {
  display: flex;
  height: 100dvh;
  overflow: hidden;
}

.desktop-layout {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--card);
  border-right: 2px solid var(--border);
  padding: 24px 16px;
  gap: 4px;
  overflow-y: auto;
}

.conv-list-panel, .conv-list {
  width: 380px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--card);
  border-right: 2px solid var(--border);
  overflow: hidden;
}

.detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  overflow: hidden;
}

/* ================================================================
   Sidebar
   ================================================================ */
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px 20px;
  border-bottom: 2px solid var(--border);
}

.logo-icon {
  width: 32px; height: 32px;
  background: var(--primary);
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius);
}
.logo-icon svg { width: 16px; height: 16px; color: var(--primary-fg); }

.sidebar-title {
  font-size: 18px; font-weight: 600;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-top: 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  font-size: 14px;
  font-weight: 500;
  color: var(--muted-fg);
  cursor: pointer;
  transition: background 0.15s ease-out;
}
.nav-item svg { width: 16px; height: 16px; flex-shrink: 0; }
.nav-item:hover { background: var(--muted); }
.nav-item.active {
  background: var(--primary);
  color: var(--primary-fg);
  box-shadow: var(--shadow);
}

.nav-count {
  margin-left: auto;
  padding: 2px 8px;
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--muted);
  color: var(--muted-fg);
  border-radius: var(--radius);
}
.nav-item.active .nav-count {
  background: var(--primary-fg);
  color: var(--primary);
}

.nav-divider {
  height: 1px;
  background: var(--border);
  opacity: 0.1;
  margin: 4px 0;
}

.sidebar-footer {
  margin-top: 8px;
  padding: 8px 12px;
}
.btn-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--border);
  background: var(--card);
  cursor: pointer;
  transition: background 0.15s;
  border-radius: var(--radius);
}
.btn-icon:hover { background: var(--muted); }
.btn-icon svg { width: 18px; height: 18px; }

.platform-filters {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
  padding-top: 16px;
  border-top: 2px solid var(--border);
}
.platform-filters-label {
  font-size: 12px; font-weight: 600;
  color: var(--muted-fg);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0 4px;
}
.platform-chips {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 0 4px;
}
.platform-chip {
  padding: 4px 10px;
  border: 2px solid var(--border);
  background: var(--card);
  font-family: var(--font-mono);
  font-size: 11px;
  cursor: pointer;
  transition: background 0.15s;
}
.platform-chip.active {
  background: var(--fg);
  color: var(--card);
}

/* ================================================================
   Search
   ================================================================ */
.search-bar {
  padding: 16px;
  border-bottom: 2px solid var(--border);
}
.search-box {
  position: relative;
  display: flex;
  align-items: center;
}
.search-icon {
  position: absolute;
  left: 10px;
  display: flex;
  align-items: center;
  color: var(--muted-fg);
  pointer-events: none;
}
.search-icon svg { width: 16px; height: 16px; }
.search-input {
  width: 100%;
  padding: 8px 12px 8px 34px;
  border: 2px solid var(--border);
  background: var(--card);
  font-size: 14px;
  outline: none;
  border-radius: var(--radius);
}
.search-input:focus { box-shadow: 0 0 0 2px var(--ring); }
.search-input::placeholder { color: var(--muted-fg); }

/* ================================================================
   Conversation List
   ================================================================ */
.conv-list {
  flex: 1;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.conv-item {
  display: flex;
  padding: 14px 16px;
  gap: 12px;
  background: var(--card);
  border-bottom: 1px solid oklch(0 0 0 / 0.1);
  cursor: pointer;
  transition: background 0.15s;
  position: relative;
}
.conv-item:hover { background: var(--muted); }
.conv-item.selected {
  background: var(--muted);
  border-left: 4px solid var(--primary);
  padding-left: 12px;
}
.conv-item.hidden-item { opacity: 0.4; }
.conv-item.archived-item { opacity: 0.65; }

.conv-avatar {
  width: 40px; height: 40px;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid var(--border);
  font-size: 14px; font-weight: 700;
  color: white;
  border-radius: var(--radius);
}

.conv-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
  min-width: 0;
}

.conv-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.conv-name {
  font-size: 14px;
  font-weight: 400;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-item.unread .conv-name { font-weight: 600; }

.platform-badge {
  padding: 1px 6px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: white;
  text-transform: uppercase;
  white-space: nowrap;
  border-radius: var(--radius);
}

.status-badge {
  padding: 1px 6px;
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--muted-fg);
  text-transform: uppercase;
  border: 1.5px solid var(--muted-fg);
  border-radius: var(--radius);
}

.conv-preview {
  font-size: 13px;
  color: var(--muted-fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-item.unread .conv-preview { color: var(--fg); font-weight: 500; }

.conv-meta {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted-fg);
  font-variant-numeric: tabular-nums;
}

.unread-dot {
  width: 10px; height: 10px;
  background: var(--primary);
  flex-shrink: 0;
  margin-top: 6px;
  border: 2px solid var(--border);
  border-radius: var(--radius);
}

/* ================================================================
   Conversation Detail Header
   ================================================================ */
.conv-detail-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  background: var(--card);
  border-bottom: 2px solid var(--border);
  gap: 12px;
}

.conv-detail-avatar {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid var(--border);
  font-size: 13px; font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.conv-detail-info { display: flex; flex-direction: column; gap: 2px; flex: 1; }
.conv-detail-name { font-size: 16px; font-weight: 600; }
.conv-detail-meta { font-family: var(--font-mono); font-size: 12px; color: var(--muted-fg); }

.conv-detail-actions {
  display: flex; gap: 8px; margin-left: auto;
}

/* ================================================================
   Buttons
   ================================================================ */
.btn-outline {
  padding: 6px 12px;
  border: 2px solid var(--border);
  background: var(--card);
  font-size: 12px; font-weight: 500;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: transform 0.1s;
  border-radius: var(--radius);
}
.btn-outline:active { transform: translate(2px, 2px); box-shadow: none; }

.btn-primary {
  padding: 6px 12px;
  border: 2px solid var(--border);
  background: var(--primary);
  color: var(--primary-fg);
  font-size: 12px; font-weight: 600;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: transform 0.1s;
  border-radius: var(--radius);
}
.btn-primary:active { transform: translate(2px, 2px); box-shadow: none; }

.btn-destructive {
  padding: 8px 16px;
  border: 2px solid var(--border);
  background: var(--destructive);
  color: white;
  font-size: 14px; font-weight: 600;
  box-shadow: var(--shadow);
  cursor: pointer;
  border-radius: var(--radius);
}
.btn-destructive:active { transform: translate(2px, 2px); box-shadow: none; }

.btn-send {
  padding: 10px 20px;
  background: var(--primary);
  color: var(--primary-fg);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  font-size: 14px; font-weight: 600;
  flex-shrink: 0;
  cursor: pointer;
  border-radius: var(--radius);
}
.btn-send:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-send:active:not(:disabled) { transform: translate(2px, 2px); box-shadow: none; }

.back-btn {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
.back-btn svg { width: 20px; height: 20px; }

/* ================================================================
   Conversation Detail + Messages
   ================================================================ */
.conv-detail {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  overflow: hidden;
}

.conv-detail-loading {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 24px;
}

.message-list, .messages-area {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overscroll-behavior: contain;
}

.message {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 480px;
}
.message.outgoing {
  align-self: flex-end;
  align-items: flex-end;
}

.message-bubble {
  padding: 12px 16px;
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  position: relative;
  border-radius: var(--radius);
}
.message.incoming .message-bubble {
  background: var(--card);
  color: var(--card-fg);
}
.message.outgoing .message-bubble {
  background: var(--primary);
  color: var(--primary-fg);
}
.message.failed .message-bubble {
  opacity: 0.6;
}

.message-bubble p {
  font-size: 14px;
  line-height: 1.5;
}

.message-time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted-fg);
  font-variant-numeric: tabular-nums;
}

.message-failed {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
}
.message-failed .fail-text { color: var(--destructive); }
.message-failed .retry-btn {
  padding: 2px 8px;
  border: 2px solid var(--destructive);
  color: var(--destructive);
  font-size: 11px; font-weight: 600;
  cursor: pointer;
  border-radius: var(--radius);
}

.date-separator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  color: var(--muted-fg);
  font-family: var(--font-mono);
  font-size: 11px;
}
.date-separator::before, .date-separator::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
  opacity: 0.15;
}

/* Message sender name (for comment threads) */
.msg-sender-name {
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-sans);
  display: flex;
  align-items: center;
  gap: 4px;
}
.msg-sender-name svg { width: 12px; height: 12px; }

/* Message attachments */
.msg-attachment-img {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
  border: 1px solid var(--border);
  margin-bottom: 4px;
}
.msg-attachment-video {
  max-width: 100%;
  max-height: 280px;
  border: 1px solid var(--border);
  background: oklch(0 0 0);
}
.msg-attachment-media {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 4px 0;
}
.att-link {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--primary);
  text-decoration: underline;
}
.att-type-badge {
  display: inline-block;
  padding: 2px 8px;
  background: var(--muted);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--muted-fg);
  border: 1px solid var(--border);
  align-self: flex-start;
}
.att-title {
  font-size: 13px;
  line-height: 1.4;
  color: inherit;
  opacity: 0.85;
}
.msg-empty {
  color: var(--muted-fg);
  font-style: italic;
}

/* Message hover actions */
.msg-actions-btn {
  position: absolute;
  top: -8px; right: -8px;
  width: 24px; height: 24px;
  background: var(--card);
  border: 2px solid var(--border);
  display: none;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: var(--radius);
}
.msg-actions-btn svg { width: 14px; height: 14px; }
.message.outgoing:hover .msg-actions-btn { display: flex; }

/* ================================================================
   Reply Composer
   ================================================================ */
.reply-composer {
  padding: 16px 24px;
  background: var(--card);
  border-top: 2px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.reply-input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.reply-input {
  flex: 1;
  min-height: 44px;
  max-height: 200px;
  padding: 10px 14px;
  border: 2px solid var(--border);
  background: var(--card);
  resize: vertical;
  outline: none;
  font-size: 14px;
  line-height: 1.5;
  border-radius: var(--radius);
}
.reply-input:focus { box-shadow: 0 0 0 2px var(--ring); }
.reply-input::placeholder { color: var(--muted-fg); }

.reply-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted-fg);
}

/* ================================================================
   Context Menu
   ================================================================ */
.context-menu {
  position: fixed;
  z-index: 1000;
  width: 220px;
  background: var(--card);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  border-radius: var(--radius);
}
.context-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.1s;
}
.context-item:hover { background: var(--muted); }
.context-item svg { width: 16px; height: 16px; flex-shrink: 0; }
.context-item.destructive { color: var(--destructive); }
.context-item.muted { color: var(--muted-fg); }
.context-divider {
  height: 1px;
  background: var(--border);
  opacity: 0.1;
  margin: 0 14px;
}

/* ================================================================
   Swipe Actions (Mobile)
   ================================================================ */
.swipe-actions {
  position: absolute;
  right: 0; top: 0; bottom: 0;
  display: flex;
  z-index: -1;
}
.swipe-btn {
  width: 70px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: none;
  color: white;
  font-size: 10px;
  font-weight: 600;
  font-family: var(--font-sans);
}
.swipe-btn svg { width: 16px; height: 16px; }
.swipe-read { background: var(--primary); }
.swipe-archive { background: var(--accent); color: var(--accent-fg); }
.swipe-private { background: var(--muted-fg); }
.swipe-delete { background: var(--destructive); }

/* ================================================================
   Dialog / Modal
   ================================================================ */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: oklch(0 0 0 / 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}
.dialog {
  background: var(--card);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  padding: 24px;
  max-width: 400px;
  width: 100%;
  border-radius: var(--radius);
}
.dialog h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}
.dialog p {
  font-size: 14px;
  color: var(--muted-fg);
  line-height: 1.5;
  margin-bottom: 16px;
}
.dialog-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* Keyboard help */
.keyboard-help .shortcut-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 16px;
}
.shortcut {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.shortcut kbd {
  padding: 2px 8px;
  background: var(--muted);
  border: 2px solid var(--border);
  font-family: var(--font-mono);
  font-size: 12px;
  min-width: 28px;
  text-align: center;
  border-radius: var(--radius);
}

/* ================================================================
   Toast
   ================================================================ */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%) translateY(20px);
  background: var(--card);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 3000;
  opacity: 0;
  transition: opacity 0.2s ease-out, transform 0.2s ease-out;
  border-radius: var(--radius);
}
.toast.toast-visible {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
.toast-message {
  font-size: 14px;
  font-weight: 500;
}
.toast-undo {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary);
  cursor: pointer;
  background: none;
  border: none;
  font-family: var(--font-sans);
}
.toast-error { border-color: var(--destructive); }

/* ================================================================
   Empty States
   ================================================================ */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  gap: 16px;
  text-align: center;
}
.empty-icon {
  width: 64px; height: 64px;
  background: var(--primary);
  display: flex; align-items: center; justify-content: center;
  border: 2px solid var(--border);
  border-radius: var(--radius);
}
.empty-icon svg { width: 28px; height: 28px; color: var(--primary-fg); }
.empty-state h2 { font-size: 20px; font-weight: 600; }
.empty-state p {
  font-size: 14px;
  color: var(--muted-fg);
  max-width: 360px;
  line-height: 1.5;
}
.empty-actions {
  display: flex; gap: 8px; margin-top: 8px;
}

/* ================================================================
   Loading Skeleton
   ================================================================ */
.skeleton-item {
  display: flex;
  padding: 14px 16px;
  gap: 12px;
  border-bottom: 1px solid oklch(0 0 0 / 0.05);
}
.skeleton-avatar {
  width: 40px; height: 40px;
  background: var(--muted);
  flex-shrink: 0;
  border-radius: var(--radius);
}
.skeleton-lines {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}
.skeleton-line {
  height: 12px;
  background: var(--muted);
  animation: pulse 1.5s ease-in-out infinite;
  border-radius: var(--radius);
}
.skeleton-line.w-40 { width: 40%; }
.skeleton-line.w-60 { width: 60%; }
.skeleton-line.w-80 { width: 80%; }
.skeleton-line.w-100 { width: 100%; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ================================================================
   Error Banner
   ================================================================ */
.error-banner {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--destructive);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  gap: 12px;
  color: white;
}
.error-banner svg { width: 18px; height: 18px; flex-shrink: 0; }
.error-banner span { flex: 1; font-size: 14px; font-weight: 500; }
.error-banner button {
  padding: 6px 14px;
  border: 2px solid white;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border-radius: var(--radius);
}

/* ================================================================
   Notification Opt-in
   ================================================================ */
.notif-optin {
  display: flex;
  padding: 16px;
  background: var(--card);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  gap: 12px;
  align-items: center;
  margin: 8px 16px;
}
.notif-optin-icon {
  width: 40px; height: 40px;
  background: var(--accent);
  display: flex; align-items: center; justify-content: center;
  border: 2px solid var(--border);
  flex-shrink: 0;
  border-radius: var(--radius);
}
.notif-optin-icon svg { width: 20px; height: 20px; color: var(--accent-fg); }
.notif-optin-text { flex: 1; }
.notif-optin-text h4 { font-size: 14px; font-weight: 600; margin-bottom: 2px; }
.notif-optin-text p { font-size: 12px; color: var(--muted-fg); line-height: 1.4; }
.notif-optin-actions { display: flex; flex-direction: column; gap: 4px; flex-shrink: 0; align-items: center; }
.notif-dismiss { font-size: 11px; color: var(--muted-fg); cursor: pointer; }

/* ================================================================
   Review Detail
   ================================================================ */
.review-quote {
  padding: 16px;
  background: var(--card);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  font-family: var(--font-serif);
  font-size: 16px;
  font-style: italic;
  line-height: 1.6;
  color: var(--fg);
  border-radius: var(--radius);
}
.review-stars {
  font-size: 16px;
  color: var(--accent);
}

/* ================================================================
   Quick Actions (Mobile)
   ================================================================ */
.quick-actions {
  display: flex;
  gap: 8px;
  padding: 8px 20px;
  background: var(--card);
  border-top: 1px solid oklch(0 0 0 / 0.1);
  overflow-x: auto;
}
.quick-action-btn {
  padding: 4px 10px;
  border: 2px solid var(--border);
  background: var(--card);
  font-family: var(--font-mono);
  font-size: 11px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  border-radius: var(--radius);
}
.quick-action-btn svg { width: 14px; height: 14px; }
.quick-action-btn.primary {
  background: var(--primary);
  color: var(--primary-fg);
}

/* ================================================================
   Bottom Nav (Mobile)
   ================================================================ */
.bottom-nav {
  display: none;
  align-items: center;
  justify-content: space-around;
  padding: 12px 20px calc(12px + env(safe-area-inset-bottom));
  background: var(--card);
  border-top: 2px solid var(--border);
}
.bottom-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 500;
  color: var(--muted-fg);
  cursor: pointer;
}
.bottom-nav-item.active { color: var(--primary); font-weight: 600; }
.bottom-nav-item svg { width: 20px; height: 20px; }

/* ================================================================
   Mobile Filter Tabs
   ================================================================ */
.filter-tabs {
  display: none;
  gap: 8px;
  padding: 12px 20px;
  background: var(--card);
  border-bottom: 2px solid var(--border);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.filter-tab {
  padding: 6px 14px;
  border: 2px solid var(--border);
  background: var(--card);
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  flex-shrink: 0;
  border-radius: var(--radius);
}
.filter-tab.active {
  background: var(--primary);
  color: var(--primary-fg);
  font-weight: 600;
  box-shadow: var(--shadow);
}

/* ================================================================
   Mobile Header
   ================================================================ */
.mobile-header {
  display: none;
  align-items: center;
  padding: 16px 20px;
  background: var(--card);
  gap: 10px;
}
.mobile-header .logo-icon {
  width: 28px; height: 28px;
}
.mobile-header .sidebar-title {
  font-size: 20px;
}
.mobile-header .settings-btn {
  margin-left: auto;
  width: 36px; height: 36px;
  border: 2px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  background: var(--card);
  cursor: pointer;
  border-radius: var(--radius);
}
.mobile-header .settings-btn svg { width: 18px; height: 18px; }

/* Pull to refresh */
.pull-indicator {
  display: none;
  align-items: center;
  justify-content: center;
  padding: 10px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted-fg);
  background: var(--muted);
  border-bottom: 1px solid oklch(0 0 0 / 0.1);
}
.pull-indicator.visible { display: flex; }

/* ================================================================
   Auth Expired Page
   ================================================================ */
.auth-expired {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  padding: 20px;
}
.auth-expired-card {
  background: var(--card);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  padding: 40px;
  max-width: 480px;
  width: 100%;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  border-radius: var(--radius);
}
.auth-icon-error {
  width: 64px; height: 64px;
  background: var(--destructive);
  display: flex; align-items: center; justify-content: center;
  border: 2px solid var(--border);
  border-radius: var(--radius);
}
.auth-icon-error svg { width: 28px; height: 28px; color: white; }

/* ================================================================
   Responsive — Mobile (< 768px)
   ================================================================ */
@media (max-width: 767px) {
  .sidebar { display: none; }
  .conv-list-panel { width: 100%; border-right: none; }
  .detail-panel { display: none; }
  .mobile-header { display: flex; }
  .filter-tabs { display: flex; }
  .bottom-nav { display: flex; }
  .conv-name { font-size: 15px; }
  .conv-preview { font-size: 14px; }
  .message-bubble p { font-size: 15px; }
  .message { max-width: 300px; }
  .reply-input { min-height: 44px; }
  .btn-send .desktop-only { display: none; }
  .btn-send .mobile-only { display: block; }
  .btn-send { padding: 10px 16px; }
  .conv-detail-actions .btn-outline,
  .conv-detail-actions .btn-primary { font-size: 10px; padding: 6px 10px; }
  .conv-detail-header { padding: 12px 20px; }
  .messages-area { padding: 20px; }
  .reply-composer { padding: 12px 20px calc(12px + env(safe-area-inset-bottom)); }
  .toast { bottom: 80px; }

  /* Mobile: show conversation as full screen */
  body.view-conversation .conv-list-panel { display: none; }
  body.view-conversation .detail-panel { display: flex; }
  body.view-conversation .mobile-header { display: none; }
  body.view-conversation .filter-tabs { display: none; }
  body.view-conversation .bottom-nav { display: none; }
}

/* Tablet (768-1023px) */
@media (min-width: 768px) and (max-width: 1023px) {
  .sidebar { display: none; }
  .conv-list-panel { width: 340px; }
}

/* Desktop */
@media (min-width: 768px) {
  .btn-send .mobile-only { display: none; }
}

/* ================================================================
   Reduced Motion
   ================================================================ */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
</head>
<body>
<div id="app"></div>
<script src="/inbox/app.js?v=__CACHE_BUST__"></script>
</body>
</html>
"""
