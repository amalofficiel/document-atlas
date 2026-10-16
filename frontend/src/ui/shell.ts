import { icon } from "./icons";

export const appShell = `
  <a class="skip-link" href="#chat-input">Passer à votre question</a>
  <div class="app-shell">
    <aside class="sidebar" aria-label="Espace documentaire">
      <div class="sidebar-brand"><span class="monogram">DA<span></span></span><div><b>Document Atlas</b><small>par Amal Hlaissie</small></div></div>
      <div class="sidebar-divider"></div>
      <p class="sidebar-eyebrow">VOTRE ESPACE DOCUMENTAIRE</p>
      <button class="new-chat clear-chat" type="button">${icon("plus")} Nouvelle discussion</button>
      <div class="sidebar-section"><p>DISCUSSION EN COURS</p><div class="history-item">${icon("chat")}<span id="conversation-title" dir="auto">Nouvelle recherche</span></div></div>
      <div class="sidebar-note"><span class="note-icon">${icon("book")}</span><h2>Une réponse, ses références.</h2><p>Retrouvez les passages cités directement dans les documents consultés.</p></div>
      <a class="official-link" href="https://github.com/amalofficiel/document-atlas" target="_blank" rel="noopener noreferrer">Voir le code source ${icon("arrow")}</a>
      <div class="sidebar-footer"><span class="footer-rule"></span><p>Corpus de démonstration</p><small>Assistant de recherche documentaire</small></div>
    </aside>
    <div class="chat-container">
      <header class="chat-header"><div class="header-title"><span class="mobile-brand">DA</span><span class="header-breadcrumb">Espace documentaire <span>/</span></span><h1>Document Atlas</h1></div><div class="header-actions"><span class="connection-status" id="connection-status" role="status"><span class="status-dot"></span>Connexion…</span><button class="mobile-clear clear-chat" type="button" aria-label="Nouvelle discussion" title="Nouvelle discussion">${icon("plus")}</button></div></header>
      <main class="chat-main" id="chat-main" role="log" aria-label="Conversation" aria-live="polite"><div class="empty-state" id="empty-state"></div></main>
      <footer class="composer-area">
        <form class="chat-form" id="chat-form" autocomplete="off">
          <div class="composer-heading"><label for="chat-input">Votre question</label><span>Français <span class="dot-separator">·</span> <span lang="ar" dir="rtl">العربية</span></span></div>
          <div class="composer-input-row"><textarea id="chat-input" class="chat-input" rows="2" maxlength="1000" dir="auto" placeholder="Que souhaitez-vous savoir sur ce corpus de démonstration ?" aria-describedby="composer-hint"></textarea><button class="chat-send" type="submit" aria-label="Envoyer la question">${icon("send")}</button></div>
          <div class="composer-hint" id="composer-hint"><span>Entrée pour envoyer <span class="dot-separator">·</span> Maj + Entrée pour une nouvelle ligne</span><span id="character-count">0 / 1000</span></div>
        </form>
        <p class="disclaimer">L’assistant peut faire des erreurs. Consultez les sources pour vérifier les réponses.</p>
      </footer>
    </div>
  </div>`;
