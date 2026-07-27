"""
pdf_generator.py — Génère un PDF stylé Tastee/Winespace à partir des données scrapées.
Approche : HTML+CSS → WeasyPrint → PDF.
Charte graphique : bleu #1f1240 / violet #614dd4 / gris #888888.
"""

import base64
import io
from datetime import datetime


# ──────────────────────────────────────────────────────────────────────────────
#  Template HTML (inline CSS, Google Fonts, pas de fichiers externes)
# ──────────────────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Anton&family=Raleway:wght@400;600;700&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  @page {{
    size: A4;
    margin: 2cm 2cm 2.5cm 2cm;
    @bottom-center {{
      content: "Tastee · Winespace · " string(product-name) " · Page " counter(page) " / " counter(pages);
      font-family: 'Raleway', Calibri, sans-serif;
      font-size: 8pt;
      color: #999;
    }}
  }}

  body {{
    font-family: 'Raleway', Calibri, sans-serif;
    font-size: 11pt;
    color: #000;
    line-height: 1.4;
  }}

  /* ── Header ── */
  .header {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    border-bottom: 3px solid #614dd4;
    padding-bottom: 14px;
    margin-bottom: 20px;
  }}
  .header-logo {{
    font-family: 'Anton', Impact, sans-serif;
    font-size: 22pt;
    color: #1f1240;
    letter-spacing: 1px;
  }}
  .header-meta {{
    text-align: right;
    font-size: 9pt;
    color: #888;
    font-style: italic;
  }}
  .header-meta strong {{
    color: #614dd4;
    font-style: normal;
    font-weight: 700;
  }}

  /* ── Fiche produit ── */
  .product-section {{
    display: flex;
    gap: 24px;
    margin-bottom: 24px;
    background: #f8f7fc;
    border-radius: 8px;
    padding: 16px;
    border-left: 4px solid #614dd4;
  }}
  .packshot-wrapper {{
    flex-shrink: 0;
    width: 110px;
    text-align: center;
  }}
  .packshot-wrapper img {{
    max-width: 100px;
    max-height: 130px;
    object-fit: contain;
  }}
  .product-info {{
    flex: 1;
  }}
  .product-producer {{
    font-size: 10pt;
    color: #614dd4;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }}
  .product-name {{
    font-family: 'Anton', Impact, sans-serif;
    font-size: 18pt;
    color: #1f1240;
    line-height: 1.1;
    margin-bottom: 8px;
    string-set: product-name content();
  }}
  .product-type {{
    font-size: 10pt;
    color: #444;
    margin-bottom: 4px;
  }}
  .product-appellation {{
    font-size: 9pt;
    color: #888;
    font-style: italic;
  }}

  /* ── Titres de section ── */
  .section-title {{
    font-family: 'Anton', Impact, sans-serif;
    font-size: 14pt;
    color: #614dd4;
    border-bottom: 1px solid #e0dbf5;
    padding-bottom: 4px;
    margin-bottom: 12px;
    margin-top: 20px;
  }}

  /* ── Grid deux colonnes ── */
  .two-col {{
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
  }}
  .col {{
    flex: 1;
  }}

  /* ── Arômes ── */
  .arome-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }}
  .arome-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #614dd4;
    flex-shrink: 0;
  }}
  .arome-label {{
    font-weight: 600;
    font-size: 10pt;
    color: #1f1240;
  }}
  .arome-sub {{
    font-size: 9pt;
    color: #888;
    margin-left: 18px;
    margin-top: -4px;
    margin-bottom: 4px;
  }}

  /* ── Caractéristiques ── */
  .cara-item {{
    margin-bottom: 10px;
  }}
  .cara-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 3px;
  }}
  .cara-name {{
    font-weight: 700;
    font-size: 10pt;
    color: #1f1240;
  }}
  .cara-intensite {{
    font-size: 9pt;
    color: #614dd4;
    font-weight: 600;
  }}
  .cara-bar-bg {{
    height: 6px;
    background: #e8e5f5;
    border-radius: 3px;
    overflow: hidden;
  }}
  .cara-bar-fill {{
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, #614dd4, #8b7fe8);
  }}

  /* ── Balance qualitative ── */
  .balance-wrapper {{
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
  }}
  .balance-card {{
    flex: 1;
    text-align: center;
    padding: 12px;
    border-radius: 6px;
  }}
  .balance-card.pos {{
    background: #e8f5e9;
    border: 1px solid #a5d6a7;
  }}
  .balance-card.neg {{
    background: #fce4ec;
    border: 1px solid #f48fb1;
  }}
  .balance-count {{
    font-family: 'Anton', Impact, sans-serif;
    font-size: 28pt;
    line-height: 1;
    margin-bottom: 4px;
  }}
  .balance-card.pos .balance-count {{ color: #2e7d32; }}
  .balance-card.neg .balance-count {{ color: #c62828; }}
  .balance-label {{
    font-size: 9pt;
    color: #555;
  }}
  .balance-pct {{
    font-weight: 700;
    font-size: 11pt;
  }}
  .balance-card.pos .balance-pct {{ color: #2e7d32; }}
  .balance-card.neg .balance-pct {{ color: #c62828; }}

  /* ── Résumé qualitatif ── */
  .resume-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 10pt;
  }}
  .resume-table th {{
    background: #1f1240;
    color: white;
    padding: 7px 10px;
    text-align: left;
    font-weight: 700;
    font-size: 9pt;
  }}
  .resume-table td {{
    padding: 6px 10px;
    border-bottom: 1px solid #e8e5f5;
    vertical-align: middle;
  }}
  .resume-table tr:nth-child(even) td {{
    background: #f5f5f7;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 8pt;
    font-weight: 600;
  }}
  .badge-freq {{ background: #e3f2fd; color: #1565c0; }}
  .badge-mod  {{ background: #f3e5f5; color: #6a1b9a; }}
  .badge-pos  {{ background: #e8f5e9; color: #2e7d32; }}
  .badge-neg  {{ background: #fce4ec; color: #c62828; }}

  /* ── Scores ── */
  .scores-section {{
    background: #1f1240;
    color: white;
    border-radius: 8px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 0;
    margin-bottom: 20px;
  }}
  .score-block {{
    flex: 1;
    text-align: center;
    border-right: 1px solid #3d2f6e;
  }}
  .score-block:last-child {{ border-right: none; }}
  .score-value {{
    font-family: 'Anton', Impact, sans-serif;
    font-size: 28pt;
    line-height: 1;
    color: #fff;
  }}
  .score-moy {{ color: #a89eef; }}
  .score-label {{
    font-size: 8pt;
    color: #8b7fe8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
  }}
  .score-meta {{
    flex: 2;
    text-align: right;
    font-size: 9pt;
    color: #8b7fe8;
    padding-left: 16px;
  }}
  .score-meta div {{ margin-bottom: 4px; }}
  .score-meta strong {{ color: #a89eef; }}

  /* ── Footer note ── */
  .footer-note {{
    margin-top: 24px;
    border-top: 1px solid #e0dbf5;
    padding-top: 8px;
    font-size: 8pt;
    color: #bbb;
    text-align: center;
    font-style: italic;
  }}
</style>
</head>
<body>

<!-- ═══════════════════════════════════════════════════
     HEADER
════════════════════════════════════════════════════ -->
<div class="header">
  <div class="header-logo">TASTEE</div>
  <div class="header-meta">
    Rapport <strong>{report_name}</strong><br>
    Créé le {created_at}<br>
    Par Winespace
  </div>
</div>

<!-- ═══════════════════════════════════════════════════
     FICHE PRODUIT
════════════════════════════════════════════════════ -->
<div class="product-section">
  <div class="packshot-wrapper">
    {packshot_html}
  </div>
  <div class="product-info">
    <div class="product-producer">{producer}</div>
    <div class="product-name">{product_name}</div>
    <div class="product-type">{product_type}</div>
    <div class="product-appellation">{appellation}</div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════
     ARÔMES + CARACTÉRISTIQUES (2 colonnes)
════════════════════════════════════════════════════ -->
<div class="two-col">
  <div class="col">
    <div class="section-title">Arômes dominants</div>
    {aromes_html}
  </div>
  <div class="col">
    <div class="section-title">Caractéristiques principales</div>
    {caracteristiques_html}
  </div>
</div>

<!-- ═══════════════════════════════════════════════════
     BALANCE QUALITATIVE
════════════════════════════════════════════════════ -->
<div class="section-title">Balance qualitative</div>
<div class="balance-wrapper">
  <div class="balance-card pos">
    <div class="balance-count">{strongs_count}</div>
    <div class="balance-pct">{strongs_pct}</div>
    <div class="balance-label">Points forts cités</div>
  </div>
  <div class="balance-card neg">
    <div class="balance-count">{weaks_count}</div>
    <div class="balance-pct">{weaks_pct}</div>
    <div class="balance-label">Points faibles cités</div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════
     RÉSUMÉ QUALITATIF
════════════════════════════════════════════════════ -->
<div class="section-title">Résumé qualitatif</div>
<table class="resume-table">
  <thead>
    <tr>
      <th>Caractéristique</th>
      <th>Fréquence</th>
      <th>Qualité perçue</th>
    </tr>
  </thead>
  <tbody>
    {resume_rows}
  </tbody>
</table>

<!-- ═══════════════════════════════════════════════════
     ANALYSE DES SCORES
════════════════════════════════════════════════════ -->
<div class="section-title">Analyse des scores</div>
<div class="scores-section">
  <div class="score-block">
    <div class="score-value">{score_min}</div>
    <div class="score-label">Minimum</div>
  </div>
  <div class="score-block">
    <div class="score-value score-moy">{score_moy}</div>
    <div class="score-label">Moyenne</div>
  </div>
  <div class="score-block">
    <div class="score-value">{score_max}</div>
    <div class="score-label">Maximum</div>
  </div>
  <div class="score-meta">
    <div>Total commentaires : <strong>{total_comments}</strong></div>
    <div>Médiane : <strong>{mediane} / 100</strong></div>
    <div>Coups de cœur : <strong>{nb_coeurs}</strong></div>
  </div>
</div>

<div class="footer-note">
  Document généré automatiquement par Tastee PDF Generator · Données analysées par Winespace
</div>

</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers de rendu HTML
# ──────────────────────────────────────────────────────────────────────────────

INTENSITE_WIDTHS = {
    "très peu intense": "15%",
    "peu intense":       "35%",
    "modérement intense": "55%",
    "intensément":       "70%",
    "très intense":      "90%",
}


def _intensite_width(label: str) -> str:
    label_low = label.lower()
    for k, v in INTENSITE_WIDTHS.items():
        if k in label_low:
            return v
    return "50%"


def _badge_freq(freq: str) -> str:
    cls = "badge-freq" if "fréquemment" in freq.lower() else "badge-mod"
    return f'<span class="badge {cls}">{freq}</span>'


def _badge_qual(qual: str) -> str:
    if not qual:
        return ""
    cls = "badge-pos" if "qualitatif" in qual.lower() and "peu" not in qual.lower() else "badge-neg"
    return f'<span class="badge {cls}">{qual}</span>'


def _aromes_html(aromes: list) -> str:
    if not aromes:
        return "<p style='color:#888;font-size:9pt'>Aucun arôme renseigné</p>"
    html = ""
    i = 0
    while i < len(aromes):
        a = aromes[i]
        # Si l'élément suivant ressemble à un sous-type (ex : "Noix")
        sub = aromes[i + 1] if i + 1 < len(aromes) and len(aromes[i + 1]) < 30 else None
        html += f'<div class="arome-item"><div class="arome-dot"></div><span class="arome-label">{a}</span></div>'
        if sub and not any(kw in sub.lower() for kw in ["intense", "modér", "fréquemment", "plutôt"]):
            html += f'<div class="arome-sub">{sub}</div>'
            i += 2
        else:
            i += 1
    return html


def _caracteristiques_html(caras: list) -> str:
    if not caras:
        return "<p style='color:#888;font-size:9pt'>Aucune donnée</p>"
    html = ""
    for c in caras:
        width = _intensite_width(c.get("intensite", ""))
        html += f"""
        <div class="cara-item">
          <div class="cara-header">
            <span class="cara-name">{c['nom']}</span>
            <span class="cara-intensite">{c.get('intensite', '')}</span>
          </div>
          <div class="cara-bar-bg">
            <div class="cara-bar-fill" style="width:{width}"></div>
          </div>
        </div>"""
    return html


def _resume_rows(resume: list) -> str:
    if not resume:
        return "<tr><td colspan='3' style='color:#888;text-align:center'>Aucune donnée</td></tr>"
    rows = ""
    for r in resume:
        rows += f"""
        <tr>
          <td style="font-weight:600;color:#1f1240">{r['nom']}</td>
          <td>{_badge_freq(r.get('frequence',''))}</td>
          <td>{_badge_qual(r.get('qualite',''))}</td>
        </tr>"""
    return rows


def _packshot_html(packshot_b64: str) -> str:
    if not packshot_b64:
        return "<div style='width:100px;height:130px;background:#f0edf9;border-radius:4px'></div>"
    return f'<img src="{packshot_b64}" alt="Packshot">'


# ──────────────────────────────────────────────────────────────────────────────
#  Fonction principale
# ──────────────────────────────────────────────────────────────────────────────

def generate_pdf(data: dict) -> bytes:
    """
    Prend le dict retourné par scraper.scrape_tastee_report()
    et retourne un bytes PDF prêt à télécharger.
    """
    from weasyprint import HTML

    balance = data.get("balance", {})
    scores  = data.get("scores", {})

    html_content = HTML_TEMPLATE.format(
        report_name        = data.get("reportName", "—"),
        created_at         = data.get("createdAt", datetime.today().strftime("%d/%m/%Y")),
        producer           = data.get("producer", ""),
        product_name       = data.get("productName", ""),
        product_type       = data.get("type", ""),
        appellation        = data.get("appellation", ""),
        packshot_html      = _packshot_html(data.get("packshotB64", "")),
        aromes_html        = _aromes_html(data.get("aromes", [])),
        caracteristiques_html = _caracteristiques_html(data.get("caracteristiques", [])),
        strongs_count      = balance.get("strongsCount", "—"),
        strongs_pct        = balance.get("strongsPct", ""),
        weaks_count        = balance.get("weaksCount", "—"),
        weaks_pct          = balance.get("weaksPct", ""),
        resume_rows        = _resume_rows(data.get("resume", [])),
        score_min          = scores.get("min", "—"),
        score_moy          = scores.get("moyenne", "—"),
        score_max          = scores.get("max", "—"),
        total_comments     = data.get("totalComments", "—"),
        mediane            = data.get("mediane", "—"),
        nb_coeurs          = data.get("nbCoeurs", "0"),
    )

    pdf_bytes = HTML(string=html_content, base_url=None).write_pdf()
    return pdf_bytes
