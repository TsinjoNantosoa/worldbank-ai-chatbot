/**
 * Chatbot World Bank — Widget injectable
 * ========================================
 * Injectez ce script sur n'importe quelle page pour afficher un chatbot flottant
 * connecté à l'API /query du backend World Bank.
 *
 * Usage :
 *   <script src="https://YOUR_DOMAIN/interface_wp_chatbot.js"></script>
 *
 * Le widget crée automatiquement un bouton flottant en bas à droite et un panel
 * de conversation avec l'assistant World Bank Data.
 */
(function () {
  "use strict";

  /* ────── Configuration ────── */
  const API_URL =
    window.WB_CHATBOT_API || "https://YOUR_DOMAIN/query";
  const LANG = window.WB_CHATBOT_LANG || "fr";
  const TITLE = "World Bank Data Assistant";
  const SUBTITLE = "Données Banque Mondiale — CC BY 4.0";
  const WELCOME_FR =
    "Bonjour ! Je suis l'assistant World Bank Data. Posez-moi une question sur les indicateurs économiques, sociaux ou environnementaux disponibles via la Banque Mondiale.";
  const WELCOME_EN =
    "Hello! I'm the World Bank Data assistant. Ask me about economic, social, or environmental indicators available through the World Bank.";

  /* ────── Couleurs World Bank ────── */
  const C = {
    primary: "#002244",
    accent: "#009FDA",
    white: "#ffffff",
    light: "#f5f7fa",
    border: "#dde3ee",
    textDark: "#222",
    textMuted: "#78909c",
  };

  /* ────── State ────── */
  const userId =
    "wb-widget-" + Math.random().toString(36).substring(2, 8);
  let isOpen = false;

  /* ────── Inject CSS ────── */
  const style = document.createElement("style");
  style.textContent = `
    #wb-chat-fab{
      position:fixed;bottom:24px;right:24px;z-index:99999;
      width:56px;height:56px;border-radius:50%;
      background:${C.primary};color:${C.white};border:none;
      cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,0.25);
      display:flex;align-items:center;justify-content:center;
      font-size:26px;transition:transform 0.25s,background 0.25s;
    }
    #wb-chat-fab:hover{background:#003366;transform:scale(1.08);}
    #wb-chat-fab.open{transform:rotate(180deg);}
    #wb-chat-panel{
      position:fixed;bottom:90px;right:24px;z-index:99999;
      width:380px;max-width:calc(100vw - 48px);height:520px;max-height:calc(100vh - 120px);
      border-radius:14px;overflow:hidden;
      display:none;flex-direction:column;
      background:${C.white};
      box-shadow:0 10px 40px rgba(0,0,0,0.18);
      font-family:'Segoe UI',system-ui,sans-serif;
    }
    #wb-chat-panel.open{display:flex;}
    .wb-hdr{
      background:${C.primary};color:${C.white};
      padding:14px 18px;display:flex;align-items:center;gap:10px;
      flex-shrink:0;
    }
    .wb-hdr .wb-logo{font-size:22px;}
    .wb-hdr .wb-titles{flex:1}
    .wb-hdr .wb-ttl{font-size:0.88rem;font-weight:700}
    .wb-hdr .wb-sub{font-size:0.66rem;opacity:0.55;margin-top:1px}
    .wb-hdr .wb-close{background:none;border:none;color:${C.white};font-size:18px;cursor:pointer;opacity:0.7;transition:opacity 0.2s}
    .wb-hdr .wb-close:hover{opacity:1}
    #wb-msgs{
      flex:1;overflow-y:auto;padding:14px 16px;
      display:flex;flex-direction:column;gap:10px;
      background:${C.light};
    }
    #wb-msgs::-webkit-scrollbar{width:4px}
    #wb-msgs::-webkit-scrollbar-thumb{background:#c8ced6;border-radius:3px}
    .wb-msg{
      max-width:85%;padding:10px 14px;border-radius:12px;
      font-size:0.84rem;line-height:1.5;word-break:break-word;
    }
    .wb-msg.u{
      align-self:flex-end;background:${C.primary};color:${C.white};
      border-bottom-right-radius:3px;
    }
    .wb-msg.b{
      align-self:flex-start;background:${C.white};color:${C.textDark};
      border:1px solid ${C.border};border-bottom-left-radius:3px;
      box-shadow:0 1px 3px rgba(0,0,0,0.04);
    }
    .wb-msg.b a{color:${C.accent}}
    .wb-typing{
      align-self:flex-start;background:${C.white};
      border:1px solid ${C.border};border-radius:12px;
      padding:10px 14px;display:flex;gap:4px;align-items:center;
    }
    .wb-typing span{
      width:6px;height:6px;background:#90a4ae;border-radius:50%;
      animation:wb-bounce 1.2s infinite;
    }
    .wb-typing span:nth-child(2){animation-delay:0.2s}
    .wb-typing span:nth-child(3){animation-delay:0.4s}
    @keyframes wb-bounce{
      0%,60%,100%{transform:translateY(0)}
      30%{transform:translateY(-5px)}
    }
    .wb-inputbar{
      border-top:1px solid #e0e0e0;padding:9px 12px;
      display:flex;gap:8px;flex-shrink:0;background:${C.white};
    }
    .wb-inputbar input{
      flex:1;border:1px solid #cfd8dc;border-radius:7px;
      padding:8px 12px;font-size:0.84rem;outline:none;
      font-family:inherit;transition:border-color 0.2s;
    }
    .wb-inputbar input:focus{border-color:${C.primary}}
    .wb-inputbar button{
      background:${C.primary};color:${C.white};border:none;
      border-radius:7px;padding:8px 16px;font-size:0.84rem;
      cursor:pointer;font-weight:600;transition:background 0.2s;
    }
    .wb-inputbar button:hover{background:#003366}
    .wb-inputbar button:disabled{background:#b0bec5;cursor:not-allowed}
    .wb-foot{
      text-align:center;font-size:0.63rem;color:${C.textMuted};
      padding:3px 0 7px;font-style:italic;background:${C.white};
    }
  `;
  document.head.appendChild(style);

  /* ────── Build DOM ────── */
  // FAB
  const fab = document.createElement("button");
  fab.id = "wb-chat-fab";
  fab.innerHTML = "🌍";
  fab.title = "Ouvrir le chatbot World Bank";
  fab.addEventListener("click", toggle);
  document.body.appendChild(fab);

  // Panel
  const panel = document.createElement("div");
  panel.id = "wb-chat-panel";
  panel.innerHTML = `
    <div class="wb-hdr">
      <span class="wb-logo">🌍</span>
      <div class="wb-titles">
        <div class="wb-ttl">${TITLE}</div>
        <div class="wb-sub">${SUBTITLE}</div>
      </div>
      <button class="wb-close" onclick="document.getElementById('wb-chat-fab').click()">✕</button>
    </div>
    <div id="wb-msgs"></div>
    <div class="wb-inputbar">
      <input type="text" id="wb-input" placeholder="${LANG === 'en' ? 'Ask a question...' : 'Posez votre question...'}" />
      <button id="wb-send">▶</button>
    </div>
    <div class="wb-foot">${LANG === 'en' ? 'World Bank Open Data (CC BY 4.0). Do not share personal information.' : 'Données World Bank (CC BY 4.0). Ne partagez pas d\'infos personnelles.'}</div>
  `;
  document.body.appendChild(panel);

  // Welcome
  const msgs = document.getElementById("wb-msgs");
  addBot(LANG === "en" ? WELCOME_EN : WELCOME_FR);

  // Listeners
  document.getElementById("wb-send").addEventListener("click", doSend);
  document.getElementById("wb-input").addEventListener("keydown", function (e) {
    if (e.key === "Enter") doSend();
  });

  /* ────── Toggle ────── */
  function toggle() {
    isOpen = !isOpen;
    fab.classList.toggle("open", isOpen);
    panel.classList.toggle("open", isOpen);
    if (isOpen) document.getElementById("wb-input").focus();
  }

  /* ────── Send ────── */
  async function doSend() {
    const input = document.getElementById("wb-input");
    const btn = document.getElementById("wb-send");
    const q = input.value.trim();
    if (!q) return;

    addUser(q);
    input.value = "";
    btn.disabled = true;
    showTyping();

    try {
      const lang = detectLang(q);
      const r = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, user_id: userId, lang: lang }),
      });
      removeTyping();
      if (!r.ok) throw new Error("HTTP " + r.status);
      const data = await r.json();
      addBot(data.answer || "Aucune réponse.");
    } catch (e) {
      removeTyping();
      addBot(
        LANG === "en"
          ? "⚠️ Connection error. Please try again."
          : "⚠️ Erreur de connexion. Veuillez réessayer."
      );
    }
    btn.disabled = false;
    input.focus();
  }

  /* ────── DOM helpers ────── */
  function addUser(text) {
    const d = document.createElement("div");
    d.className = "wb-msg u";
    d.textContent = text;
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function addBot(html) {
    const d = document.createElement("div");
    d.className = "wb-msg b";
    d.innerHTML = html;
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function showTyping() {
    const d = document.createElement("div");
    d.className = "wb-typing";
    d.id = "wb-typ";
    d.innerHTML = "<span></span><span></span><span></span>";
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function removeTyping() {
    const t = document.getElementById("wb-typ");
    if (t) t.remove();
  }

  function detectLang(text) {
    return /\b(what|who|when|where|why|how|can|do|does|is|are|please|hello|hi|summarize)\b/i.test(text)
      ? "en"
      : "fr";
  }
})();
