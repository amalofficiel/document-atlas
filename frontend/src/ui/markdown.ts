export function renderMarkdown(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/^### (.*)$/gm, "<h3>$1</h3>").replace(/^##? (.*)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/^- (.*)$/gm, "<li>$1</li>")
    .replace(/(^|\n)((?:<li>.*\n?)+)/g, "$1<ul>$2</ul>").replace(/\n/g, "<br/>");
}
