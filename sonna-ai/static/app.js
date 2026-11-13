(() => {
  "use strict";

  /* =========================================================
     SONNA AI - Workspace UI  <->  FastAPI backend (main.py)
     Works with the index.html / style.css you sent (same ids).
     ========================================================= */

  // Each section talks to one backend mode: auto | pc | search | rag
  // (mode: null = not connected to a backend endpoint)
  const SECTIONS = [
    { icon: "✦", name: "General Chat", mode: "auto", title: "What are we building today?", intro: "Ask me anything. I decide whether to chat, search the web, or work on your PC." },
    { icon: "◈", name: "Coding Assistant", mode: "auto", title: "Welcome to Coding Assistant", intro: "Share your code or your question and I will help you work through it." },
    { icon: "⌘", name: "Research", mode: "search", title: "Welcome to Research", intro: "Ask a question and I will search the web and summarize what I find." },
    { icon: "▣", name: "PC Assistant", mode: "pc", title: "Welcome to PC Assistant", intro: "Find files, open apps, or check your PC. I ask permission before risky actions." },
    { icon: "☰", name: "Documents", mode: "rag", title: "Welcome to Documents", intro: "Attach PDF, DOCX, TXT or MD files with the + button, then ask about them." },
    { icon: "◎", name: "AI Monitoring", mode: null, title: "Welcome to AI Monitoring", intro: "Live numbers from the tracing log (traces.jsonl): requests, latency, tokens and errors." },
  ];

  // Same limits as the Python backend (main.py / Rag.py)
  const MAX_MESSAGE_CHARS = 4000;
  const MAX_FILE_MB = 50;
  const MAX_AUDIO_MB = 25;
  const ALLOWED_EXTS = [".pdf", ".docx", ".txt", ".md"];
  const HEALTH_INTERVAL_MS = 15000;
  const CONFIRM_POLL_MS = 1000;
  const DEFAULT_CONFIRM_TIMEOUT_S = 60;

  /* ---------------- Elements ---------------- */

  const $ = (sel) => document.querySelector(sel);
  const sectionsEl = $("#sections");
  const titleEl = $("#sectionTitle");
  const welcomeTitle = $("#welcomeTitle");
  const welcomeCopy = $("#welcomeCopy");
  const messagesEl = $("#messages");
  const input = $("#messageInput");
  const attachmentsEl = $("#attachments");
  const loginModal = $("#loginModal");
  const fileInput = $("#fileInput");
  const recBtn = $("#voiceButton");
  const sendBtn = $(".send-btn");
  const composer = $("#composer");
  const statusDot = $(".status-dot");
  const statusText = $(".workspace-card small");
  const composerWrap = $(".composer-wrap");
  const newChatButton = $("#newChatButton");
  const loadChatsButton = $("#loadChatsButton");
  const deleteChatButton = $("#deleteChatButton");
  const MONITORING = "AI Monitoring";
  const MONITORING_REFRESH_MS = 10000;

  /* ---------------- Extra styles (so style.css stays untouched) ---------------- */

  const extraCss = document.createElement("style");
  extraCss.textContent = `
  /* ---------------- Messages ---------------- */

  .message-body {
    white-space: normal;
    overflow-wrap: anywhere;
    line-height: 1.8;
    text-align: start;
    unicode-bidi: plaintext;
  }

  .message.error {
    border-color: #7a2f2e;
    background: #2a1517;
  }

  .message-body p {
    margin: 0 0 12px;
    line-height: 1.8;
  }

  .message-body p:last-child {
    margin-bottom: 0;
  }

  .message-body h1,
  .message-body h2,
  .message-body h3 {
    margin: 16px 0 9px;
    line-height: 1.4;
  }

  .message-body h1 { font-size: 20px; }
  .message-body h2 { font-size: 17px; }
  .message-body h3 { font-size: 15px; }

  .message-body strong {
    color: var(--accent);
    font-weight: 700;
  }

  .message-body em {
    font-style: italic;
  }

  .message-body ul,
  .message-body ol {
    margin: 8px 0 12px;
    padding-inline-start: 24px;
  }

  .message-body li {
    margin: 5px 0;
  }

  .message-body code {
    padding: 2px 6px;
    border-radius: 5px;
    background: #0a0e12;
    border: 1px solid var(--line);
    color: var(--accent);
    font: 12px ui-monospace, monospace;
    direction: ltr;
    unicode-bidi: isolate;
  }

  .message-body pre {
    margin: 12px 0;
    padding: 13px;
    overflow-x: auto;
    border: 1px solid var(--line);
    border-radius: 10px;
    background: #090c10;
    color: #d9e6bd;
    white-space: pre;
    direction: ltr;
    text-align: left;
  }

  .message-body pre code {
    padding: 0;
    border: 0;
    background: transparent;
    color: inherit;
  }

  .message-body blockquote {
    margin: 12px 0;
    padding: 9px 14px;
    border-inline-start: 3px solid var(--accent);
    color: var(--muted);
    background: var(--panel);
    border-radius: 5px;
  }

  /* ---------------- Markdown Tables ---------------- */

  .md-table-wrap {
    direction: rtl;
    overflow-x: auto;
    margin: 14px 0;
    border: 1px solid var(--line);
    border-radius: 10px;
  }

  .md-table-wrap table {
    width: 100%;
    min-width: 420px;
    border-collapse: collapse;
    font-size: 13px;
    line-height: 1.7;
  }

  .md-table-wrap th,
  .md-table-wrap td {
    padding: 10px 12px;
    text-align: start;
    vertical-align: top;
    border-bottom: 1px solid var(--line);
    white-space: normal;
    overflow-wrap: anywhere;
  }

  .md-table-wrap th {
    background: var(--panel-2);
    color: var(--text);
    font-weight: 700;
  }

  .md-table-wrap tr:last-child td {
    border-bottom: 0;
  }

  /* ---------------- Message Extra Information ---------------- */

  .msg-extra {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
  }

  .chip {
    font-size: 10px;
    padding: 3px 8px;
    border-radius: 999px;
    border: 1px solid var(--line);
    color: var(--muted);
  }

  .chip.ok {
    color: var(--accent);
    border-color: #425532;
  }

  .chip.fail {
    color: var(--danger);
    border-color: #7a2f2e;
  }

  /* ---------------- Thinking Animation ---------------- */

  .thinking {
    display: inline-flex;
    gap: 4px;
    padding: 4px 0;
  }

  .thinking i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--muted);
    animation: sonnaDot 1.1s infinite;
  }

  .thinking i:nth-child(2) {
    animation-delay: .18s;
  }

  .thinking i:nth-child(3) {
    animation-delay: .36s;
  }

  @keyframes sonnaDot {
    0%, 80%, 100% { opacity: .25; }
    40% { opacity: 1; }
  }

  /* ---------------- Attachments ---------------- */

  .attachment {
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }

  .attachment button {
    border: 0;
    background: none;
    color: var(--muted);
    padding: 0;
    font-size: 13px;
    line-height: 1;
  }

  .attachment button:hover {
    color: var(--danger);
  }

  .attachment.busy {
    opacity: .6;
  }

  /* ---------------- Composer ---------------- */

  .composer textarea:disabled {
    opacity: .6;
  }

  .send-btn:disabled,
  .voice-btn:disabled {
    opacity: .45;
    cursor: not-allowed;
  }

  /* ---------------- Confirmation Modal ---------------- */

  #confirmTool {
    font-size: 18px;
    margin-bottom: 12px;
  }

  .confirm-args {
    max-height: 180px;
    overflow: auto;
    margin: 0 0 18px;
    padding: 11px;
    border-radius: 9px;
    background: #0c1015;
    border: 1px solid var(--line);
    color: var(--muted);
    font-size: 11px;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .modal-actions {
    display: flex;
    gap: 10px;
  }

  .modal-actions .primary-btn {
    margin-top: 0;
  }

  .ghost-btn {
    flex: 1;
    border: 1px solid var(--line);
    border-radius: 10px;
    background: transparent;
    color: var(--text);
    padding: 12px;
    font-weight: 700;
  }

  .ghost-btn:hover {
    border-color: var(--danger);
    color: var(--danger);
  }

  /* ---------------- AI Monitoring ---------------- */

  .mon {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .mon-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .mon-src {
    color: var(--muted);
    font-size: 11px;
    overflow-wrap: anywhere;
  }

  .mon-refresh {
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--text);
    border-radius: 9px;
    padding: 7px 12px;
    font-size: 12px;
    flex: none;
  }

  .mon-refresh:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  .mon-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
  }

  .mon-card {
    border: 1px solid var(--line);
    background: var(--panel);
    border-radius: 14px;
    padding: 14px;
  }

  .mon-card small {
    display: block;
    color: var(--muted);
    font-size: 10px;
    letter-spacing: .1em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }

  .mon-card b {
    font-size: 22px;
    letter-spacing: -.03em;
  }

  .mon-table-wrap {
    overflow-x: auto;
    border: 1px solid var(--line);
    border-radius: 14px;
  }

  .mon-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }

  .mon-table th,
  .mon-table td {
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid var(--line);
    white-space: nowrap;
  }

  .mon-table th {
    color: var(--muted);
    font-size: 10px;
    letter-spacing: .1em;
  }

  .mon-table td.q {
    white-space: normal;
    max-width: 280px;
    overflow-wrap: anywhere;
  }

  .mon-table tr:last-child td {
    border-bottom: 0;
  }

  .mon-empty {
    color: var(--muted);
    padding: 18px;
    border: 1px dashed var(--line);
    border-radius: 14px;
  }

  .chat-controls {
    display: grid;
    gap: 7px;
    margin: 14px 0 18px;
  }

  .chat-controls button {
    display: flex;
    align-items: center;
    gap: 9px;
    width: 100%;
    padding: 9px 11px;
    border: 1px solid var(--line);
    border-radius: 9px;
    background: var(--panel);
    color: var(--muted);
    cursor: pointer;
    font: inherit;
    font-size: 12px;
    text-align: start;
  }

  .chat-controls button:hover {
    border-color: var(--accent);
    color: var(--text);
    background: var(--panel-2);
  }

  .chat-controls button span:first-child { color: var(--accent); font-size: 15px; }

  .chat-delete {
    margin-inline-start: auto;
    border: 0;
    background: transparent;
    color: var(--muted);
    cursor: pointer;
    font-size: 16px;
  }

  .chat-delete:hover { color: var(--danger); }
  .chat-row {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  min-width: 0;
}

  .chat-row .section-btn {
    flex: 1;
    min-width: 0;
  }

  .chat-row .chat-delete {
    flex: 0 0 28px;
    width: 28px;
    height: 28px;
    display: grid;
    place-items: center;
    margin-inline-start: 0;
    padding: 0;
    border-radius: 7px;
    line-height: 1;
  }

  .clear-chat-btn {
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--muted);
    border-radius: 10px;
    padding: 0 12px;
    height: 36px;
    font-size: 12px;
  }

  .clear-chat-btn:hover {
    border-color: var(--danger);
    color: var(--danger);
  }

  .clear-chat-btn:disabled {
    opacity: .45;
    cursor: not-allowed;
  }
  /* ---------------- Backend Status ---------------- */

  .status-dot.offline {
    background: var(--danger);
    box-shadow: 0 0 12px var(--danger);
  }
`;
  document.head.appendChild(extraCss);

  /* ---------------- State ---------------- */

  let active = SECTIONS[0].name;
  let busy = false;
  let monitoringUnlocked = false;
  let recorder = null;
  let recordChunks = [];
  const histories = {}; // section name -> [{role, text, time, error, steps, sources, route, pending}]

  const cfg = () => SECTIONS.find((s) => s.name === active);
  const nowTime = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const CHAT_STORAGE_KEY = "sonna-chat-histories-v1";

  function saveMessages() {
    try {
      localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(histories));
    } catch {
      /* Storage may be unavailable in private browsing. */
    }
  }

  function loadMessages() {
    try {
      const saved = JSON.parse(localStorage.getItem(CHAT_STORAGE_KEY) || "{}");
      if (saved && typeof saved === "object") Object.assign(histories, saved);
    } catch {
      /* Start with a fresh workspace when stored data is invalid. */
    }
  }

  function createChat() {
  const baseName = `Chat ${new Date().toLocaleDateString("en-US", {
    month: "short",
    day: "numeric"
  })}`;

  let name = baseName;
  let number = 2;

  // Avoid overwriting another chat created on the same day.
  while (histories[name] || SECTIONS.some((section) => section.name === name)) {
    name = `${baseName} (${number++})`;
  }

  histories[name] = [{
    role: "bot",
    text: "New conversation ready. What would you like to build?",
    time: nowTime()
  }];

  SECTIONS.push({
    icon: "＋",
    name,
    mode: "auto",
    title: name,
    intro: "A fresh private conversation."
  });

  saveMessages();
  setActive(name);
}

  function deleteChat(name) {
    const chatName = name || active;
    const section = SECTIONS.find((item) => item.name === chatName);

    // Only user-created chats can be deleted.
    if (!section || section.icon !== "＋" || !histories[chatName]) return;

    if (!window.confirm(`Delete "${chatName}" and all its messages?`)) return;

    delete histories[chatName];

    const index = SECTIONS.findIndex((item) => item.name === chatName);

    if (index >= 0) {
      SECTIONS.splice(index, 1);
    }

    saveMessages();

    if (active === chatName) {
      const fallback =
        SECTIONS.find((item) => item.name === "General Chat") || SECTIONS[0];

      setActive(fallback.name);
    } else {
      renderSections();
    }
  }

  function restoreSavedChats() {
    const builtInNames = new Set(
      SECTIONS.map((section) => section.name)
    );

    Object.keys(histories).forEach((name) => {
      if (name === MONITORING || builtInNames.has(name)) return;

      SECTIONS.push({
        icon: "＋",
        name,
        mode: "auto",
        title: name,
        intro: "A saved conversation."
      });
    });
  }

  /* ---------------- API helper ---------------- */

  function errorText(data, status) {
    const detail = data && (data.detail || data.error);
    if (typeof detail === "string") return detail;
    // FastAPI validation errors (422) come as a list of {msg, loc}
    if (Array.isArray(detail) && detail.length) return detail.map((d) => d.msg || String(d)).join("; ");
    return `Request failed (${status})`;
  }

  async function api(path, options = {}) {
    let res;
    try {
      res = await fetch(path, options);
    } catch {
      throw new Error("Cannot reach the server. Is python main.py running?");
    }
    let data = null;
    try {
      data = await res.json();
    } catch {
      data = null;
    }
    if (!res.ok) throw new Error(errorText(data, res.status));
    return data;
  }

  /* ---------------- Backend status ---------------- */

  async function checkHealth() {
    try {
      await api("/api/health");
      statusDot.classList.remove("offline");
      statusText.textContent = "Online and secure";
    } catch {
      statusDot.classList.add("offline");
      statusText.textContent = "Backend offline";
    }
  }

  /* ---------------- Sections ---------------- */

  function renderSections() {
    sectionsEl.textContent = "";

    SECTIONS.forEach((s) => {
      const isUserChat = s.icon === "＋";

      // Wrapper for chat button and delete button.
      const row = isUserChat ? document.createElement("div") : null;

      if (row) {
        row.className = "chat-row";
      }

      const btn = document.createElement("button");

      btn.className = `section-btn ${s.name === active ? "active" : ""}`;
      btn.dataset.section = s.name;

      btn.innerHTML = '<span class="section-icon"></span><span></span>';

      btn.children[0].textContent = s.icon;
      btn.children[1].textContent = s.name;

      btn.onclick = () => {
        if (s.name === "AI Monitoring" && !monitoringUnlocked) {
          loginModal.hidden = false;
          $("#email").focus();
          return;
        }

        setActive(s.name);
      };

      if (isUserChat) {
        const removeBtn = document.createElement("button");

        removeBtn.type = "button";
        removeBtn.className = "chat-delete";
        removeBtn.textContent = "×";
        removeBtn.title = `Delete ${s.name}`;
        removeBtn.setAttribute("aria-label", `Delete ${s.name}`);

        removeBtn.onclick = () => deleteChat(s.name);

        row.append(btn, removeBtn);
        sectionsEl.appendChild(row);

      } else {
        sectionsEl.appendChild(btn);
      }
    });
  }
  function setActive(name) {
    active = name;
    const s = cfg();
    titleEl.textContent = s.name;
    welcomeTitle.textContent = s.title;
    welcomeCopy.textContent = s.intro;
    if (!histories[name]) histories[name] = [{ role: "bot", text: s.intro, time: nowTime() }];
    renderSections();
    const isMonitoring = name === MONITORING;
    
    composerWrap.hidden = isMonitoring; // the dashboard has no chat box
    clearChatButton.hidden = isMonitoring;
    renderMessages();
    if (isMonitoring) {
      loadMonitoring();
    } else {
      input.placeholder = "Message Sonna...";
      input.focus();
    }
  }

  /* ---------------- Messages ---------------- */

  function renderMarkdown(value) {
  if (!value) return "";

  const html = marked.parse(String(value), {
    gfm: true,
    breaks: true,
  });

  return DOMPurify.sanitize(html);
}
  function buildMessage(msg) {
    const el = document.createElement("div");
    el.className = `message ${msg.role === "user" ? "user" : ""} ${msg.error ? "error" : ""}`;

    const head = document.createElement("small");
    head.textContent = `${msg.role === "user" ? "You" : "Sonna AI"} · ${msg.time}`;
    el.appendChild(head);

    const body = document.createElement("div");
    body.className = "message-body";
    body.dir = "auto";
    if (msg.pending) {
      body.innerHTML = '<span class="thinking" aria-label="Sonna is thinking"><i></i><i></i><i></i></span>';
    } else {
      body.innerHTML = renderMarkdown(msg.text);
    }
    el.appendChild(body);

    const chips = [];
    if (msg.route) chips.push({ text: `route: ${msg.route}`, cls: "ok" });
    (msg.steps || []).forEach((s) =>
      chips.push({
        text: `${s.agent ? s.agent + ": " : ""}${s.tool}${s.ok ? "" : " (failed)"}`,
        cls: s.ok ? "ok" : "fail",
        title: s.error || "",
      })
    );
    (msg.sources || []).forEach((src) =>
      chips.push({ text: src.page ? `${src.file} - p.${src.page}` : src.file, cls: "" })
    );
    if (chips.length) {
      const box = document.createElement("div");
      box.className = "msg-extra";
      chips.forEach((c) => {
        const chip = document.createElement("span");
        chip.className = `chip ${c.cls}`;
        chip.textContent = c.text;
        if (c.title) chip.title = c.title;
        box.appendChild(chip);
      });
      el.appendChild(box);
    }
    return el;
  }

  function renderMessages() {
    if (active === MONITORING) {
      renderMonitoring();
      return;
    }
    messagesEl.textContent = "";
    (histories[active] || []).forEach((m) => messagesEl.appendChild(buildMessage(m)));
    const last = messagesEl.lastElementChild;
    if (last) last.scrollIntoView({ block: "end" });
  }

  function pushBot(text, error = false, section = active) {
    (histories[section] ||= []).push({ role: "bot", text, time: nowTime(), error });
    saveMessages();
    if (section === active) renderMessages();
  }

  function setBusy(value) {
    busy = value;
    input.disabled = value;
    sendBtn.disabled = value;
    recBtn.disabled = value;
    clearChatButton.disabled = value;
  }

  /* ---------------- AI Monitoring (reads /api/monitoring -> traces.jsonl) ---------------- */

  const monitoring = { data: null, error: null, loading: false };

  const fmtMs = (ms) => (ms == null ? "-" : ms >= 1000 ? (ms / 1000).toFixed(1) + " s" : Math.round(ms) + " ms");
  const fmtNum = (n) => Number(n || 0).toLocaleString();

  function h(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  async function loadMonitoring() {
    if (monitoring.loading) return;
    monitoring.loading = true;
    renderMonitoring();
    try {
      monitoring.data = await api("/api/monitoring?limit=50");
      monitoring.error = null;
    } catch (err) {
      monitoring.error =
        err.message === "Not Found"
          ? "The backend has no /api/monitoring endpoint yet. Add monitoring_endpoint.py to main.py."
          : err.message;
    } finally {
      monitoring.loading = false;
      if (active === MONITORING) renderMonitoring();
    }
  }

  function renderMonitoring() {
    messagesEl.textContent = "";
    const wrap = h("div", "mon");

    const head = h("div", "mon-head");
    head.appendChild(h("div", "mon-src", monitoring.data ? `Source: ${monitoring.data.trace_file}` : "Source: traces.jsonl"));
    const refresh = h("button", "mon-refresh", monitoring.loading ? "Loading..." : "Refresh");
    refresh.type = "button";
    refresh.disabled = monitoring.loading;
    refresh.onclick = loadMonitoring;
    head.appendChild(refresh);
    wrap.appendChild(head);

    if (monitoring.error) {
      wrap.appendChild(h("div", "mon-empty", monitoring.error));
    } else if (monitoring.data) {
      const sum = monitoring.data.summary;
      const cards = h("div", "mon-cards");
      [
        ["Requests", fmtNum(sum.requests)],
        ["Success rate", sum.success_rate == null ? "-" : sum.success_rate + "%"],
        ["Avg latency", fmtMs(sum.avg_latency_ms)],
        ["P95 latency", fmtMs(sum.p95_latency_ms)],
        ["Total tokens", fmtNum(sum.total_tokens)],
        ["Errors", fmtNum(sum.errors)],
      ].forEach(([label, value]) => {
        const card = h("div", "mon-card");
        card.append(h("small", "", label), h("b", "", value));
        cards.appendChild(card);
      });
      wrap.appendChild(cards);

      const recent = monitoring.data.recent || [];
      if (!recent.length) {
        wrap.appendChild(h("div", "mon-empty", "No traces yet. Send a PC or Search request first (plain chat and documents are not traced)."));
      } else {
        const tw = h("div", "mon-table-wrap");
        const table = h("table", "mon-table");
        const thead = h("thead");
        const hr = h("tr");
        ["Time", "Agent", "Query", "Latency", "Tokens", "Status"].forEach((c) => hr.appendChild(h("th", "", c)));
        thead.appendChild(hr);
        const tbody = h("tbody");
        recent.forEach((r) => {
          const tr = h("tr");
          tr.appendChild(h("td", "", r.timestamp ? new Date(r.timestamp).toLocaleString() : "-"));
          tr.appendChild(h("td", "", r.agent || "-"));
          const q = h("td", "q", r.query || "");
          q.dir = "auto";
          tr.appendChild(q);
          tr.appendChild(h("td", "", fmtMs(r.latency_ms)));
          tr.appendChild(h("td", "", fmtNum(r.total_tokens)));
          const st = h("td");
          const chip = h("span", `chip ${r.ok ? "ok" : "fail"}`, r.ok ? "ok" : "failed");
          if (r.error) chip.title = r.error;
          if (r.models && r.models.length) tr.title = r.models.join(", ");
          st.appendChild(chip);
          tr.appendChild(st);
          tbody.appendChild(tr);
        });
        table.append(thead, tbody);
        tw.appendChild(table);
        wrap.appendChild(tw);
      }
    } else {
      wrap.appendChild(h("div", "mon-empty", "Loading..."));
    }
    messagesEl.appendChild(wrap);
  }

  setInterval(() => {
    if (active === MONITORING && !document.hidden) loadMonitoring();
  }, MONITORING_REFRESH_MS);

  /* ---------------- Chat ---------------- */

  async function sendMessage(text) {
    const message = text.trim();
    if (!message || busy) return;

    const section = active;
    const s = cfg();

    if (!s.mode) {
      pushBot("This section does not accept messages.", true);
      return;
    }
    if (message.length > MAX_MESSAGE_CHARS) {
      pushBot(`Message is too long (max ${MAX_MESSAGE_CHARS} characters).`, true);
      return;
    }

    const list = (histories[section] ||= []);
    list.push({ role: "user", text: message, time: nowTime() });
    const reply = { role: "bot", text: "", time: nowTime(), pending: true };
    list.push(reply);
    input.value = "";
    input.style.height = "auto";
    renderMessages();

    setBusy(true);
    startConfirmPolling();
    try {
      const data = await api("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          chat_id: s.name,
          mode: s.mode,
        }),
      });
      reply.pending = false;
      if (data.ok && data.answer) {
        reply.text = data.answer;
      } else {
        reply.error = true;
        reply.text = data.error || "Something went wrong.";
      }
      reply.steps = data.steps || [];
      reply.sources = data.sources || [];
      // The route is only interesting when the orchestrator chose it (auto mode)
      if (s.mode === "auto") reply.route = data.route;
    } catch (err) {
      reply.pending = false;
      reply.error = true;
      reply.text = err.message;
    } finally {
      stopConfirmPolling();
      setBusy(false);
      if (section === active) {
        renderMessages();
        input.focus();
      }
    }
  }

  composer.onsubmit = (e) => {
    e.preventDefault();
    sendMessage(input.value);
  };

  input.onkeydown = (e) => {
    // Enter sends, Shift+Enter = new line; ignore Enter while an Arabic/IME word is being composed
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (e.isComposing || e.keyCode === 229) return;
      sendMessage(input.value);
    }
  };

  input.oninput = () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 160) + "px";
  };

  /* ---------------- Permission confirmations (Allow / Deny) ---------------- */

  const confirmEl = document.createElement("div");
  confirmEl.className = "modal-backdrop";
  confirmEl.hidden = true;
  confirmEl.innerHTML =
    '<div class="modal" role="alertdialog" aria-modal="true" aria-labelledby="confirmTool">' +
    '<span class="modal-icon">!</span><p class="eyebrow">PERMISSION NEEDED</p>' +
    '<h2 id="confirmTool"></h2><pre class="confirm-args" id="confirmArgs"></pre>' +
    '<div class="modal-actions"><button type="button" class="ghost-btn" id="confirmDeny">Deny</button>' +
    '<button type="button" class="primary-btn" id="confirmAllow">Allow</button></div></div>';
  document.body.appendChild(confirmEl);

  let confirmTimer = null;
  let activeConfirm = null;
  let confirmDeadline = 0;
  let confirmTimeoutS = DEFAULT_CONFIRM_TIMEOUT_S;
  let polling = false;
  const answeredConfirms = new Set();

  function closeConfirm() {
    confirmEl.hidden = true;
    activeConfirm = null;
  }

  function startConfirmPolling() {
    stopConfirmPolling();
    confirmTimer = setInterval(pollConfirmations, CONFIRM_POLL_MS);
  }

  function stopConfirmPolling() {
    clearInterval(confirmTimer);
    confirmTimer = null;
    closeConfirm();
  }

  function updateCountdown() {
    if (!activeConfirm) return;
    const left = Math.ceil((confirmDeadline - Date.now()) / 1000);
    if (left <= 0) {
      // The backend already treated this request as denied
      answeredConfirms.add(activeConfirm.id);
      closeConfirm();
      return;
    }
    $("#confirmTool").textContent = `${activeConfirm.tool} (${activeConfirm.level}) - ${left}s`;
  }

  async function pollConfirmations() {
    if (activeConfirm) {
      updateCountdown();
      return;
    }
    if (polling) return;
    polling = true;
    try {
      const { items, timeout } = await api("/api/confirm/pending");
      if (timeout) confirmTimeoutS = timeout;
      const next = items.find((i) => !answeredConfirms.has(i.id));
      if (next) {
        activeConfirm = next;
        confirmDeadline = Date.now() + confirmTimeoutS * 1000;
        $("#confirmArgs").textContent = JSON.stringify(next.arguments, null, 2);
        updateCountdown();
        confirmEl.hidden = false;
        $("#confirmDeny").focus();
      }
    } catch {
      /* server busy or offline: try again next tick */
    } finally {
      polling = false;
    }
  }

  async function answerConfirm(approved) {
    const item = activeConfirm;
    if (!item) return;
    answeredConfirms.add(item.id);
    closeConfirm();
    try {
      await api(`/api/confirm/${item.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approved }),
      });
    } catch {
      /* expired: the agent already treated it as denied */
    }
  }

  $("#confirmAllow").onclick = () => answerConfirm(true);
  $("#confirmDeny").onclick = () => answerConfirm(false);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && activeConfirm) answerConfirm(false);
  });

  /* ---------------- Files (the + button uploads to the RAG knowledge base) ---------------- */

  function renderAttachments(files) {
    attachmentsEl.textContent = "";
    files.forEach((f) => {
      const chip = document.createElement("span");
      chip.className = "attachment";
      const label = document.createElement("span");
      label.dir = "auto";
      label.textContent = `${f.file} · ${f.chunks} chunks`;
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "✕";
      remove.setAttribute("aria-label", `Remove ${f.file}`);
      remove.onclick = () => removeFile(f.file);
      chip.append(label, remove);
      attachmentsEl.appendChild(chip);
    });
  }

  async function loadFiles() {
    try {
      const data = await api("/api/rag/files");
      renderAttachments(data.files || []);
    } catch {
      /* offline: keep what is shown */
    }
  }

  async function removeFile(name) {
    try {
      const data = await api(`/api/rag/files/${encodeURIComponent(name)}`, { method: "DELETE" });
      if (data && data.ok === false) pushBot(`${name}: ${data.error || "could not remove file"}`, true);
    } catch (err) {
      pushBot(err.message, true);
    } finally {
      loadFiles();
    }
  }

  $("#fileButton").onclick = () => fileInput.click();

  fileInput.onchange = async () => {
    const picked = [...fileInput.files];
    fileInput.value = "";
    if (!picked.length) return;

    // Same checks as Rag.py, so we do not upload files that would be rejected anyway
    const files = [];
    picked.forEach((f) => {
      const dot = f.name.lastIndexOf(".");
      const ext = dot >= 0 ? f.name.slice(dot).toLowerCase() : "";
      if (!ALLOWED_EXTS.includes(ext)) pushBot(`${f.name}: file type not allowed (${ALLOWED_EXTS.join(", ")})`, true);
      else if (f.size > MAX_FILE_MB * 1024 * 1024) pushBot(`${f.name}: file is larger than ${MAX_FILE_MB} MB`, true);
      else files.push(f);
    });
    if (!files.length) return;

    const body = new FormData();
    files.forEach((f) => body.append("files", f));

    const pending = document.createElement("span");
    pending.className = "attachment busy";
    pending.textContent = "Indexing files...";
    attachmentsEl.appendChild(pending);

    try {
      const { results } = await api("/api/rag/upload", { method: "POST", body });
      const failed = results.filter((r) => !r.ok);
      failed.forEach((r) => pushBot(`${r.name}: ${r.error}`, true));
      const done = results.length - failed.length;
      if (done) pushBot(`${done} file(s) indexed. Open the Documents section and ask about them.`);
    } catch (err) {
      pushBot(err.message, true);
    } finally {
      loadFiles();
    }
  };

  /* ---------------- Voice ---------------- */

  function audioFilename(blob) {
    const type = blob.type || "";
    if (type.includes("mp4")) return "audio.mp4";
    if (type.includes("ogg")) return "audio.ogg";
    if (type.includes("wav")) return "audio.wav";
    return "audio.webm";
  }

  async function transcribe(blob) {
    if (!blob.size) return;
    if (blob.size > MAX_AUDIO_MB * 1024 * 1024) {
      pushBot(`Recording is larger than ${MAX_AUDIO_MB} MB.`, true);
      return;
    }
    const body = new FormData();
    body.append("audio", blob, audioFilename(blob));
    body.append("language", "ar");

    const oldPlaceholder = input.placeholder;
    input.placeholder = "Transcribing...";
    recBtn.disabled = true;
    try {
      const data = await api("/api/voice", { method: "POST", body });
      if (data.ok && data.text) {
        input.value = data.text;
        input.oninput();
        input.focus();
      } else {
        pushBot(data.error || "Could not understand the audio.", true);
      }
    } catch (err) {
      pushBot(err.message, true);
    } finally {
      input.placeholder = oldPlaceholder;
      recBtn.disabled = busy;
    }
  }

  recBtn.onclick = async () => {
    if (recorder && recorder.state === "recording") {
      recorder.stop();
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      pushBot("Voice recording is not supported in this browser.", true);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recorder = new MediaRecorder(stream);
      recordChunks = [];
      recorder.ondataavailable = (e) => e.data.size && recordChunks.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        recBtn.classList.remove("recording");
        recBtn.setAttribute("aria-label", "Record voice");
        transcribe(new Blob(recordChunks, { type: recorder.mimeType || "audio/webm" }));
      };
      recorder.start();
      recBtn.classList.add("recording");
      recBtn.setAttribute("aria-label", "Stop recording");
    } catch {
      pushBot("Microphone permission was denied.", true);
    }
  };

  /* ---------------- AI Monitoring login ---------------- */

  $("#closeModal").onclick = () => (loginModal.hidden = true);

  $("#loginForm").onsubmit = (e) => {
    e.preventDefault();
    const ok =
      $("#email").value === "elhosenyhassan007@gamil.com" && $("#password").value === "Elhoseny@007";
    if (ok) {
      monitoringUnlocked = true;
      $("#loginError").textContent = "";
      loginModal.hidden = true;
      setActive("AI Monitoring");
    } else {
      $("#loginError").textContent = "Invalid credentials.";
    }
  };

  newChatButton.onclick = createChat;

const clearChatButton = document.createElement("button");
clearChatButton.type = "button";
clearChatButton.className = "clear-chat-btn";
clearChatButton.textContent = "Clear chat";
$(".top-actions").prepend(clearChatButton);

async function clearSection() {
  const s = cfg();
  if (!s || !s.mode || busy) return;

  if (!window.confirm(`Clear all messages in "${s.name}"?`)) return;

  try {
    await api(`/api/chat/${encodeURIComponent(s.name)}`, {
      method: "DELETE",
    });
  } catch (err) {
    pushBot(err.message, true);
    return;
  }

  histories[s.name] = [{ role: "bot", text: s.intro, time: nowTime() }];
  saveMessages();
  renderMessages();
}

clearChatButton.onclick = clearSection;  
// Saved chats are listed in the sidebar.
if (loadChatsButton) loadChatsButton.hidden = true;
if (deleteChatButton) deleteChatButton.hidden = true;

  /* ---------------- Init ---------------- */

  loadMessages();
  restoreSavedChats();
  const dateChip = $(".date-chip");
  if (dateChip) {
    dateChip.textContent = new Date()
      .toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" })
      .toUpperCase();
  }

  setActive(active);
  checkHealth();
  setInterval(checkHealth, HEALTH_INTERVAL_MS);
  loadFiles();
})();
