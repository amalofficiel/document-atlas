export interface Source { filename: string; page: number | null; year: number | null; retrieval_type: string | null; url: string; }
export interface ChatResponse { answer: string; sources: Source[]; }
export interface ChatMessage { role: "user" | "bot"; text: string; sources?: Source[]; }
