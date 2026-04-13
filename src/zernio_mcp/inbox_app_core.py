INBOX_JS_CORE = """\
(function() {
  'use strict';

  // ── Lucide SVG Icons ──
  const ICONS = {
    arrowLeft: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>',
    check: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    send: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
    settings: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
    x: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    archive: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="5" x="2" y="3" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/></svg>',
    lock: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    externalLink: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>',
    bell: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
    moreHorizontal: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>',
    pencil: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/></svg>',
    heart: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>',
    repeat: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/></svg>',
    bookmark: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>',
    userPlus: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" x2="19" y1="8" y2="14"/><line x1="22" x2="16" y1="11" y2="11"/></svg>',
    search: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    inbox: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>',
    fileText: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 13H8"/><path d="M16 17H8"/><path d="M16 13h-2"/></svg>',
    chevronDown: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
    sun: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>',
    moon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>',
    alertTriangle: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
    refreshCw: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>',
  };

  // ── State ──
  const state = {
    view: 'list',
    items: [],
    selectedId: null,
    conversation: null,
    messages: [],
    filters: { type: 'all', platform: null, status: null, q: '' },
    unreadCounts: {},
    loading: true,
    error: null,
    darkMode: localStorage.getItem('inbox-dark') === 'true' || window.matchMedia('(prefers-color-scheme: dark)').matches,
  };

  // ── Helpers ──
  function platformColor(platform) {
    const colors = {
      twitter: 'oklch(0.1759 0.0275 161.2531)',
      instagram: 'oklch(0.6088 0.2498 29.2339)',
      linkedin: 'oklch(0.3 0.1 230)',
      bluesky: 'oklch(0.55 0.15 250)',
      facebook: 'oklch(0.45 0.15 260)',
      google: 'oklch(0.7721 0.1727 64.1585)',
      threads: 'oklch(0.1759 0.0275 161.2531)',
      reddit: 'oklch(0.55 0.15 30)',
      pinterest: 'oklch(0.5 0.2 20)',
    };
    return colors[platform] || 'oklch(0.4500 0.0200 161.0)';
  }

  function platformLabel(platform) {
    var labels = { twitter: 'Twitter', instagram: 'IG', linkedin: 'LI', bluesky: 'BSKY', facebook: 'FB', google: 'Google', threads: 'Threads', reddit: 'Reddit', pinterest: 'Pin' };
    return labels[platform] || (platform ? platform.toUpperCase().slice(0, 3) : '');
  }

  function typeLabel(type) {
    return { dm: 'DM', comment: 'Comment', review: 'Review' }[type] || type;
  }

  function relativeTime(iso) {
    var diff = (Date.now() - new Date(iso)) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    if (diff < 604800) return Math.floor(diff / 86400) + 'd ago';
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  function formatTime(iso) {
    return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  }

  function sameDay(a, b) {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  }

  function formatDateSeparator(dateStr) {
    var d = new Date(dateStr);
    var today = new Date();
    var yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    if (sameDay(d, today)) return 'Today';
    if (sameDay(d, yesterday)) return 'Yesterday';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function toastMessage(action, item) {
    var name = item && item.participant ? item.participant.name : 'item';
    var msgs = {
      archive: 'Archived conversation with ' + name,
      read: 'Marked as read',
      unread: 'Marked as unread',
      follow: 'Followed ' + name,
      hide: 'Comment hidden',
      unhide: 'Comment unhidden',
      like: 'Liked',
      delete: 'Deleted',
    };
    return msgs[action] || 'Action completed';
  }

  // ── Toast ──
  function showToast(message, type) {
    type = type || 'success';
    var existing = document.querySelector('.toast');
    if (existing) existing.remove();
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.innerHTML = '<span>' + escapeHtml(message) + '</span><button class="toast-close">' + ICONS.x + '</button>';
    document.body.appendChild(toast);
    toast.querySelector('.toast-close').addEventListener('click', function() { toast.remove(); });
    setTimeout(function() { if (toast.parentNode) toast.remove(); }, 4000);
  }

  // ── API Client ──
  var api = {
    stream: function(filters) {
      var params = new URLSearchParams();
      if (filters.type && filters.type !== 'all') params.set('type', filters.type);
      if (filters.platform) params.set('platform', filters.platform);
      if (filters.status) params.set('status', filters.status);
      if (filters.q) params.set('q', filters.q);
      return fetch('/inbox/api/stream?' + params).then(function(resp) {
        if (!resp.ok) throw new Error('Failed to load inbox');
        return resp.json();
      });
    },
    conversation: function(id, accountId) {
      var url = '/inbox/api/conversations/' + encodeURIComponent(id);
      if (accountId) url += '?accountId=' + encodeURIComponent(accountId);
      return fetch(url).then(function(resp) {
        if (!resp.ok) throw new Error('Failed to load conversation');
        return resp.json();
      });
    },
    reply: function(body) {
      return fetch('/inbox/api/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then(function(resp) {
        if (!resp.ok) throw new Error('Failed to send reply');
        return resp.json();
      });
    },
    action: function(body) {
      return fetch('/inbox/api/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then(function(resp) {
        if (!resp.ok) throw new Error('Action failed');
        return resp.json();
      });
    },
    editMessage: function(messageId, body) {
      return fetch('/inbox/api/message/' + encodeURIComponent(messageId), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then(function(resp) {
        if (!resp.ok) throw new Error('Failed to edit message');
        return resp.json();
      });
    },
    sent: function() {
      return fetch('/inbox/api/sent').then(function(resp) {
        if (!resp.ok) throw new Error('Failed to load sent messages');
        return resp.json();
      });
    },
  };

  // ── Router ──
  function navigate(path, replace) {
    var method = replace ? 'replaceState' : 'pushState';
    history[method](null, '', path);
    route();
  }

  function route() {
    var path = location.pathname;
    if (path.startsWith('/inbox/conv/')) {
      var id = path.split('/inbox/conv/')[1];
      state.view = 'conversation';
      state.selectedId = id;
      loadConversation(id);
    } else if (path === '/inbox/archived') {
      state.view = 'archived';
      loadStream({ type: 'all', platform: state.filters.platform, status: 'archived', q: state.filters.q });
    } else if (path === '/inbox/sent') {
      state.view = 'sent';
      loadSentMessages();
    } else {
      state.view = 'list';
      loadStream(state.filters);
    }
    render();
  }

  window.addEventListener('popstate', route);

  // ── Data Loading ──
  function loadStream(filters) {
    state.loading = true;
    state.error = null;
    render();
    api.stream(filters).then(function(data) {
      state.items = data.items || [];
      state.unreadCounts = data.unreadCounts || {};
      state.loading = false;
      render();
    }).catch(function(e) {
      state.error = e.message;
      state.loading = false;
      render();
    });
  }

  function loadConversation(id) {
    state.loading = true;
    state.error = null;
    render();
    var item = state.items.find(function(i) { return i.id === id; });
    var accountId = item ? item.accountId : '';
    api.conversation(id, accountId).then(function(data) {
      state.conversation = data.conversation;
      state.messages = data.messages || [];
      state.loading = false;
      render();
      scrollMessagesToBottom();
    }).catch(function(e) {
      state.error = e.message;
      state.loading = false;
      render();
    });
  }

  function loadSentMessages() {
    state.loading = true;
    state.error = null;
    render();
    api.sent().then(function(data) {
      state.items = data.items || [];
      state.loading = false;
      render();
    }).catch(function(e) {
      state.error = e.message;
      state.loading = false;
      render();
    });
  }

  function scrollMessagesToBottom() {
    var msgList = document.querySelector('.message-list');
    if (msgList) msgList.scrollTop = msgList.scrollHeight;
  }

  // ── Actions ──
  window.doAction = function(action) {
    var item = state.items.find(function(i) { return i.id === state.selectedId; }) || state.conversation;
    if (!item) return;

    if (action === 'archive') {
      state.items = state.items.filter(function(i) { return i.id !== item.id; });
      render();
    }
    if (action === 'read') {
      var it = state.items.find(function(i) { return i.id === item.id; });
      if (it) { it.unread = false; render(); }
    }

    api.action({
      action: action,
      itemId: item.id,
      itemType: item.type,
      platformData: item.platformData || {},
    }).then(function() {
      showToast(toastMessage(action, item));
    }).catch(function() {
      loadStream(state.filters);
      showToast('Action failed. Please try again.', 'error');
    });
  };

  window.sendReply = function() {
    var input = document.getElementById('replyInput');
    if (!input) return;
    var content = input.value.trim();
    if (!content) return;

    var item = state.conversation;
    if (!item) return;

    var tempMsg = { id: 'temp-' + Date.now(), content: content, sender: 'me', timestamp: new Date().toISOString(), status: 'sending' };
    state.messages.push(tempMsg);
    input.value = '';
    render();
    scrollMessagesToBottom();

    api.reply({
      itemId: item.id,
      itemType: item.type,
      content: content,
      private: false,
      platformData: item.platformData || {},
    }).then(function() {
      tempMsg.status = 'sent';
      showToast('Reply sent');
      render();
    }).catch(function() {
      tempMsg.status = 'failed';
      showToast('Failed to send. Tap to retry.', 'error');
      render();
    });
  };

  window.navigate = navigate;
  window.__inboxState = state;
  window.__inboxRender = function() { render(); };
  window.__inboxLoadStream = function(f) { loadStream(f || state.filters); };
  window.escapeHtml = escapeHtml;
  window.ICONS = ICONS;
  window.platformLabel = platformLabel;

  window.toggleDarkMode = function() {
    state.darkMode = !state.darkMode;
    localStorage.setItem('inbox-dark', state.darkMode);
    render();
  };

  // ── Render ──
  function render() {
    var app = document.getElementById('app');
    if (!app) return;
    document.documentElement.classList.toggle('dark', state.darkMode);

    if (state.view === 'list' || state.view === 'archived' || state.view === 'sent') {
      renderListView(app);
    } else if (state.view === 'conversation') {
      renderConversationView(app);
    }
  }

  function isDesktop() { return window.innerWidth >= 1024; }
  function isMobile() { return window.innerWidth < 768; }

  // ── Skeleton ──
  function renderSkeleton() {
    var html = '';
    for (var i = 0; i < 4; i++) {
      var opacity = i === 3 ? ' style="opacity:0.5"' : '';
      html += '<div class="skeleton-item"' + opacity + '>' +
        '<div class="skeleton-avatar"></div>' +
        '<div class="skeleton-lines">' +
        '<div class="skeleton-line w-60"></div>' +
        '<div class="skeleton-line w-80"></div>' +
        '<div class="skeleton-line w-40"></div>' +
        '</div></div>';
    }
    return html;
  }

  // ── Empty State ──
  function renderEmptyState() {
    return '<div class="empty-state">' +
      '<div class="empty-icon">' + ICONS.check + '</div>' +
      '<h2>All caught up</h2>' +
      '<p>No new messages, comments, or reviews waiting.</p>' +
      '</div>';
  }

  // ── Error State ──
  function renderErrorState() {
    return '<div class="empty-state">' +
      '<div class="empty-icon">' + ICONS.alertTriangle + '</div>' +
      '<h2>Something went wrong</h2>' +
      '<p>' + escapeHtml(state.error) + '</p>' +
      '<button class="btn-primary" onclick="location.reload()">Retry</button>' +
      '</div>';
  }

  // ── Sidebar ──
  function renderSidebar() {
    var counts = state.unreadCounts || {};
    var f = state.filters.type || 'all';
    function navClass(filter) { return 'nav-item' + (f === filter && state.view === 'list' ? ' active' : ''); }
    function countBadge(n) { return n ? ' <span class="nav-count">' + n + '</span>' : ''; }

    return '<div class="sidebar">' +
      '<div class="sidebar-logo">' +
        '<div class="logo-icon">' + ICONS.inbox + '</div>' +
        '<span class="sidebar-title">Inbox</span>' +
      '</div>' +
      '<nav class="sidebar-nav">' +
        '<a class="' + navClass('all') + '" data-filter="all">All Messages' + countBadge(counts.all) + '</a>' +
        '<a class="' + navClass('comment') + '" data-filter="comment">Comments' + countBadge(counts.comment) + '</a>' +
        '<a class="' + navClass('dm') + '" data-filter="dm">Direct Messages' + countBadge(counts.dm) + '</a>' +
        '<a class="' + navClass('review') + '" data-filter="review">Reviews' + countBadge(counts.review) + '</a>' +
        '<div class="nav-divider"></div>' +
        '<a class="nav-item' + (state.view === 'archived' ? ' active' : '') + '" data-filter="archived">' + ICONS.archive + ' Archived</a>' +
        '<a class="nav-item' + (state.view === 'sent' ? ' active' : '') + '" data-filter="sent">' + ICONS.send + ' Sent</a>' +
      '</nav>' +
      '<div class="sidebar-footer">' +
        '<button class="btn-icon" onclick="toggleDarkMode()">' + (state.darkMode ? ICONS.sun : ICONS.moon) + '</button>' +
      '</div>' +
    '</div>';
  }

  // ── Conversation Item ──
  function renderConvItem(item) {
    var selectedClass = item.id === state.selectedId ? ' selected' : '';
    var unreadClass = item.unread ? ' unread' : '';
    var hiddenClass = item.hidden ? ' hidden-item' : '';
    var color = platformColor(item.platform);

    var initials = (item.participant && item.participant.initials) ? escapeHtml(item.participant.initials) : '?';
    var name = (item.participant && item.participant.name) ? escapeHtml(item.participant.name) : 'Unknown';
    var preview = item.preview ? escapeHtml(item.preview) : '';

    return '<div class="conv-item' + unreadClass + selectedClass + hiddenClass + '" data-id="' + escapeHtml(item.id) + '" data-type="' + escapeHtml(item.type || '') + '">' +
      '<div class="conv-avatar" style="background:' + color + '">' + initials + '</div>' +
      '<div class="conv-content">' +
        '<div class="conv-header">' +
          '<span class="conv-name">' + name + '</span>' +
          '<span class="platform-badge" style="background:' + color + '">' + escapeHtml(platformLabel(item.platform)) + '</span>' +
          (item.hidden ? '<span class="status-badge">HIDDEN</span>' : '') +
        '</div>' +
        '<div class="conv-preview">' + preview + '</div>' +
        '<div class="conv-meta">' + relativeTime(item.timestamp) + ' &middot; ' + escapeHtml(typeLabel(item.type)) + '</div>' +
      '</div>' +
      (item.unread ? '<div class="unread-dot"></div>' : '') +
    '</div>';
  }

  // ── Conversation List ──
  function renderConvList() {
    var html = '<div class="conv-list">';
    html += '<div class="conv-list-header">' +
      '<h2 class="conv-list-title">' + listTitle() + '</h2>' +
      '<div class="search-box">' +
        '<span class="search-icon">' + ICONS.search + '</span>' +
        '<input type="text" class="search-input" placeholder="Search..." id="searchInput" value="' + escapeHtml(state.filters.q) + '">' +
      '</div>' +
    '</div>';

    if (state.loading) {
      html += renderSkeleton();
    } else if (state.error) {
      html += renderErrorState();
    } else if (state.items.length === 0) {
      html += renderEmptyState();
    } else {
      html += '<div class="conv-items">';
      state.items.forEach(function(item) {
        html += renderConvItem(item);
      });
      html += '</div>';
    }
    html += '</div>';
    return html;
  }

  function listTitle() {
    if (state.view === 'archived') return 'Archived';
    if (state.view === 'sent') return 'Sent';
    var titles = { all: 'All Messages', dm: 'Direct Messages', comment: 'Comments', review: 'Reviews' };
    return titles[state.filters.type] || 'All Messages';
  }

  // ── Detail Panel (empty) ──
  function renderEmptyDetail() {
    return '<div class="detail-panel empty-detail">' +
      '<div class="empty-state">' +
        '<div class="empty-icon">' + ICONS.inbox + '</div>' +
        '<h2>Select a conversation</h2>' +
        '<p>Choose a message from the list to view it here.</p>' +
      '</div>' +
    '</div>';
  }

  // ── List View ──
  function renderListView(container) {
    var html = '';
    if (isMobile()) {
      html += '<div class="mobile-layout">';
      html += renderMobileHeader();
      html += renderMobileFilterTabs();
      html += renderConvList();
      html += renderMobileBottomNav();
      html += '</div>';
    } else {
      html += '<div class="desktop-layout">';
      html += renderSidebar();
      html += renderConvList();
      html += renderEmptyDetail();
      html += '</div>';
    }
    container.innerHTML = html;
    bindSearchInput();
  }

  // ── Mobile Header ──
  function renderMobileHeader() {
    return '<div class="mobile-header">' +
      '<h1 class="mobile-title">Inbox</h1>' +
      '<div class="mobile-header-actions">' +
        '<button class="btn-icon" onclick="toggleDarkMode()">' + (state.darkMode ? ICONS.sun : ICONS.moon) + '</button>' +
      '</div>' +
    '</div>';
  }

  // ── Mobile Filter Tabs ──
  function renderMobileFilterTabs() {
    var f = state.filters.type || 'all';
    var counts = state.unreadCounts || {};
    function tabClass(filter) { return 'filter-tab' + (f === filter ? ' active' : ''); }
    function badge(n) { return n ? '<span class="tab-badge">' + n + '</span>' : ''; }

    return '<div class="filter-tabs">' +
      '<button class="' + tabClass('all') + '" data-filter="all">All' + badge(counts.all) + '</button>' +
      '<button class="' + tabClass('dm') + '" data-filter="dm">DMs' + badge(counts.dm) + '</button>' +
      '<button class="' + tabClass('comment') + '" data-filter="comment">Comments' + badge(counts.comment) + '</button>' +
      '<button class="' + tabClass('review') + '" data-filter="review">Reviews' + badge(counts.review) + '</button>' +
    '</div>';
  }

  // ── Mobile Bottom Nav ──
  function renderMobileBottomNav() {
    return '<div class="bottom-nav">' +
      '<a class="bottom-nav-item' + (state.view === 'list' ? ' active' : '') + '" data-filter="all">' + ICONS.inbox + '<span>Inbox</span></a>' +
      '<a class="bottom-nav-item' + (state.view === 'archived' ? ' active' : '') + '" data-filter="archived">' + ICONS.archive + '<span>Archived</span></a>' +
      '<a class="bottom-nav-item' + (state.view === 'sent' ? ' active' : '') + '" data-filter="sent">' + ICONS.send + '<span>Sent</span></a>' +
      '<a class="bottom-nav-item" onclick="toggleDarkMode()">' + (state.darkMode ? ICONS.sun : ICONS.moon) + '<span>Theme</span></a>' +
    '</div>';
  }

  // ── Conversation View ──
  function renderConversationView(container) {
    var html = '';
    if (isMobile()) {
      html += '<div class="mobile-layout conversation-full">';
      html += renderConversationDetail();
      html += '</div>';
    } else {
      html += '<div class="desktop-layout">';
      html += renderSidebar();
      html += renderConvList();
      html += '<div class="detail-panel">';
      html += renderConversationDetail();
      html += '</div>';
    }
    container.innerHTML = html;
    bindSearchInput();
    scrollMessagesToBottom();
  }

  // ── Conversation Detail ──
  function renderConversationDetail() {
    if (state.loading) {
      return '<div class="conv-detail"><div class="conv-detail-loading">' + renderSkeleton() + '</div></div>';
    }
    if (state.error) {
      return '<div class="conv-detail">' + renderErrorState() + '</div>';
    }
    var conv = state.conversation;
    if (!conv) {
      return '<div class="conv-detail">' + renderEmptyDetail() + '</div>';
    }

    var color = platformColor(conv.platform);
    var initials = (conv.participant && conv.participant.initials) ? escapeHtml(conv.participant.initials) : '?';
    var name = (conv.participant && conv.participant.name) ? escapeHtml(conv.participant.name) : 'Unknown';
    var username = (conv.participant && conv.participant.username) ? escapeHtml(conv.participant.username) : '';
    var platformName = escapeHtml(platformLabel(conv.platform));
    var platformUrl = conv.platformUrl ? escapeHtml(conv.platformUrl) : '#';
    var replyUsername = (conv.replyAs && conv.replyAs.username) ? escapeHtml(conv.replyAs.username) : username;

    var html = '<div class="conv-detail">';

    // Header
    html += '<div class="conv-detail-header">' +
      '<button class="back-btn mobile-only" onclick="navigate(\\'/inbox\\')">' + ICONS.arrowLeft + '</button>' +
      '<div class="conv-avatar" style="background:' + color + '">' + initials + '</div>' +
      '<div class="conv-detail-info">' +
        '<span class="conv-detail-name">' + name + '</span>' +
        '<span class="conv-detail-meta">@' + username + ' &middot; ' + platformName + ' ' + escapeHtml(typeLabel(conv.type)) + '</span>' +
      '</div>' +
      '<div class="conv-detail-actions">' +
        '<button class="btn-outline" onclick="doAction(\\'read\\')">' + ICONS.check + ' <span class="desktop-only">Mark Read</span></button>' +
        '<button class="btn-outline" onclick="doAction(\\'archive\\')">' + ICONS.archive + ' <span class="desktop-only">Archive</span></button>' +
        (conv.platform === 'twitter' ? '<button class="btn-primary" onclick="doAction(\\'follow\\')">' + ICONS.userPlus + ' <span class="desktop-only">Follow</span></button>' : '') +
        '<a class="btn-outline" href="' + platformUrl + '" target="_blank">' + ICONS.externalLink + ' <span class="desktop-only">Open in ' + platformName + '</span></a>' +
      '</div>' +
    '</div>';

    // Messages
    html += '<div class="message-list">';
    var lastDate = null;
    state.messages.forEach(function(msg) {
      var msgDate = new Date(msg.timestamp).toDateString();
      if (msgDate !== lastDate) {
        lastDate = msgDate;
        html += '<div class="date-separator"><span>' + formatDateSeparator(msg.timestamp) + '</span></div>';
      }
      var msgClass = msg.sender === 'me' ? 'outgoing' : 'incoming';
      var statusText = '';
      if (msg.sender === 'me') {
        if (msg.status === 'sending') statusText = ' &middot; Sending...';
        else if (msg.status === 'failed') statusText = ' &middot; Failed';
        else statusText = ' &middot; Sent';
      }
      var bubbleContent = '';
      // Attachments
      if (msg.attachments && msg.attachments.length > 0) {
        msg.attachments.forEach(function(att) {
          var attType = att.type || 'file';
          var attTitle = (att.payload && att.payload.title) ? att.payload.title : '';
          var attUrl = att.url || (att.payload && att.payload.url) || '';
          if (attType === 'image' || attType === 'photo') {
            bubbleContent += '<img src="' + escapeHtml(attUrl) + '" alt="Image" class="msg-attachment-img" loading="lazy">';
          } else if (attType === 'ig_reel' || attType === 'video' || attType === 'reel') {
            var label = attType === 'ig_reel' ? 'Reel' : 'Video';
            bubbleContent += '<div class="msg-attachment-media">' +
              '<span class="att-type-badge">' + label + '</span>';
            if (attUrl) {
              bubbleContent += '<video class="msg-attachment-video" src="' + escapeHtml(attUrl) + '" ' +
                'controls preload="metadata" playsinline></video>';
            }
            if (attTitle) {
              bubbleContent += '<p class="att-title">' + escapeHtml(attTitle.slice(0, 150)) + (attTitle.length > 150 ? '...' : '') + '</p>';
            }
            bubbleContent += '</div>';
          } else if (attType === 'share' || attType === 'link') {
            bubbleContent += '<div class="msg-attachment-media">' +
              '<span class="att-type-badge">Link</span>' +
              (attTitle ? '<p class="att-title">' + escapeHtml(attTitle.slice(0, 150)) + '</p>' : '') +
              (attUrl ? '<a href="' + escapeHtml(attUrl) + '" target="_blank" class="att-link">Open link</a>' : '') +
            '</div>';
          } else {
            bubbleContent += '<div class="msg-attachment-media">' +
              '<span class="att-type-badge">' + escapeHtml(attType) + '</span>' +
              (attTitle ? '<p class="att-title">' + escapeHtml(attTitle.slice(0, 100)) + '</p>' : '') +
            '</div>';
          }
        });
      }
      // Text content
      if (msg.content) {
        bubbleContent += '<p>' + escapeHtml(msg.content) + '</p>';
      }
      // Fallback if completely empty
      if (!bubbleContent) {
        bubbleContent = '<p class="msg-empty">[Message]</p>';
      }

      html += '<div class="message ' + msgClass + (msg.status === 'failed' ? ' failed' : '') + '">' +
        '<div class="message-bubble">' + bubbleContent + '</div>' +
        '<span class="message-time">' + formatTime(msg.timestamp) + statusText + '</span>' +
      '</div>';
    });
    html += '</div>';

    // Reply composer
    html += '<div class="reply-composer">' +
      '<div class="reply-input-row">' +
        '<textarea class="reply-input" placeholder="Type your reply..." id="replyInput"></textarea>' +
        '<button class="btn-send" onclick="sendReply()">' +
          '<span class="desktop-only">Send</span>' +
          '<span class="mobile-only">' + ICONS.send + '</span>' +
        '</button>' +
      '</div>' +
      '<div class="reply-meta">' +
        '<span>Replying as @' + replyUsername + ' on ' + platformName + '</span>' +
      '</div>' +
    '</div>';

    html += '</div>';
    return html;
  }

  // ── Search Binding ──
  function bindSearchInput() {
    var input = document.getElementById('searchInput');
    if (!input) return;
    var timeout;
    input.addEventListener('input', function() {
      clearTimeout(timeout);
      var val = input.value;
      timeout = setTimeout(function() {
        state.filters.q = val;
        loadStream(state.filters);
      }, 300);
    });
  }

  // ── Reply on Enter ──
  document.addEventListener('keydown', function(e) {
    if (e.target && e.target.id === 'replyInput' && e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendReply();
    }
  });

  // ── Event Delegation ──
  document.addEventListener('click', function(e) {
    var app = document.getElementById('app');
    if (!app || !app.contains(e.target)) return;

    var convItem = e.target.closest('.conv-item');
    if (convItem) {
      navigate('/inbox/conv/' + convItem.dataset.id);
      return;
    }

    var navItem = e.target.closest('.nav-item');
    if (navItem) {
      var filter = navItem.dataset.filter;
      if (filter === 'archived') { navigate('/inbox/archived'); return; }
      if (filter === 'sent') { navigate('/inbox/sent'); return; }
      state.filters.type = filter || 'all';
      state.view = 'list';
      navigate('/inbox', true);
      return;
    }

    var filterTab = e.target.closest('.filter-tab');
    if (filterTab) {
      var tabFilter = filterTab.dataset.filter;
      state.filters.type = tabFilter || 'all';
      loadStream(state.filters);
      return;
    }

    var platformChip = e.target.closest('.platform-chip');
    if (platformChip) {
      var pf = platformChip.dataset.platform;
      state.filters.platform = state.filters.platform === pf ? null : pf;
      loadStream(state.filters);
      return;
    }

    var bottomNavItem = e.target.closest('.bottom-nav-item');
    if (bottomNavItem) {
      var bnFilter = bottomNavItem.dataset.filter;
      if (bnFilter === 'archived') { navigate('/inbox/archived'); return; }
      if (bnFilter === 'sent') { navigate('/inbox/sent'); return; }
      if (bnFilter === 'all') { state.filters.type = 'all'; navigate('/inbox', true); return; }
    }
  });

  // ── Resize Listener ──
  var resizeTimeout;
  window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() { render(); }, 150);
  });

  // ── Polling ──
  var pollInterval;

  function pollFn() {
    if (document.hidden) return;
    api.stream(state.filters).then(function(data) {
      var newKeys = (data.items || []).map(function(i) { return i.id + i.timestamp; }).join(',');
      var oldKeys = state.items.map(function(i) { return i.id + i.timestamp; }).join(',');
      if (newKeys !== oldKeys) {
        state.items = data.items || [];
        state.unreadCounts = data.unreadCounts || {};
        render();
      }
    }).catch(function() { /* silent poll failure */ });
  }

  function startPolling() {
    pollInterval = setInterval(pollFn, 15000);
  }

  document.addEventListener('visibilitychange', function() {
    clearInterval(pollInterval);
    var interval = document.hidden ? 60000 : 15000;
    pollInterval = setInterval(pollFn, interval);
  });

  // ── Init ──
  document.addEventListener('DOMContentLoaded', function() {
    if (state.darkMode) document.documentElement.classList.add('dark');
    route();
    startPolling();
  });

})();
"""
