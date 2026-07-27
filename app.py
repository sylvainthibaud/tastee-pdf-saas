"""
app.py — Serveur Flask du mini SaaS Tastee PDF Generator
Lancer localement : python app.py
Héberger en ligne  : Railway / Render (voir README)
"""

import io
import os

from flask import Flask, jsonify, render_template, request, send_file

from pdf_generator import generate_pdf
from scraper import scrape_tastee_report

app = Flask(__name__)


# ──────────────────────────────────────────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    POST JSON { "url": "https://tastee.wine/fr/reports/..." }
    → retourne le PDF en téléchargement
    """
    body = request.get_json(force=True, silent=True) or {}
    url  = (body.get("url") or "").strip()

    # Validation basique
    if not url:
        return jsonify({"error": "L'URL est vide."}), 400
    if "tastee.wine" not in url and "tastee.app" not in url:
        return jsonify({"error": "Ce lien ne semble pas être une URL Tastee valide."}), 400

    try:
        # 1. Scraping
        data = scrape_tastee_report(url)

        # 2. Génération PDF
        pdf_bytes = generate_pdf(data)

        # 3. Nom du fichier
        product = data.get("productName", "rapport").replace(" ", "_")[:40]
        filename = f"Tastee_{product}.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as exc:
        app.logger.exception("Erreur génération PDF")
        return jsonify({"error": f"Erreur : {str(exc)}"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ──────────────────────────────────────────────────────────────────────────────
#  Lancement
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
