"""Rebuild the authored, fictional PDF corpus. Requires reportlab."""
import json
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape


def main():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

    root = Path(__file__).resolve().parents[1]
    pages = json.loads((root / 'evaluation/corpus.json').read_text())
    groups = defaultdict(list)
    for page in pages:
        groups[page['filename']].append(page)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('Notice', parent=styles['Normal'], textColor=colors.HexColor('#9b341c'), fontSize=10, leading=15))
    styles['BodyText'].fontSize = 12
    styles['BodyText'].leading = 20
    styles['Title'].textColor = colors.HexColor('#13265e')
    out = root / 'documents'
    out.mkdir(exist_ok=True)
    for filename, sections in groups.items():
        story = []
        for section in sections:
            if story:
                story.append(PageBreak())
            story.extend([
                Paragraph('DOCUMENT ATLAS - CORPUS FICTIF', styles['Notice']), Spacer(1,24),
                Paragraph(escape(section['title']), styles['Title']), Spacer(1,18),
                Paragraph(escape(section['heading']), styles['Heading2']), Spacer(1,12),
                Paragraph(escape(section['text']), styles['BodyText']), Spacer(1,32),
                Paragraph('Exemple inventé pour une démonstration technique. Ces règles ne proviennent d’aucune institution et ne constituent pas des recommandations.', styles['Notice']),
            ])
        def footer(canvas, doc):
            canvas.setFont('Helvetica', 9)
            canvas.setFillColor(colors.HexColor('#475569'))
            canvas.drawString(54, 32, 'Document Atlas | Données fictives')
            canvas.drawRightString(A4[0]-54,32,f'Page {doc.page}')
        SimpleDocTemplate(str(out/filename),pagesize=A4,rightMargin=54,leftMargin=54,topMargin=54,bottomMargin=54,title=sections[0]['title'],author='Amal Hlaissie').build(story,onFirstPage=footer,onLaterPages=footer)
        print(filename)


if __name__ == '__main__':
    main()
