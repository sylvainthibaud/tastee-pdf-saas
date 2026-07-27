"""
scraper.py — Extraction des données d'un rapport Tastee partagé
Utilise Playwright pour rendre la page JavaScript et extraire toutes les infos.
"""

from playwright.sync_api import sync_playwright


# Script JavaScript injecté dans la page pour extraire les données
EXTRACT_SCRIPT = """
() => {
    const lines = document.body.innerText.split('\\n').map(l => l.trim()).filter(Boolean);

    function sectionLines(startMarker, endMarkers) {
        const start = lines.indexOf(startMarker);
        if (start === -1) return [];
        const res = [];
        for (let i = start + 1; i < lines.length; i++) {
            if (endMarkers.includes(lines[i])) break;
            res.push(lines[i]);
        }
        return res;
    }

    // Infos produit (les 15 premières lignes contiennent tout)
    const header = lines.slice(0, 20);

    // Arômes dominants
    const aromes = sectionLines('Arômes dominants', ['Caractéristiques principales']);

    // Caractéristiques (paires nom / intensité)
    const caraRaw = sectionLines('Caractéristiques principales', ['Balance qualitative']);
    const caracteristiques = [];
    for (let i = 0; i < caraRaw.length - 1; i += 2) {
        caracteristiques.push({ nom: caraRaw[i], intensite: caraRaw[i + 1] || '' });
    }

    // Balance
    const balIdx = lines.indexOf('Balance qualitative');
    const strongsIdx = lines.indexOf('Nombre de points forts cités');
    const weaksIdx  = lines.indexOf('Nombre de points faibles cités');

    // Résumé qualitatif (triplets : caractéristique / fréquence / qualité)
    const resumeRaw = sectionLines('Résumé qualitatif', ['Voir plus', 'Profil aromatique']);
    const resume = [];
    for (let i = 0; i + 2 < resumeRaw.length; i += 3) {
        const q = resumeRaw[i + 2] || '';
        if (q.startsWith('Plutôt') || q.startsWith('Fréquemment') || q.startsWith('Modér')) {
            // skip odd format — reconstruct
        }
        resume.push({
            nom: resumeRaw[i],
            frequence: resumeRaw[i + 1] || '',
            qualite: resumeRaw[i + 2] || ''
        });
    }

    // Scores
    const scoreIdx = lines.indexOf('Analyse des scores');
    const scoreNums = scoreIdx > -1
        ? lines.slice(scoreIdx, scoreIdx + 20).filter(l => /^\\d+$/.test(l))
        : [];

    const totalCommIdx = lines.indexOf('Total commentaires');
    const medianeIdx   = lines.indexOf('Médiane');
    const coeursIdx    = lines.indexOf('Nombre de coups de cœur');

    // Packshot URL
    const packshotEl = document.querySelector('img[alt="cuvee bottle image"]');

    // Type et appellation
    const typeEl = Array.from(document.querySelectorAll('*')).find(e =>
        e.children.length === 0 &&
        /^(Rouge|Blanc|Rosé|Orange|Pétillant|Effervescent)/.test(e.textContent.trim())
    );
    const appellationEl = Array.from(document.querySelectorAll('*')).find(e =>
        e.children.length <= 2 &&
        /^(DO |AOC |IGP |AOP )/.test(e.textContent.trim())
    );

    // Report name (dans les guillemets)
    const reportNameEl = Array.from(document.querySelectorAll('em, [class*="name"]'))
        .find(e => e.textContent.includes('"') || e.textContent.includes('«'));

    // Date de création
    const dateEl = Array.from(document.querySelectorAll('*')).find(e =>
        e.children.length === 0 && /^\\d{2}\\/\\d{2}\\/\\d{4}$/.test(e.textContent.trim())
    );

    return {
        reportName:  reportNameEl?.textContent?.trim()     || '',
        createdAt:   dateEl?.textContent?.trim()           || '',
        producer:    header[5]  || '',
        productName: header[6]  || '',
        type:        typeEl?.textContent?.trim()            || header[7] || '',
        appellation: appellationEl?.textContent?.trim()    || header[8] || '',
        packshotUrl: packshotEl?.src                       || '',
        aromes,
        caracteristiques,
        resume,
        balance: {
            strongsCount: strongsIdx > -1 ? lines[strongsIdx + 1] : '',
            strongsPct:   strongsIdx > -1 ? lines[strongsIdx + 2] : '',
            weaksCount:   weaksIdx  > -1 ? lines[weaksIdx  + 1] : '',
            weaksPct:     weaksIdx  > -1 ? lines[weaksIdx  + 2] : '',
        },
        scores: {
            min:     scoreNums[0] || '',
            moyenne: scoreNums[1] || '',
            max:     scoreNums[2] || '',
        },
        totalComments:     totalCommIdx > -1 ? lines[totalCommIdx + 1] : '',
        mediane:           medianeIdx   > -1 ? lines[medianeIdx   + 1] : '',
        nbCoeurs:          coeursIdx    > -1 ? lines[coeursIdx    + 1] : '',
    };
}
"""


def scrape_tastee_report(url: str) -> dict:
    """
    Scrape un rapport Tastee partagé et retourne un dict structuré
    avec toutes les données + le packshot encodé en base64.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="fr-FR")
        page = context.new_page()

        # Charge la page et attend la fin du rendu JS
        page.goto(url, wait_until="networkidle", timeout=40_000)

        # Extrait les données textuelles
        data = page.evaluate(EXTRACT_SCRIPT)

        # Récupère le packshot en base64 (fetch depuis la page elle-même,
        # donc pas de problème de CORS)
        if data.get("packshotUrl"):
            try:
                packshot_b64 = page.evaluate(
                    """async (url) => {
                        const r = await fetch(url);
                        const blob = await r.blob();
                        return new Promise(resolve => {
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.readAsDataURL(blob);
                        });
                    }""",
                    data["packshotUrl"],
                )
                data["packshotB64"] = packshot_b64  # data:image/png;base64,...
            except Exception:
                data["packshotB64"] = None

        browser.close()
        return data
