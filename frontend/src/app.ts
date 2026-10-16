import { askQuestion, isBackendReady, ChatApiError, DEMO_MODE } from "./api/client";
import { appShell } from "./ui/shell";
import { renderWelcome } from "./ui/welcome";
import { addMessage, addTyping } from "./ui/messages";

export function initializeApp(): void {
  const app = document.getElementById("app")!;
  app.innerHTML = appShell;
  const notice = document.createElement('p');
  notice.className = 'demo-notice';
  notice.textContent = DEMO_MODE
    ? 'DÉMO GRATUITE · Corpus fictif · Recherche lexicale en français · Sans génération IA'
    : 'PIPELINE IA LOCAL · Corpus fictif · Vérifiez les sources avant toute utilisation';
  document.querySelector('.chat-header')!.after(notice);
  if (DEMO_MODE) document.querySelector('.composer-heading > span')!.textContent = 'Recherche en français';
  document.querySelector('.disclaimer')!.textContent = DEMO_MODE
    ? 'Extraits fictifs, affichés sans reformulation par un modèle. Aucune question envoyée à un serveur IA.'
    : 'L’assistant peut faire des erreurs. Consultez les documents fictifs pour vérifier les réponses.';
  const chatMain = document.getElementById("chat-main") as HTMLElement;
  const emptyState = document.getElementById("empty-state") as HTMLElement;
  const form = document.getElementById("chat-form") as HTMLFormElement;
  const input = document.getElementById("chat-input") as HTMLTextAreaElement;
  const sendButton = form.querySelector("button") as HTMLButtonElement;
  const status = document.getElementById("connection-status") as HTMLElement;
  const clearButtons = document.querySelectorAll<HTMLButtonElement>(".clear-chat");
  const conversationTitle = document.getElementById("conversation-title")!;
  let busy = false;
  let hasMessages = false;

  function updateInput(): void {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
    document.getElementById("character-count")!.textContent = `${input.value.length} / 1000`;
    sendButton.disabled = busy || !input.value.trim();
  }
  input.addEventListener("input", updateInput);
  window.addEventListener("resize", updateInput);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      if (!busy && input.value.trim()) form.requestSubmit();
    }
  });
  function setConnectionStatus(connected: boolean): void {
    status.classList.toggle("offline", !connected);
    status.innerHTML = `<span class="status-dot"></span>${connected ? (DEMO_MODE ? "Démo disponible" : "Assistant disponible") : "Service indisponible"}`;
  }
  async function checkBackend(): Promise<void> {
    setConnectionStatus(await isBackendReady());
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question || busy) return;
    busy = true;
    if (!hasMessages) conversationTitle.textContent = question;
    hasMessages = true;
    input.value = "";
    input.disabled = true;
    clearButtons.forEach(b => b.disabled = true);
    updateInput();
    form.setAttribute("aria-busy", "true");
    const arabic = /[\u0600-\u06ff]/.test(question);
    emptyState.remove();
    addMessage(chatMain, { role: "user", text: question });
    const typingEl = addTyping(chatMain, arabic);
    try {
      const data = await askQuestion(question);
      typingEl.remove();
      addMessage(chatMain, { role: "bot", text: data.answer, sources: data.sources });
      setConnectionStatus(true);
    } catch (err) {
      typingEl.remove();
      const apiError = err instanceof ChatApiError;
      addMessage(chatMain, { role: "bot", text: apiError
        ? (arabic ? "تعذّر إنشاء الإجابة. يرجى إعادة المحاولة بعد قليل." : `${err.message} Veuillez réessayer dans quelques instants.`)
        : (arabic ? "تعذّر الاتصال بالخادم. تحقق من اتصالك وأعد المحاولة." : "Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.") });
      if (apiError) void checkBackend(); else setConnectionStatus(false);
      input.value = question;
    } finally {
      busy = false;
      input.disabled = false;
      clearButtons.forEach(b => b.disabled = false);
      form.removeAttribute("aria-busy");
      updateInput();
      input.focus();
    }
  });
  clearButtons.forEach(button => button.addEventListener("click", () => {
    if (busy) return;
    chatMain.replaceChildren(emptyState);
    hasMessages = false;
    conversationTitle.textContent = "Nouvelle recherche";
    input.value = "";
    renderEmptyState();
    updateInput();
    chatMain.scrollTop = 0;
    input.focus();
  }));
  renderEmptyState();
  updateInput();
  void checkBackend();

  function renderEmptyState(): void {
    renderWelcome(emptyState, (question) => {
      input.value = question;
      updateInput();
      input.focus();
    });
  }
}
