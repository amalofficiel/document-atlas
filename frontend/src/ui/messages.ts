import type { Source, ChatMessage } from "../types";
import { API_URL, DEMO_MODE } from "../api/client";
import { icon } from "./icons";
import { renderMarkdown } from "./markdown";

function createSourceLink(source: Source): HTMLAnchorElement {
  const link = document.createElement("a");
  link.href = new URL(source.url, `${API_URL.replace(/\/$/, "")}/`).href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.title = `${source.filename} · page ${source.page} — ouvrir dans un nouvel onglet`;
  return link;
}
export function addMessage(chatMain: HTMLElement, message: ChatMessage): void {
  const el = document.createElement("article");
  el.className = `message ${message.role}`;
  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.innerHTML = message.role === "bot" ? `<span class="assistant-avatar">${icon("book")}</span><span>Document Atlas</span><span class="response-label">${DEMO_MODE ? "EXTRAITS DU CORPUS FICTIF" : "RÉPONSE DOCUMENTAIRE"}</span>` : "<span>Vous</span>";
  el.append(meta);
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.dir = "auto";
  if (/[\u0600-\u06ff]/.test(message.text)) bubble.lang = "ar";
  bubble.innerHTML = renderMarkdown(message.text);
  if (message.role === "bot" && message.sources?.length) {
    const walker = document.createTreeWalker(bubble, NodeFilter.SHOW_TEXT);
    const textNodes: Text[] = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode as Text);
    for (const node of textNodes) {
      const text = node.textContent ?? "";
      const fragment = document.createDocumentFragment();
      let offset = 0;
      for (const match of text.matchAll(/\[Source\s+(\d+)\]/g)) {
        const source = message.sources[Number(match[1]) - 1];
        if (!source) continue;
        fragment.append(text.slice(offset, match.index));
        const link = createSourceLink(source);
        link.className = "citation";
        link.textContent = match[0];
        fragment.append(link);
        offset = match.index + match[0].length;
      }
      fragment.append(text.slice(offset));
      node.replaceWith(fragment);
    }
  }
  el.append(bubble);
  if (message.sources?.length) {
    const sourcesEl = document.createElement("details");
    sourcesEl.className = "sources";
    sourcesEl.open = true;
    const summary = document.createElement("summary");
    summary.innerHTML = `${icon("document")} Documents consultés <span class="source-count">${message.sources.length}</span>`;
    sourcesEl.append(summary);
    message.sources.forEach((s, i) => {
      const link = createSourceLink(s);
      link.className = "source";
      const index = document.createElement("span");
      index.className = "source-number";
      index.textContent = String(i + 1).padStart(2, "0");
      const title = document.createElement("span");
      title.className = "source-title";
      const filename = document.createElement("b");
      filename.textContent = s.filename;
      const location = document.createElement("small");
      location.textContent = [s.year, s.page ? `Page ${s.page}` : null, "Ouvrir le passage cité"].filter(Boolean).join(" · ");
      title.append(filename, location);
      const arrow = document.createElement("span");
      arrow.innerHTML = icon("arrow");
      link.append(index, title, arrow);
      sourcesEl.append(link);
    });
    el.append(sourcesEl);
  }
  chatMain.append(el);
  chatMain.scrollTop = chatMain.scrollHeight;
}
export function addTyping(chatMain: HTMLElement, arabic: boolean): HTMLElement {
  const el = document.createElement("div");
  el.className = "message bot loading-message";
  el.setAttribute("role", "status");
  el.innerHTML = `<div class="loading-feedback"><span class="assistant-avatar">${icon("book")}</span><span dir="auto">${arabic ? "جارٍ البحث في الوثائق…" : "Recherche dans les documents…"}</span><span class="typing" aria-hidden="true"><i></i><i></i><i></i></span></div>`;
  chatMain.append(el);
  chatMain.scrollTop = chatMain.scrollHeight;
  return el;
}
