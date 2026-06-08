/**
 * SMART URS Chat — HTTP send (reliable) + WebSocket receive (instant).
 * Both customer and provider join ws/chat/{booking_id}/ → same room group.
 */
(function (config) {
    const bookingId = config.bookingId;
    const myRole = config.role;
    const messagesEl = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const chatForm = document.getElementById('chatForm');
    const chatSendBtn = document.getElementById('chatSendBtn');
    const statusEl = document.getElementById('chatStatus');
    const statusText = document.getElementById('chatStatusText');
    const errorBanner = document.getElementById('chatError');

    let lastMessageId = 0;
    let socket = null;
    let pollTimer = null;
    const seenIds = new Set();

    const sendUrl = '/api/chat/' + bookingId + '/send/';
    const pollUrl = '/api/chat/' + bookingId + '/messages/';
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = wsScheme + '://' + window.location.host + '/ws/chat/' + bookingId + '/';

    function log() {
        console.log.apply(console, ['[SMART URS Chat]'].concat(Array.from(arguments)));
    }

    function getCsrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        if (match) return decodeURIComponent(match[1]);
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    function setStatus(state, text) {
        if (!statusEl || !statusText) return;
        statusEl.className = 'chat-status-dot ' + state + ' small';
        statusText.textContent = text;
        log('Status:', state, '-', text);
    }

    function showError(msg) {
        if (!errorBanner) return;
        errorBanner.textContent = msg;
        errorBanner.classList.add('show');
        log('ERROR:', msg);
    }

    function hideError() {
        if (errorBanner) errorBanner.classList.remove('show');
    }

    function scrollToBottom() {
        if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    function appendMessage(msg) {
        if (!msg || !msg.id || seenIds.has(msg.id)) return;
        seenIds.add(msg.id);
        if (msg.id > lastMessageId) lastMessageId = msg.id;

        const isMine = msg.sender_type === myRole;
        const div = document.createElement('div');
        div.className = 'chat-bubble ' + (isMine ? 'mine' : 'theirs');
        div.innerHTML =
            '<div>' + escapeHtml(msg.content) + '</div>' +
            '<div class="chat-meta">' + escapeHtml(msg.sender_name) + ' · ' + escapeHtml(msg.created_at) + '</div>';
        messagesEl.appendChild(div);
        scrollToBottom();
        log('Displayed msg', msg.id, 'from', msg.sender_type);
    }

    function renderHistory(messages) {
        messagesEl.innerHTML = '';
        seenIds.clear();
        lastMessageId = 0;
        (messages || []).forEach(appendMessage);
    }

    function pollMessages(since) {
        const url = since ? pollUrl + '?since=' + since : pollUrl;
        return fetch(url, { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) {
                if (!r.ok) throw new Error('Poll HTTP ' + r.status);
                return r.json();
            })
            .then(function (data) {
                if (!since) renderHistory(data.messages);
                else (data.messages || []).forEach(appendMessage);
            });
    }

    function sendViaHttp(text) {
        log('HTTP send:', text);
        return fetch(sendUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ message: text }),
        })
        .then(function (r) {
            return r.json().then(function (d) { return { ok: r.ok, data: d }; });
        })
        .then(function (res) {
            if (!res.ok || res.data.error) throw new Error(res.data.error || 'Send failed');
            log('HTTP send OK id=', res.data.message.id);
            appendMessage(res.data.message);
        });
    }

    function connectWebSocket() {
        log('Connecting WebSocket:', wsUrl);
        setStatus('connecting', 'Connecting…');

        socket = new WebSocket(wsUrl);

        socket.onopen = function () {
            setStatus('connected', '🟢 Connected');
            log('WebSocket OPEN — room ws/chat/' + bookingId + '/');
        };

        socket.onmessage = function (e) {
            try {
                const data = JSON.parse(e.data);
                log('WS received:', data.type);
                if (data.type === 'history') {
                    renderHistory(data.messages);
                } else if (data.type === 'message') {
                    appendMessage(data.message);
                } else if (data.type === 'error') {
                    showError(data.message);
                }
            } catch (err) {
                log('WS parse error:', err);
            }
        };

        socket.onclose = function (e) {
            setStatus('disconnected', '🔴 Disconnected');
            log('WebSocket CLOSED code=', e.code, '— polling every 1s');
            setTimeout(connectWebSocket, 5000);
        };

        socket.onerror = function () {
            log('WebSocket ERROR');
            showError('WebSocket error — messages still send via HTTP; polling active.');
        };
    }

    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';
        chatSendBtn.disabled = true;
        setStatus('connecting', 'Sending…');

        sendViaHttp(text)
            .then(function () {
                setStatus('connected', '🟢 Connected');
                hideError();
            })
            .catch(function (err) {
                showError('Failed to send: ' + err.message);
                chatInput.value = text;
                setStatus('disconnected', '🔴 Send failed');
            })
            .finally(function () {
                chatSendBtn.disabled = false;
                chatInput.focus();
            });
    });

    // Start: HTTP history first, then WebSocket for instant updates, poll as safety net
    pollMessages()
        .then(function () { connectWebSocket(); })
        .catch(function (err) {
            showError('Load failed: ' + err.message);
            connectWebSocket();
        });

    pollTimer = setInterval(function () {
        pollMessages(lastMessageId).catch(function () {});
    }, 1000);

    log('Chat init booking=', bookingId, 'role=', myRole);
})(window.CHAT_CONFIG);
