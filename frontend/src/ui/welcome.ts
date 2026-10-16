import { icon } from "./icons";

const suggestions = [
  { category: "EXPLORER LES ARCHIVES", title: "Combien de temps les dossiers sont-ils conservés ?", icon: "document" as const },
  { category: "EXPLORER UN SUJET", title: "Quelle est la limite de requêtes de l’API ?", icon: "book" as const },
  { category: "COMPRENDRE LES INCIDENTS", title: "Comment signaler une panne ?", icon: "globe" as const },
];
export function renderWelcome(emptyState: HTMLElement, onSelect: (question: string) => void): void {
  emptyState.innerHTML = `
    <div class="welcome-mark">${icon("book")}<span class="mark-spark"></span></div>
    <p class="welcome-kicker"><span></span> LES DOCUMENTS AU CŒUR DE LA RÉPONSE</p>
    <h2>La bonne information.<br /><em>À la source.</em></h2>
    <p class="welcome-copy">Explorez les documents fictifs de notre atelier. Posez votre question, retrouvez les références.</p>
    <div class="welcome-features"><span>${icon("document")}Corpus de démonstration</span><span>${icon("globe")}Sources PDF consultables</span><span>${icon("check")}Sources citées</span></div>
    <div class="suggestions-heading"><span>PAR OÙ COMMENCER ?</span><span>Quelques idées de questions</span></div>
    <div class="suggestions">${suggestions.map((s, i) => `<button class="suggestion" type="button" data-index="${i}"><span class="suggestion-top">${icon(s.icon)}${icon("arrow")}</span><span class="suggestion-category">${s.category}</span><span class="suggestion-title" dir="auto" >${s.title}</span></button>`).join("")}</div>`;
  emptyState.querySelectorAll<HTMLButtonElement>(".suggestion").forEach((button) => {
    button.addEventListener("click", () => {
      onSelect(suggestions[Number(button.dataset.index)]!.title);
    });
  });
}
