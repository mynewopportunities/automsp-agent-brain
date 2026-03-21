#!/usr/bin/env python3
import sys, os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER

NAVY = HexColor('#1B2A4A')
GREEN = HexColor('#00C896')
LIGHT_GRAY = HexColor('#F5F7FA')
DARK_GRAY = HexColor('#4A5568')
BORDER_GRAY = HexColor('#E2E8F0')

def get_styles():
    return {
        'Title': ParagraphStyle('Title', fontSize=24, textColor=NAVY, spaceAfter=6, fontName='Helvetica-Bold'),
        'H2': ParagraphStyle('H2', fontSize=14, textColor=NAVY, spaceAfter=6, spaceBefore=12, fontName='Helvetica-Bold'),
        'H3': ParagraphStyle('H3', fontSize=12, textColor=DARK_GRAY, spaceAfter=4, spaceBefore=8, fontName='Helvetica-Bold'),
        'Body': ParagraphStyle('Body', fontSize=10, textColor=DARK_GRAY, spaceAfter=6, fontName='Helvetica', leading=16),
        'Bullet': ParagraphStyle('Bullet', fontSize=10, textColor=DARK_GRAY, spaceAfter=3, fontName='Helvetica', leftIndent=20, leading=16),
        'TableCell': ParagraphStyle('TableCell', fontSize=9, textColor=DARK_GRAY, fontName='Helvetica'),
        'TableHeader': ParagraphStyle('TableHeader', fontSize=9, textColor=white, fontName='Helvetica-Bold'),
        'Meta': ParagraphStyle('Meta', fontSize=9, textColor=HexColor('#718096'), fontName='Helvetica-Oblique'),
    }

def parse_table(lines):
    rows = []
    for line in lines:
        if re.match(r'\s*\|[-:| ]+\|\s*$', line): continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)
    return rows

def md_to_pdf(md_path, pdf_path=None):
    if not pdf_path:
        pdf_path = md_path.replace('.md', '.pdf')
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    styles = get_styles()
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=25*mm, bottomMargin=20*mm)
    story = []
    header_data = [['AutoMSP', 'automsp.ae | hello@automsp.ae']]
    header_table = Table(header_data, colWidths=[110*mm, 70*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TEXTCOLOR', (0,0), (-1,-1), white),
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (0,0), 14),
        ('FONTNAME', (1,0), (1,0), 'Helvetica'),
        ('FONTSIZE', (1,0), (1,0), 8),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (0,0), 15),
        ('RIGHTPADDING', (1,0), (1,0), 15),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8*mm))
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('# ') and not line.startswith('## '):
            story.append(Paragraph(line[2:].strip(), styles['Title']))
            story.append(HRFlowable(width='100%', thickness=2, color=GREEN, spaceAfter=8))
            i += 1; continue
        if line.startswith('## '):
            story.append(Spacer(1, 3*mm))
            story.append(Paragraph(line[3:].strip(), styles['H2']))
            story.append(HRFlowable(width='100%', thickness=1, color=BORDER_GRAY, spaceAfter=4))
            i += 1; continue
        if line.startswith('### '):
            story.append(Paragraph(line[4:].strip(), styles['H3']))
            i += 1; continue
        if re.match(r'^-{3,}$', line.strip()):
            story.append(HRFlowable(width='100%', thickness=1, color=BORDER_GRAY, spaceAfter=6))
            i += 1; continue
        if line.strip().startswith('|') and i+1 < len(lines) and re.match(r'\s*\|[-:| ]+\|\s*$', lines[i+1]):
            tlines = [line]
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('|'):
                tlines.append(lines[j]); j += 1
            rows = parse_table(tlines)
            if rows:
                pw = A4[0] - 40*mm
                cw = pw / len(rows[0])
                tdata = []
                for ri, row in enumerate(rows):
                    st = styles['TableHeader'] if ri == 0 else styles['TableCell']
                    tdata.append([Paragraph(str(c), st) for c in row])
                t = Table(tdata, colWidths=[cw]*len(rows[0]), repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), NAVY),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LIGHT_GRAY]),
                    ('GRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 6),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                story.append(t)
                story.append(Spacer(1, 4*mm))
            i = j; continue
        if re.match(r'^[\*\-] ', line):
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line[2:].strip())
            story.append(Paragraph(f'• {text}', styles['Bullet']))
            i += 1; continue
        if re.match(r'^\- \[[ x]\]', line):
            checked = 'x' in line[2:5] and '☑' or '☐'
            story.append(Paragraph(f'{checked} {line[6:].strip()}', styles['Bullet']))
            i += 1; continue
        if re.match(r'^\d+\. ', line):
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', re.sub(r'^\d+\. ', '', line))
            story.append(Paragraph(f'• {text}', styles['Bullet']))
            i += 1; continue
        if line.strip():
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line.strip())
            text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
            text = re.sub(r'`(.+?)`', r'<font name="Courier">\1</font>', text)
            story.append(Paragraph(text, styles['Body']))
        else:
            story.append(Spacer(1, 3*mm))
        i += 1
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=1, color=BORDER_GRAY))
    story.append(Paragraph('AutoMSP — AI Automation for MSPs and Enterprise | automsp.ae | hello@automsp.ae', styles['Meta']))
    doc.build(story)
    return pdf_path

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 md_to_pdf.py /path/to/file.md [output.pdf]")
        sys.exit(1)
    result = md_to_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"PDF: {result}")
