import os
import zipfile
import html

def create_docx(filename):
    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    word_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/>
        <w:color w:val="2B2B2B"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:after="160" w:line="276" w:lineRule="auto"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
  
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:pPr>
      <w:spacing w:before="360" w:after="160"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri Light" w:hAnsi="Calibri Light"/>
      <w:b/>
      <w:sz w:val="34"/>
      <w:color w:val="1B365D"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:pPr>
      <w:spacing w:before="260" w:after="120"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri Light" w:hAnsi="Calibri Light"/>
      <w:b/>
      <w:sz w:val="28"/>
      <w:color w:val="2E5B88"/>
    </w:rPr>
  </w:style>
</w:styles>"""

    def p(text="", bold=False, italic=False, style=None, color=None, size=None, align=None, bullet=False):
        style_xml = f'<w:pStyle w:val="{style}"/>' if style else ''
        align_xml = f'<w:jc w:val="{align}"/>' if align else ''
        p_pr = f'<w:pPr>{style_xml}{align_xml}</w:pPr>' if (style_xml or align_xml) else ''
        if bullet:
            p_pr = '<w:pPr><w:pStyle w:val="ListParagraph"/></w:pPr>'
            text = f"•   {text}"
            
        r_pr_items = []
        if bold: r_pr_items.append('<w:b/>')
        if italic: r_pr_items.append('<w:i/>')
        if color: r_pr_items.append(f'<w:color w:val="{color}"/>')
        if size: r_pr_items.append(f'<w:sz w:val="{size}"/>')
        
        r_pr = f'<w:rPr>{"".join(r_pr_items)}</w:rPr>' if r_pr_items else ''
        escaped_text = html.escape(text)
        return f'<w:p>{p_pr}<w:r>{r_pr}<w:t xml:space="preserve">{escaped_text}</w:t></w:r></w:p>'

    def code_box(code_text):
        lines = code_text.strip().split('\n')
        xml_res = []
        for line in lines:
            esc = html.escape(line)
            xml_res.append(f'<w:p><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F4F4F5"/><w:spacing w:before="40" w:after="40"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="19"/><w:color w:val="1F2937"/></w:rPr><w:t xml:space="preserve">{esc}</w:t></w:r></w:p>')
        return "".join(xml_res)

    def note_box(title, text):
        esc_title = html.escape(title)
        esc_text = html.escape(text)
        return f'<w:p><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="EBF5FF"/><w:spacing w:before="120" w:after="40"/></w:pPr><w:r><w:rPr><w:b/><w:color w:val="1E40AF"/><w:sz w:val="21"/></w:rPr><w:t xml:space="preserve">{esc_title}</w:t></w:r></w:p><w:p><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="EBF5FF"/><w:spacing w:before="0" w:after="120"/></w:pPr><w:r><w:rPr><w:color w:val="1E3A8A"/><w:sz w:val="20"/></w:rPr><w:t xml:space="preserve">{esc_text}</w:t></w:r></w:p>'

    body_parts = []

    # Title
    body_parts.append(p("DOCUMENTATION TECHNIQUE & SPÉCIFICATIONS ARCHITECTURE", bold=True, size="36", color="1B365D", align="center"))
    body_parts.append(p("GetVideo 2.0 - Téléchargeur & Extracteur Multimédia Universel HD", bold=True, size="26", color="2E5B88", align="center"))
    body_parts.append(p("Architecture Asynchrone Temps Réel, Sécurité Anti-Bot, Moteur i18n & Zero-Storage", italic=True, size="22", color="6B7280", align="center"))
    body_parts.append(p("_________________________________________________________________________________", color="CBD5E1", align="center"))
    body_parts.append(p("Auteur : Sylvano | Version : 2.0.0 | Date : Août 2026", size="18", color="6B7280", align="center"))
    body_parts.append(p(""))

    # 1. Vision & Fonctionnalités
    body_parts.append(p("1. Présentation & Nouveautés de GetVideo 2.0", style="Heading1"))
    body_parts.append(p("GetVideo 2.0 est une plateforme universelle de téléchargement et d'extraction multimédia conçue pour offrir des performances maximales sans coût d'infrastructure et sans stockage serveur persistant (Zero-Storage Policy)."))
    
    body_parts.append(p("Nouvelles Fonctionnalités Majeures (v2.0) :", bold=True))
    body_parts.append(p("Suivi de Progression en Temps Réel : Synchronisation à 100% entre le backend et la barre de progression dans le navigateur via polling et hooks yt-dlp.", bullet=True))
    body_parts.append(p("Annulation Interactive : Possibilité d'interrompre un téléchargement en cours d'un simple clic avec libération immédiate des ressources.", bullet=True))
    body_parts.append(p("Thème Clair & Sombre Persistant : Bascule intelligente avec support du mode système et stockage local.", bullet=True))
    body_parts.append(p("Système Multilingue (i18n) : 6 langues supportées (Français, Anglais, Espagnol, Arabe avec RTL, Allemand, Portugais).", bullet=True))
    body_parts.append(p("QR Code Mobile : Téléchargement instantané sur smartphone en scannant l'écran.", bullet=True))
    body_parts.append(p("Extraction de Sous-Titres : Téléchargement des fichiers .vtt et .srt multilingues.", bullet=True))
    body_parts.append(p("Sécurité Avancée : Rate Limiting (15 req/min), protection anti-SSRF et filtrage des scrapers malveillants.", bullet=True))

    # 2. Architecture Technique
    body_parts.append(p("2. Architecture Technique Asynchrone", style="Heading1"))
    body_parts.append(p("Le backend FastAPI utilise désormais un gestionnaire de tâches asynchrones en arrière-plan couplé aux hooks de progression de yt-dlp :"))
    body_parts.append(code_box("""
Client Web (Navigateur)               FastAPI Backend                    yt-dlp & FFmpeg
      |                                      |                                  |
      |--- 1. POST /api/start_download ----->|--- 2. Thread background -------->|
      |<-- Renvoie { task_id } --------------|                                  | (Téléchargement
      |                                      |                                  |  & Fusion flux)
      |--- 3. GET /api/progress/{task_id} -->|                                  |
      |<-- { percent: 45.2%, speed: 5.5MB } -|<- Hook de progression en direct -|
      |    (Répété toutes les 350ms)         |                                  |
      |                                      |                                  |
      |--- 4. Quand status == 'ready' ------>|<-- Fichier prêt dans /tmp -------|
      |--- GET /api/download_file/{task_id} -|                                  |
      |<== Téléchargement direct vers PC ====|                                  |
      |                                      |--- 5. Auto-suppression /tmp ---->|
    """))

    # 3. Spécification des Endpoints
    body_parts.append(p("3. Spécification des Endpoints d'API", style="Heading1"))
    body_parts.append(p("POST /api/start_download : Démarre la tâche de téléchargement en arrière-plan et renvoie l'identifiant unique (task_id).", bullet=True))
    body_parts.append(p("GET /api/progress/{task_id} : Renvoie en temps réel le pourcentage (0-100%), la vitesse, le volume transféré et l'ETA.", bullet=True))
    body_parts.append(p("POST /api/cancel_download/{task_id} : Annule la tâche en cours et supprime les fichiers temporaires.", bullet=True))
    body_parts.append(p("GET /api/download_file/{task_id} : Sert le fichier final avec Content-Length et déclenche le nettoyage automatique.", bullet=True))
    body_parts.append(p("GET /api/subtitle : Télécharge les sous-titres officiels ou traduits.", bullet=True))

    # 4. Guide de Déploiement
    body_parts.append(p("4. Déploiement Gratuit en Ligne", style="Heading1"))
    body_parts.append(p("GetVideo 2.0 est optimisé pour être déployé gratuitement à vie sur :", bold=True))
    body_parts.append(p("Oracle Cloud Infrastructure Always Free (4 vCPU ARM, 24 Go RAM, 10 To bande passante/mois).", bullet=True))
    body_parts.append(p("Hugging Face Spaces (Conteneur Docker gratuit avec 2 vCPU et 16 Go RAM).", bullet=True))

    # Build XML
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    {"".join(body_parts)}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as docx:
        docx.writestr('[Content_Types].xml', content_types_xml)
        docx.writestr('_rels/.rels', rels_xml)
        docx.writestr('word/_rels/document.xml.rels', word_rels_xml)
        docx.writestr('word/styles.xml', styles_xml)
        docx.writestr('word/document.xml', document_xml)

if __name__ == '__main__':
    target = '/home/sylvano/.gemini/antigravity/scratch/media/Documentation_Technique_MediaDownloader.docx'
    create_docx(target)
    print("Documentation mise à jour avec succès.")
