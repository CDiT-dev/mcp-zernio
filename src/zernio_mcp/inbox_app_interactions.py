INBOX_JS_INTERACTIONS = """\
(function() {
  'use strict';

  // =========================================================================
  // 1. Context Menu (Desktop Right-Click)
  // =========================================================================

  let contextMenu = null;

  function showContextMenu(e, item) {
    e.preventDefault();
    hideContextMenu();

    const menu = document.createElement('div');
    menu.className = 'context-menu';
    menu.style.left = e.clientX + 'px';
    menu.style.top = e.clientY + 'px';

    const actions = [];

    // Group 1: Reply actions
    actions.push({ icon: ICONS.arrowLeft, label: 'Reply', action: () => { navigate('/inbox/conv/' + item.id); focusReply(); } });
    if (item.type === 'comment') {
      actions.push({ icon: ICONS.lock, label: 'Private Reply', action: () => replyPrivate(item) });
      actions.push({ icon: ICONS.heart, label: 'Like', action: () => doAction('like', item) });
    }

    actions.push('divider');

    // Group 2: Management
    actions.push({ icon: ICONS.check, label: item.unread ? 'Mark as Read' : 'Mark as Unread', action: () => doAction(item.unread ? 'read' : 'unread', item) });
    actions.push({ icon: ICONS.archive, label: 'Archive', action: () => doAction('archive', item) });
    actions.push({ icon: ICONS.externalLink, label: 'Open in ' + platformName(item.platform), action: () => openInApp(item) });

    if (item.type === 'comment') {
      actions.push('divider');
      // Group 3: Moderation
      actions.push({ icon: ICONS.eyeOff || ICONS.x, label: item.hidden ? 'Unhide Comment' : 'Hide Comment', action: () => doAction(item.hidden ? 'unhide' : 'hide', item), muted: true });
      actions.push({ icon: ICONS.x, label: 'Delete Comment', action: () => confirmDelete(item), destructive: true });
    }

    actions.forEach(a => {
      if (a === 'divider') {
        menu.appendChild(Object.assign(document.createElement('div'), { className: 'context-divider' }));
        return;
      }
      const row = document.createElement('div');
      row.className = 'context-item' + (a.destructive ? ' destructive' : '') + (a.muted ? ' muted' : '');
      row.innerHTML = a.icon + '<span>' + a.label + '</span>';
      row.addEventListener('click', () => { hideContextMenu(); a.action(); });
      menu.appendChild(row);
    });

    document.body.appendChild(menu);
    contextMenu = menu;

    // Reposition if off-screen
    const rect = menu.getBoundingClientRect();
    if (rect.right > window.innerWidth) menu.style.left = (e.clientX - rect.width) + 'px';
    if (rect.bottom > window.innerHeight) menu.style.top = (e.clientY - rect.height) + 'px';
  }

  function hideContextMenu() {
    if (contextMenu) { contextMenu.remove(); contextMenu = null; }
  }

  document.addEventListener('click', hideContextMenu);
  document.addEventListener('contextmenu', (e) => {
    const convItem = e.target.closest('.conv-item');
    if (convItem) {
      const item = state.items.find(i => i.id === convItem.dataset.id);
      if (item) showContextMenu(e, item);
      return;
    }

    const msgBubble = e.target.closest('.message.outgoing .message-bubble');
    if (msgBubble) {
      const msgEl = msgBubble.closest('.message');
      showMessageContextMenu(e, msgEl.dataset.msgId);
      return;
    }
  });

  function showMessageContextMenu(e, messageId) {
    e.preventDefault();
    hideContextMenu();

    const menu = document.createElement('div');
    menu.className = 'context-menu';
    menu.style.left = e.clientX + 'px';
    menu.style.top = e.clientY + 'px';

    const editRow = document.createElement('div');
    editRow.className = 'context-item';
    editRow.innerHTML = ICONS.pencil + '<span>Edit Message</span>';
    editRow.addEventListener('click', () => { hideContextMenu(); editMessage(messageId); });
    menu.appendChild(editRow);

    const deleteRow = document.createElement('div');
    deleteRow.className = 'context-item destructive';
    deleteRow.innerHTML = ICONS.x + '<span>Delete Message</span>';
    deleteRow.addEventListener('click', () => { hideContextMenu(); confirmDeleteMessage(messageId); });
    menu.appendChild(deleteRow);

    document.body.appendChild(menu);
    contextMenu = menu;
  }

  // =========================================================================
  // 2. Delete Confirmation Dialog
  // =========================================================================

  function confirmDelete(item) {
    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';

    overlay.innerHTML = '<div class="dialog">' +
      '<h3>Delete this ' + escapeHtml(item.type) + '?</h3>' +
      '<p>This will permanently remove it from the platform. This action cannot be undone.</p>' +
      '<div class="dialog-actions">' +
        '<button class="btn-outline" id="cancelDelete">Cancel</button>' +
        '<button class="btn-destructive" id="confirmDeleteBtn">Delete</button>' +
      '</div>' +
    '</div>';

    document.body.appendChild(overlay);

    overlay.querySelector('#cancelDelete').addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
    overlay.querySelector('#confirmDeleteBtn').addEventListener('click', () => {
      overlay.remove();
      doAction('delete', item);
    });

    // Focus trap
    overlay.querySelector('#cancelDelete').focus();
  }

  // =========================================================================
  // 3. Toast / Snackbar
  // =========================================================================

  let currentToast = null;
  let toastTimeout = null;

  function showToast(message, type, undoAction) {
    type = type || 'success';
    undoAction = undoAction || null;
    if (currentToast) currentToast.remove();
    clearTimeout(toastTimeout);

    const toast = document.createElement('div');
    toast.className = 'toast' + (type === 'error' ? ' toast-error' : '');
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');

    let html = '<span class="toast-message">' + escapeHtml(message) + '</span>';
    if (undoAction) {
      html += '<button class="toast-undo">Undo</button>';
    }
    toast.innerHTML = html;

    if (undoAction) {
      toast.querySelector('.toast-undo').addEventListener('click', () => {
        undoAction();
        toast.remove();
        currentToast = null;
        showToast('Undone');
      });
    }

    toast.addEventListener('click', (e) => {
      if (!e.target.closest('.toast-undo')) {
        toast.remove();
        currentToast = null;
      }
    });

    document.body.appendChild(toast);
    currentToast = toast;

    // Animate in
    requestAnimationFrame(() => toast.classList.add('toast-visible'));

    toastTimeout = setTimeout(() => {
      toast.classList.remove('toast-visible');
      setTimeout(() => { toast.remove(); currentToast = null; }, 200);
    }, 5000);
  }

  // Integration point: doAction() in the core JS should call toastForAction(action, item)
  // after successfully performing an action, to show feedback to the user.
  function toastForAction(action, item) {
    const msgs = {
      archive: { msg: 'Conversation archived', undo: () => doAction('unarchive', item) },
      read: { msg: 'Marked as read', undo: () => doAction('unread', item) },
      unread: { msg: 'Marked as unread', undo: () => doAction('read', item) },
      hide: { msg: 'Comment hidden', undo: () => doAction('unhide', item) },
      delete: { msg: item.type + ' deleted', undo: null },
      like: { msg: 'Liked', undo: null },
      follow: { msg: 'Following @' + (item.participant?.username || ''), undo: null },
    };
    const t = msgs[action] || { msg: 'Done', undo: null };
    showToast(t.msg, 'success', t.undo);
  }
  window.toastForAction = toastForAction;

  // =========================================================================
  // 4. Mobile Swipe Actions
  // =========================================================================

  if ('ontouchstart' in window) {
    let touchStartX = 0;
    let touchCurrentX = 0;
    let swipingItem = null;
    let swipeRevealed = null;

    document.addEventListener('touchstart', (e) => {
      const item = e.target.closest('.conv-item');
      if (!item) return;

      // Close any previously revealed swipe
      if (swipeRevealed && swipeRevealed !== item) {
        swipeRevealed.style.transform = '';
        const sa = swipeRevealed.querySelector('.swipe-actions');
        if (sa) sa.remove();
        swipeRevealed = null;
      }

      touchStartX = e.touches[0].clientX;
      swipingItem = item;
    });

    document.addEventListener('touchmove', (e) => {
      if (!swipingItem) return;
      touchCurrentX = e.touches[0].clientX;
      const diff = touchStartX - touchCurrentX;

      if (diff > 20) { // Swiping left
        e.preventDefault();
        const translate = Math.min(diff, 280);
        swipingItem.style.transform = 'translateX(-' + translate + 'px)';

        // Create swipe actions if not already present
        if (!swipingItem.querySelector('.swipe-actions')) {
          const actions = document.createElement('div');
          actions.className = 'swipe-actions';
          actions.innerHTML =
            '<button class="swipe-btn swipe-read" data-action="read">' + ICONS.check + '<span>Read</span></button>' +
            '<button class="swipe-btn swipe-archive" data-action="archive">' + ICONS.archive + '<span>Archive</span></button>' +
            '<button class="swipe-btn swipe-private" data-action="private">' + ICONS.lock + '<span>Private</span></button>' +
            '<button class="swipe-btn swipe-delete" data-action="delete">' + ICONS.x + '<span>Delete</span></button>';
          swipingItem.style.position = 'relative';
          swipingItem.appendChild(actions);

          // Swipe action click handlers
          actions.addEventListener('click', (ev) => {
            const btn = ev.target.closest('.swipe-btn');
            if (!btn) return;
            const action = btn.dataset.action;
            const itemData = state.items.find(i => i.id === swipingItem.dataset.id);
            if (action === 'delete') {
              confirmDelete(itemData);
            } else if (action === 'private') {
              navigate('/inbox/conv/' + itemData.id);
              // TODO: open private reply mode
            } else {
              doAction(action, itemData);
            }
            // Reset swipe
            swipingItem.style.transform = '';
            const sa2 = swipingItem.querySelector('.swipe-actions');
            if (sa2) sa2.remove();
            swipeRevealed = null;
          });
        }
      }
    }, { passive: false });

    document.addEventListener('touchend', () => {
      if (!swipingItem) return;
      const diff = touchStartX - touchCurrentX;

      if (diff > 140) {
        // Snap open
        swipingItem.style.transform = 'translateX(-280px)';
        swipeRevealed = swipingItem;
      } else {
        // Snap closed
        swipingItem.style.transform = '';
        const sa = swipingItem.querySelector('.swipe-actions');
        if (sa) sa.remove();
      }
      swipingItem = null;
    });
  }

  // =========================================================================
  // 5. Keyboard Shortcuts (Desktop)
  // =========================================================================

  document.addEventListener('keydown', (e) => {
    // Don't intercept when typing in input/textarea
    if (e.target.matches('input, textarea, [contenteditable]')) return;

    switch(e.key) {
      case 'j': // Next item
        selectNextItem(1);
        break;
      case 'k': // Previous item
        selectNextItem(-1);
        break;
      case 'Enter': // Open selected
        if (state.selectedId && state.view === 'list') {
          navigate('/inbox/conv/' + state.selectedId);
        }
        break;
      case 'Escape': // Back / close menu
        hideContextMenu();
        if (state.view === 'conversation') navigate('/inbox');
        break;
      case 'r': // Reply
        if (state.view === 'conversation') {
          e.preventDefault();
          focusReply();
        }
        break;
      case 'e': // Archive
        if (state.selectedId) {
          const item = state.items.find(i => i.id === state.selectedId);
          if (item) doAction('archive', item);
        }
        break;
      case 'u': // Toggle read
        if (state.selectedId) {
          const item = state.items.find(i => i.id === state.selectedId);
          if (item) doAction(item.unread ? 'read' : 'unread', item);
        }
        break;
      case '?': // Show help
        e.preventDefault();
        showKeyboardHelp();
        break;
    }
  });

  function selectNextItem(direction) {
    const currentIdx = state.items.findIndex(i => i.id === state.selectedId);
    const newIdx = Math.max(0, Math.min(state.items.length - 1, currentIdx + direction));
    if (state.items[newIdx]) {
      state.selectedId = state.items[newIdx].id;
      render();
      // Scroll selected into view
      const el = document.querySelector('.conv-item.selected');
      if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }

  function focusReply() {
    const input = document.getElementById('replyInput');
    if (input) input.focus();
  }

  function showKeyboardHelp() {
    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML =
      '<div class="dialog keyboard-help">' +
        '<h3>Keyboard Shortcuts</h3>' +
        '<div class="shortcut-grid">' +
          '<div class="shortcut"><kbd>j</kbd><span>Next conversation</span></div>' +
          '<div class="shortcut"><kbd>k</kbd><span>Previous conversation</span></div>' +
          '<div class="shortcut"><kbd>Enter</kbd><span>Open conversation</span></div>' +
          '<div class="shortcut"><kbd>Esc</kbd><span>Go back</span></div>' +
          '<div class="shortcut"><kbd>r</kbd><span>Reply</span></div>' +
          '<div class="shortcut"><kbd>e</kbd><span>Archive</span></div>' +
          '<div class="shortcut"><kbd>u</kbd><span>Toggle read/unread</span></div>' +
          '<div class="shortcut"><kbd>?</kbd><span>Show this help</span></div>' +
        '</div>' +
        '<button class="btn-outline" id="closeKeyboardHelp">Close</button>' +
      '</div>';
    document.body.appendChild(overlay);
    overlay.querySelector('#closeKeyboardHelp').addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
    overlay.addEventListener('keydown', (e) => { if (e.key === 'Escape') overlay.remove(); });
  }
  window.showKeyboardHelp = showKeyboardHelp;

  // =========================================================================
  // 6. Dark Mode Toggle
  // =========================================================================

  window.toggleDarkMode = function() {
    state.darkMode = !state.darkMode;
    localStorage.setItem('inbox-dark', state.darkMode);
    document.documentElement.classList.toggle('dark', state.darkMode);
    render();
  };

  // Listen for system preference changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('inbox-dark')) { // Only auto-switch if user hasn't manually set
      state.darkMode = e.matches;
      document.documentElement.classList.toggle('dark', state.darkMode);
      render();
    }
  });

  // =========================================================================
  // 7. Message Hover Actions (Desktop)
  // =========================================================================

  document.addEventListener('mouseover', (e) => {
    const msg = e.target.closest('.message.outgoing');
    if (msg && !msg.querySelector('.msg-actions-btn')) {
      const btn = document.createElement('button');
      btn.className = 'msg-actions-btn';
      btn.innerHTML = ICONS.moreHorizontal;
      btn.addEventListener('click', (ev) => {
        ev.stopPropagation();
        showMessageContextMenu(ev, msg.dataset.msgId);
      });
      msg.querySelector('.message-bubble').appendChild(btn);
    }
  });

  document.addEventListener('mouseout', (e) => {
    const msg = e.target.closest('.message.outgoing');
    if (msg) {
      const btn = msg.querySelector('.msg-actions-btn');
      if (btn && !btn.matches(':hover')) btn.remove();
    }
  });

  // =========================================================================
  // 8. Pull to Refresh (Mobile)
  // =========================================================================

  if ('ontouchstart' in window) {
    let pullStartY = 0;
    let pulling = false;
    const scrollContainer = () => document.querySelector('.conv-list');

    document.addEventListener('touchstart', (e) => {
      const container = scrollContainer();
      if (container && container.scrollTop === 0) {
        pullStartY = e.touches[0].clientY;
        pulling = true;
      }
    });

    document.addEventListener('touchmove', (e) => {
      if (!pulling) return;
      const diff = e.touches[0].clientY - pullStartY;
      if (diff > 60) {
        const indicator = document.querySelector('.pull-indicator');
        if (indicator) indicator.classList.add('visible');
      }
    });

    document.addEventListener('touchend', () => {
      if (!pulling) return;
      pulling = false;
      const indicator = document.querySelector('.pull-indicator');
      if (indicator && indicator.classList.contains('visible')) {
        indicator.textContent = 'Refreshing...';
        loadStream(state.filters).then(() => {
          indicator.classList.remove('visible');
          indicator.textContent = '\\u21bb Pull to refresh \\u00b7 Updated just now';
        });
      }
    });
  }

})();
"""
