/** Browser-only lexical demo. The full Python RAG pipeline is evaluated separately. */
export interface DemoPage { filename: string; page: number; title: string; heading: string; text: string; }
const stopwords = new Set('le la les de du des un une et ou en dans pour par sur au aux ce ces cette est sont quelle quelles quel quels comment que qui a à combien quand doit il elle on se son sa ses faut ils elles'.split(' '));
export function tokenize(text: string): string[] {
  return (text.normalize('NFKD').replace(/\p{M}/gu, '').toLocaleLowerCase('fr').match(/[\p{L}\p{N}]+/gu) ?? [])
    .filter(t => t.length > 1 && !stopwords.has(t))
    .map(t => /^[a-z]+$/.test(t) && t.length > 4 && /[sx]$/.test(t) ? t.slice(0,-1) : t);
}
export function searchDemo(question: string, pages: DemoPage[], limit = 3): DemoPage[] {
  const corpus = pages.map(p => tokenize(`${p.title} ${p.heading} ${p.text}`));
  const average = corpus.reduce((sum,t) => sum+t.length,0) / (corpus.length || 1);
  const terms = [...new Set(tokenize(question))];
  return pages.map((page,index) => {
    let score = 0;
    for (const term of terms) {
      const df = corpus.filter(tokens => tokens.includes(term)).length;
      const tf = corpus[index]!.filter(token => token === term).length;
      if (!tf) continue;
      const idf = Math.log(1+(pages.length-df+0.5)/(df+0.5));
      score += idf * tf * 2.5 / (tf+1.5*(0.25+0.75*corpus[index]!.length/average));
    }
    return {page,score};
  }).filter(r => r.score > 0).sort((a,b) => b.score-a.score || a.page.filename.localeCompare(b.page.filename) || a.page.page-b.page.page).slice(0,limit).map(r => r.page);
}
