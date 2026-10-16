import type { ChatResponse } from '../types';
import { searchDemo, type DemoPage } from '../demo';
export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';
export const API_URL = DEMO_MODE ? window.location.origin : (import.meta.env.VITE_API_URL ?? 'http://localhost:8000');
export class ChatApiError extends Error {}
let corpusPromise: Promise<DemoPage[]> | undefined;
function loadCorpus(): Promise<DemoPage[]> {
  return corpusPromise ??= fetch(`${import.meta.env.BASE_URL}corpus.json`).then(async r => {
    if (!r.ok) throw new ChatApiError('Le corpus de démonstration est indisponible.');
    return await r.json() as DemoPage[];
  });
}
export async function isBackendReady(): Promise<boolean> {
  try {
    if (DEMO_MODE) return (await loadCorpus()).length > 0;
    const response = await fetch(`${API_URL}/api/health`);
    const health = await response.json() as { retrieval_ready?: boolean };
    return response.ok && health.retrieval_ready === true;
  } catch { return false; }
}
export async function askQuestion(question: string): Promise<ChatResponse> {
  if (DEMO_MODE) {
    const pages = searchDemo(question, await loadCorpus());
    return {
      answer: pages.length
        ? '### Passages retrouvés\nRecherche lexicale locale, sans génération IA. Ces extraits proviennent de documents fictifs ; ils peuvent ne pas répondre à toute la question.\n\n'+pages.map((p,i) => `**${p.heading}**\n${p.text} [Source ${i+1}]`).join('\n\n')
        : '### Aucun passage correspondant\nCette démo gratuite effectue une recherche lexicale en français sur six documents fictifs. Essayez « archives », « sauvegardes », « accès » ou « limite API ». La recherche multilingue et la génération IA sont disponibles dans le pipeline Python à exécuter en local.',
      sources: pages.map(p => ({filename:p.filename,page:p.page,year:null,retrieval_type:'browser-lexical-demo',url:`${import.meta.env.BASE_URL}documents/${encodeURIComponent(p.filename)}#page=${p.page}`})),
    };
  }
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question}),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null) as {detail?: unknown} | null;
    throw new ChatApiError(typeof error?.detail === 'string' ? error.detail : `Erreur du serveur (${response.status}).`);
  }
  return await response.json() as ChatResponse;
}
